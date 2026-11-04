import subprocess
import sys

from conftest import BACKEND_DIR

PRINT_URL = "import database; print(database.engine.url.render_as_string(hide_password=True))"


def import_database(tmp_path, **db_env):
    env = {
        "PATH": "/usr/bin:/bin",
        "HOME": str(tmp_path),
        "PYTHONDONTWRITEBYTECODE": "1",
        "NO_GCE_CHECK": "true",
        # Empty values stop a local .env from filling these in.
        "DB_HOST": "",
        "INSTANCE_UNIX_SOCKET": "",
        "GCS_BUCKET_NAME": "",
        "GCP_PROJECT_ID": "",
        "GCP_PRIVATE_KEY": "",
        "GCP_CLIENT_EMAIL": "",
        **db_env,
    }
    return subprocess.run(
        [sys.executable, "-c", PRINT_URL],
        cwd=BACKEND_DIR, env=env, capture_output=True, text=True, timeout=60,
    )


def test_missing_db_host_stops_startup_with_a_clear_error(tmp_path):
    result = import_database(tmp_path)
    assert result.returncode != 0
    assert "DB_HOST" in result.stderr
    assert "@" not in result.stdout


def test_db_host_is_used_for_tcp_connections(tmp_path):
    result = import_database(tmp_path, DB_HOST="db.example.test", DB_PORT="3307", DB_USER="u", DB_NAME="n")
    assert result.returncode == 0, result.stderr
    assert "u:***@db.example.test:3307/n" in result.stdout


def test_cloud_run_socket_still_works_without_db_host(tmp_path):
    result = import_database(tmp_path, INSTANCE_UNIX_SOCKET="/cloudsql/inst", DB_USER="u", DB_NAME="n")
    assert result.returncode == 0, result.stderr
    assert "u:***@/n?unix_socket=" in result.stdout
