import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from google.cloud import storage
from google.oauth2 import service_account
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

# ================== GCS SETUP ==================
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
gcp_project_id = os.getenv("GCP_PROJECT_ID")
gcp_private_key = os.getenv("GCP_PRIVATE_KEY")
gcp_client_email = os.getenv("GCP_CLIENT_EMAIL")

bucket = None
if gcp_project_id and gcp_private_key and gcp_client_email:
    creds_info = {
        "type": "service_account",
        "project_id": gcp_project_id,
        "private_key": gcp_private_key.replace('\\n', '\n'),
        "client_email": gcp_client_email,
        "token_uri": "https://oauth2.googleapis.com/token"
    }
    try:
        credentials = service_account.Credentials.from_service_account_info(creds_info)
        storage_client = storage.Client(credentials=credentials)
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
    except Exception as e:
        print(f"Warning: Failed to initialize GCS. Uploads won't work. Error: {e}")
else:
    # In Cloud Run, use Application Default Credentials (ADC)
    try:
        storage_client = storage.Client()
        if GCS_BUCKET_NAME:
            bucket = storage_client.bucket(GCS_BUCKET_NAME)
    except Exception as e:
        print(f"Warning: Failed to initialize GCS with ADC. Error: {e}")

class GCSDatabase:
    """Service to handle blob storage operations on Google Cloud Storage"""
    
    def __init__(self, bucket):
        self.bucket = bucket
    
    def upload_file(self, contents: bytes, destination_path: str, content_type: str = "application/octet-stream") -> str:
        """Uploads a file to GCS and returns its public URL"""
        if not self.bucket:
            raise Exception("GCS bucket is not initialized.")
        blob = self.bucket.blob(destination_path)
        blob.upload_from_string(contents, content_type=content_type)
        return blob.public_url

    def download_file_by_url(self, public_url: str) -> tuple[bytes, str]:
        if not self.bucket:
            raise Exception("GCS bucket is not initialized.")
        prefix = f"https://storage.googleapis.com/{self.bucket.name}/"
        if public_url.startswith(prefix):
            destination_path = public_url[len(prefix):]
        else:
            destination_path = public_url
            
        blob = self.bucket.blob(destination_path)
        contents = blob.download_as_bytes()
        return contents, blob.content_type

gcs_db = GCSDatabase(bucket)

# ================== CLOUD SQL SETUP ==================
DB_USER = os.getenv("DB_USER", "FastAPI")
DB_PASS = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "tutor-learning-db")
DB_HOST = os.getenv("DB_HOST", "34.154.122.155")
DB_PORT = os.getenv("DB_PORT", "3306")

# Cloud Run connects via Unix socket through the Auth Proxy sidecar
INSTANCE_UNIX_SOCKET = os.getenv("INSTANCE_UNIX_SOCKET")

if INSTANCE_UNIX_SOCKET:
    # Cloud Run: use Unix socket (Auth Proxy sidecar)
    SQLALCHEMY_DATABASE_URL = (
        f"mysql+pymysql://{quote_plus(DB_USER)}:{quote_plus(DB_PASS)}"
        f"@/{DB_NAME}?unix_socket={INSTANCE_UNIX_SOCKET}"
    )
else:
    # Local dev: direct TCP connection to public IP
    SQLALCHEMY_DATABASE_URL = (
        f"mysql+pymysql://{quote_plus(DB_USER)}:{quote_plus(DB_PASS)}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_recycle=1800,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=2,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()