from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse, RedirectResponse
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import uuid
from datetime import datetime
import json
import os
import tempfile

import schemas
import models
from database import get_db, gcs_db, engine
from gmail_service import gmail_service

app = FastAPI(title="Tutor-Learning-API", version="1.0")

# CORS middleware — allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    """Create tables on startup (idempotent)"""
    models.Base.metadata.create_all(bind=engine)

# Configuration for encrypting passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

# ================== USERS ==================

@app.get("/")
def read_root():
    return {"message": "Welcome to the Tutor-Learning Platform Backend!"}

@app.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Creates a new user"""
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email is already registered")
    
    db_user = models.User(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        password_hash=get_password_hash(user.password),
        is_teacher=user.is_teacher
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/login/", response_model=schemas.LoginResponse)
def login(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    """User login"""
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    return schemas.LoginResponse(
        message="Login successful",
        user=user
    )

@app.get("/users/", response_model=list[schemas.UserResponse])
def list_users(db: Session = Depends(get_db)):
    """Lists all users"""
    return db.query(models.User).all()

@app.get("/users/{email}", response_model=schemas.UserResponse)
def get_user(email: str, db: Session = Depends(get_db)):
    """Gets a user by email"""
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/users/{email}", response_model=schemas.UserResponse)
def update_user(email: str, user_update: schemas.UserUpdate, db: Session = Depends(get_db)):
    """Updates a user's profile"""
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_update.first_name is not None:
        user.first_name = user_update.first_name
    if user_update.last_name is not None:
        user.last_name = user_update.last_name
    if user_update.is_teacher is not None:
        user.is_teacher = user_update.is_teacher
    
    db.commit()
    db.refresh(user)
    return user

# ================== COURSES ==================

@app.post("/courses/", response_model=schemas.CourseResponse)
def create_course(course: schemas.CourseCreate, db: Session = Depends(get_db)):
    """Creates a new course"""
    db_course = models.Course(
        title=course.title,
        description=course.description,
        is_visible=course.is_visible,
        is_enrollable=course.is_enrollable,
        teacher_id=course.teacher_id
    )
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

@app.get("/courses/", response_model=list[schemas.CourseResponse])
def list_all_courses(db: Session = Depends(get_db)):
    """Lists all courses"""
    return db.query(models.Course).all()

@app.get("/courses/{course_id}", response_model=schemas.CourseResponse)
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
         raise HTTPException(status_code=404, detail="Course not found")
    return course

@app.put("/courses/{course_id}", response_model=schemas.CourseResponse)
def update_course(course_id: int, course_update: schemas.CourseUpdate, db: Session = Depends(get_db)):
    """Updates a course"""
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if course_update.title is not None:
        course.title = course_update.title
    if course_update.description is not None:
        course.description = course_update.description
    if course_update.is_visible is not None:
        course.is_visible = course_update.is_visible
    if course_update.is_enrollable is not None:
        course.is_enrollable = course_update.is_enrollable
    
    db.commit()
    db.refresh(course)
    return course

# ================== ASSIGNMENTS (TASKS) ==================

@app.post("/assignments/", response_model=schemas.AssignmentResponse)
def create_assignment(assignment: schemas.AssignmentCreate, db: Session = Depends(get_db)):
    """Creates a new assignment (task) in a course"""
    course = db.query(models.Course).filter(models.Course.id == assignment.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    db_assignment = models.Assignment(
        course_id=assignment.course_id,
        title=assignment.title,
        description=assignment.description,
        due_date=assignment.due_date
    )
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    return db_assignment

@app.get("/assignments/course/{course_id}", response_model=list[schemas.AssignmentResponse])
def list_assignments(course_id: int, db: Session = Depends(get_db)):
    """Lists all assignments for a course"""
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    return db.query(models.Assignment).filter(models.Assignment.course_id == course_id).all()

@app.put("/assignments/{assignment_id}", response_model=schemas.AssignmentResponse)
def update_assignment(assignment_id: int, assignment_update: schemas.AssignmentUpdate, db: Session = Depends(get_db)):
    """Updates an assignment"""
    assignment = db.query(models.Assignment).filter(models.Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    if assignment_update.title is not None:
        assignment.title = assignment_update.title
    if assignment_update.description is not None:
        assignment.description = assignment_update.description
    if assignment_update.due_date is not None:
        assignment.due_date = assignment_update.due_date
    
    db.commit()
    db.refresh(assignment)
    return assignment

# ================== ASSIGNMENT SUBMISSIONS ==================
@app.post("/submissions/", response_model=schemas.AssignmentSubmissionResponse)
def submit_assignment(submission: schemas.AssignmentSubmissionCreate, db: Session = Depends(get_db)):
    assignment = db.query(models.Assignment).filter(models.Assignment.id == submission.assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
        
    user = db.query(models.User).filter(models.User.id == submission.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    existing = db.query(models.AssignmentSubmission).filter(
        models.AssignmentSubmission.assignment_id == submission.assignment_id,
        models.AssignmentSubmission.user_id == submission.user_id
    ).first()
    if existing:
         raise HTTPException(status_code=400, detail="Already submitted")
         
    db_sub = models.AssignmentSubmission(
        user_id=submission.user_id,
        assignment_id=submission.assignment_id,
        grade=submission.grade,
        submission_file_url=submission.submission_file_url
    )
    db.add(db_sub)
    db.commit()
    db.refresh(db_sub)
    return db_sub

# ================== POSTS (TEXT BLOCKS) ==================

@app.post("/textblocks/", response_model=schemas.TextBlockResponse)
def create_textblock(textblock: schemas.TextBlockCreate, db: Session = Depends(get_db)):
    """Creates a new text block (post) in a course"""
    course = db.query(models.Course).filter(models.Course.id == textblock.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    db_textblock = models.TextBlock(
        course_id=textblock.course_id,
        title=textblock.title,
        content=textblock.content
    )
    db.add(db_textblock)
    db.commit()
    db.refresh(db_textblock)
    return db_textblock

@app.get("/textblocks/course/{course_id}", response_model=list[schemas.TextBlockResponse])
def list_textblocks(course_id: int, db: Session = Depends(get_db)):
    """Lists all text blocks for a course"""
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    return db.query(models.TextBlock).filter(models.TextBlock.course_id == course_id).all()

# ================== ENROLLMENTS ==================

@app.post("/enrollments/", response_model=schemas.EnrollmentResponse)
def create_enrollment(enrollment: schemas.EnrollmentCreate, db: Session = Depends(get_db)):
    """Enrolls a user in a course and sends a welcome email"""
    user = db.query(models.User).filter(models.User.id == enrollment.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    course = db.query(models.Course).filter(models.Course.id == enrollment.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if course.teacher_id == enrollment.user_id:
        raise HTTPException(status_code=400, detail="You cannot enroll in your own course")

    existing = db.query(models.Enrollment).filter(
        models.Enrollment.user_id == enrollment.user_id,
        models.Enrollment.course_id == enrollment.course_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You are already enrolled in this course")
    
    db_enrollment = models.Enrollment(
        user_id=enrollment.user_id,
        course_id=enrollment.course_id
    )
    db.add(db_enrollment)
    db.commit()
    db.refresh(db_enrollment)
    
    # Send welcome email
    gmail_service.send_welcome_email(
        user.email,
        user.first_name,
        course.title
    )
    
    return db_enrollment

@app.get("/enrollments/user/{user_id}", response_model=list[schemas.EnrollmentListResponse])
def list_user_enrollments(user_id: int, db: Session = Depends(get_db)):
    """Lists all courses a user is enrolled in"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    return db.query(models.Enrollment).filter(models.Enrollment.user_id == user_id).all()

@app.get("/enrollments/course/{course_id}", response_model=list[schemas.EnrollmentListResponse])
def list_course_enrollments(course_id: int, db: Session = Depends(get_db)):
    """Lists all students enrolled in a course"""
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    return db.query(models.Enrollment).filter(models.Enrollment.course_id == course_id).all()


# ================== FILES (GCS HYBRID) ==================

@app.post("/files/course/{course_id}", response_model=schemas.FileResponse)
def upload_course_file(course_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Uploads a file to GCS and stores the reference in the Files table for a course"""
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    try:
        contents = file.file.read()
        file_extension = file.filename.split('.')[-1]
        unique_name = f"{uuid.uuid4()}.{file_extension}"
        destination_path = f"files/courses/{course_id}/{unique_name}"
        
        # Upload to GCS
        public_url = gcs_db.upload_file(contents, destination_path, file.content_type)
        
        # Save to Cloud SQL
        db_file = models.File(
            course_id=course_id,
            file_name=file.filename,
            mime_type=file.content_type,
            gcs_url=public_url
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        
        return db_file
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@app.get("/files/course/{course_id}", response_model=list[schemas.FileResponse])
def list_course_files(course_id: int, db: Session = Depends(get_db)):
    """Lists all files for a course"""
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    return db.query(models.File).filter(models.File.course_id == course_id).all()

@app.get("/files/{file_id}")
def download_file(file_id: int, db: Session = Depends(get_db)):
    """Redirects to the public GCS URL of a file"""
    file_record = db.query(models.File).filter(models.File.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    return RedirectResponse(url=file_record.gcs_url)