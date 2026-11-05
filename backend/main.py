from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse, RedirectResponse, Response
from sqlalchemy import or_
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import uuid
from datetime import datetime
import json
import os
import tempfile
import mimetypes
from urllib.parse import urlsplit, unquote

import auth
import schemas
import models
from database import get_db, gcs_db, engine, SessionLocal
from gmail_service import gmail_service
import threading
import time

def process_email_queue():
    """Background job that uses a database cursor to process pending emails (Cloud Run adapted)"""
    try:
        db = SessionLocal()
        try:
            # Process Registration Emails
            pending_register = db.query(models.RegisterEmailQueue).filter(
                models.RegisterEmailQueue.status == models.EmailStatus.PENDING
            ).all()
            
            for email in pending_register:
                print(f"Processing register email for {email.recipient_email}...")
                try:
                    success, error_msg = gmail_service.send_email(
                        to_email=email.recipient_email,
                        subject=email.subject,
                        body=email.body,
                        is_html=True
                    )
                    if success:
                        email.status = models.EmailStatus.SENT
                        print(f"Success sending register email to {email.recipient_email}")
                    else:
                        email.status = models.EmailStatus.FAILED
                        email.body = email.body + f"\n\n--- ERROR LOG ---\n{error_msg}"
                        print(f"Failed sending register email to {email.recipient_email} (service returned False)")
                except Exception as e:
                    print(f"Exception sending register email to {email.recipient_email}: {e}")
                    email.status = models.EmailStatus.FAILED
                    email.body = email.body + f"\n\n--- ERROR LOG ---\n{str(e)}"
                db.commit()

            # Process Enrollment Emails
            pending_enrollments = db.query(models.EnrollmentsEmailQueue).filter(
                models.EnrollmentsEmailQueue.status == models.EmailStatus.PENDING
            ).all()
            
            for email in pending_enrollments:
                print(f"Processing enrollment email for {email.recipient_email}...")
                try:
                    success, error_msg = gmail_service.send_email(
                        to_email=email.recipient_email,
                        subject=email.subject,
                        body=email.body,
                        is_html=True
                    )
                    if success:
                        email.status = models.EmailStatus.SENT
                        print(f"Success sending enrollment email to {email.recipient_email}")
                    else:
                        email.status = models.EmailStatus.FAILED
                        email.body = email.body + f"\n\n--- ERROR LOG ---\n{error_msg}"
                        print(f"Failed sending enrollment email to {email.recipient_email} (service returned False)")
                except Exception as e:
                    print(f"Exception sending enrollment email to {email.recipient_email}: {e}")
                    email.status = models.EmailStatus.FAILED
                    email.body = email.body + f"\n\n--- ERROR LOG ---\n{str(e)}"
                db.commit()
        finally:
            db.close()
    except Exception as e:
        print(f"Error in background email job: {e}")

app = FastAPI(title="Tutor-Learning-API", version="1.0")

# CORS middleware — only the origins in CORS_ALLOWED_ORIGINS, as requests carry the session cookie
app.add_middleware(
    CORSMiddleware,
    allow_origins=auth.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", auth.CSRF_HEADER],
)

@app.on_event("startup")
def on_startup():
    """Create tables on startup (idempotent) and handle migrations"""
    models.Base.metadata.create_all(bind=engine)
    
    # Manual migration for existing databases missing 'created_at' columns
    from sqlalchemy import text
    with engine.connect() as conn:
        print("Running schema migrations...")
        try:
            conn.execute(text("ALTER TABLE Assignments ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
            conn.commit()
            print("Migration: Added created_at to Assignments")
        except Exception: pass
        
        try:
            conn.execute(text("ALTER TABLE Users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0"))
            conn.commit()
            print("Migration: Added is_admin to Users")
        except Exception: pass
        
        # Database Triggers for Email Queue
        try:
            print("Creating email triggers...")
            conn.execute(text("DROP TRIGGER IF EXISTS after_user_insert"))
            conn.execute(text("""
                CREATE TRIGGER after_user_insert
                AFTER INSERT ON Users
                FOR EACH ROW
                BEGIN
                    INSERT INTO RegisterEmailQueue (recipient_email, subject, body, status, created_at)
                    VALUES (
                        NEW.email,
                        'Welcome to Tutor-Learning!',
                        CONCAT('<html><body style="font-family: Arial, sans-serif; color: #333;"><div style="max-width: 600px; margin: 0 auto; padding: 20px;"><h1 style="color: #4CAF50;">Welcome, ', NEW.first_name, '!</h1><p>You have successfully registered on the <strong>Tutor-Learning</strong> platform.</p><p>You can now start exploring available courses and enroll in the ones that interest you the most.</p><p>If you have any questions, do not hesitate to contact us.</p><br><p style="color: #666; font-size: 12px;">This is an automated email from the Tutor-Learning platform.</p></div></body></html>'),
                        'PENDING',
                        CURRENT_TIMESTAMP
                    );
                END
            """))
            print("Migration: Added after_user_insert trigger")
            
            conn.execute(text("DROP TRIGGER IF EXISTS after_enrollment_insert"))
            conn.execute(text("""
                CREATE TRIGGER after_enrollment_insert
                AFTER INSERT ON Enrollments
                FOR EACH ROW
                BEGIN
                    DECLARE v_user_name VARCHAR(100);
                    DECLARE v_user_email VARCHAR(150);
                    DECLARE v_course_title VARCHAR(200);

                    SELECT first_name, email INTO v_user_name, v_user_email FROM Users WHERE id = NEW.user_id;
                    SELECT title INTO v_course_title FROM Courses WHERE id = NEW.course_id;

                    INSERT INTO EnrollmentsEmailQueue (recipient_email, subject, body, status, created_at)
                    VALUES (
                        v_user_email,
                        CONCAT('You have enrolled in: ', v_course_title),
                        CONCAT('<html><body style="font-family: Arial, sans-serif; color: #333;"><div style="max-width: 600px; margin: 0 auto; padding: 20px;"><h1 style="color: #4CAF50;">Welcome, ', v_user_name, '!</h1><p>You have successfully enrolled in the course:</p><h2 style="color: #2196F3;">', v_course_title, '</h2><p>We hope you enjoy the content and have a great learning experience.</p><p>If you have any questions, your teacher is available to help.</p><br><p style="color: #666; font-size: 12px;">This is an automated email from the Tutor-Learning platform.</p></div></body></html>'),
                        'PENDING',
                        CURRENT_TIMESTAMP
                    );
                END
            """))
            print("Migration: Added after_enrollment_insert trigger")
            conn.commit()
        except Exception as e:
            print(f"Migration error creating triggers: {e}")
            conn.rollback()

# Configuration for encrypting passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

# ================== ACCESS CHECKS ==================

def require_teacher(user: models.User = Depends(auth.get_current_user)) -> models.User:
    if not user.is_teacher:
        raise HTTPException(status_code=403, detail="Only teachers can do this")
    return user

def require_admin(user: models.User = Depends(auth.get_current_user)) -> models.User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can do this")
    return user

def get_course_or_404(db: Session, course_id: int) -> models.Course:
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

def is_enrolled(db: Session, user: models.User, course_id: int) -> bool:
    return db.query(models.Enrollment).filter(
        models.Enrollment.user_id == user.id,
        models.Enrollment.course_id == course_id
    ).first() is not None

def is_course_member(db: Session, user: models.User, course: models.Course) -> bool:
    return course.teacher_id == user.id or is_enrolled(db, user, course.id)

def require_course_owner(db: Session, user: models.User, course_id: int) -> models.Course:
    course = get_course_or_404(db, course_id)
    if course.teacher_id != user.id:
        raise HTTPException(status_code=403, detail="Only this course's teacher can do this")
    return course

def require_course_member(db: Session, user: models.User, course_id: int) -> models.Course:
    course = get_course_or_404(db, course_id)
    if not is_course_member(db, user, course):
        raise HTTPException(status_code=403, detail="You are not a member of this course")
    return course

# ================== USERS ==================

@app.get("/")
def read_root():
    return {"message": "Welcome to the Tutor-Learning Platform Backend!"}

@app.post("/users/", response_model=schemas.UserResponse, dependencies=[Depends(auth.require_trusted_origin)])
def create_user(user: schemas.UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Creates a new user"""
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email is already registered")
    
    db_user = models.User(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        password_hash=get_password_hash(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Trigger background queue processor
    background_tasks.add_task(process_email_queue)

    return db_user

@app.post("/login/", response_model=schemas.LoginResponse, dependencies=[Depends(auth.require_trusted_origin)])
def login(credentials: schemas.UserLogin, request: Request, response: Response, db: Session = Depends(get_db)):
    """User login: starts a session in an HttpOnly cookie"""
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    previous_token = request.cookies.get(auth.SESSION_COOKIE_NAME)
    if previous_token:
        auth.delete_session(db, previous_token)
    auth.delete_expired_sessions(db)
    token, csrf_token = auth.create_session(db, user)
    auth.set_session_cookie(response, token)
    
    return schemas.LoginResponse(
        message="Login successful",
        user=user,
        csrf_token=csrf_token
    )

@app.post("/logout/")
def logout(response: Response, session: models.UserSession = Depends(auth.get_current_session), db: Session = Depends(get_db)):
    """Ends the caller's session"""
    db.delete(session)
    db.commit()
    auth.clear_session_cookie(response)
    return {"message": "Logged out"}

@app.get("/session/", response_model=schemas.SessionResponse)
def get_session(session: models.UserSession = Depends(auth.get_current_session)):
    """The logged-in user and CSRF token, so the frontend can resume after a page reload"""
    return schemas.SessionResponse(user=session.user, csrf_token=session.csrf_token)

@app.get("/users/", response_model=list[schemas.UserResponse], dependencies=[Depends(require_admin)])
def list_users(db: Session = Depends(get_db)):
    """Lists all users"""
    return db.query(models.User).all()

@app.get("/users/{email}", response_model=schemas.UserResponse)
def get_user(email: str, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """Gets your own user, or any user if you are an admin"""
    if email != current_user.email and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="You can only view your own profile")
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/users/{email}", response_model=schemas.UserResponse)
def update_user(email: str, user_update: schemas.UserUpdate, user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """Updates your own profile"""
    if email != user.email:
        raise HTTPException(status_code=403, detail="You can only edit your own profile")
    
    if user_update.first_name is not None:
        user.first_name = user_update.first_name
    if user_update.last_name is not None:
        user.last_name = user_update.last_name
    
    db.commit()
    db.refresh(user)
    return user

@app.put("/users/{email}/teacher", response_model=schemas.UserResponse, dependencies=[Depends(require_admin)])
def set_user_teacher(email: str, role: schemas.UserTeacherUpdate, db: Session = Depends(get_db)):
    """Grants or revokes the teacher role (admins only)"""
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_teacher = role.is_teacher
    db.commit()
    db.refresh(user)
    return user

# ================== COURSES ==================

@app.post("/courses/", response_model=schemas.CourseResponse)
def create_course(course: schemas.CourseCreate, teacher: models.User = Depends(require_teacher), db: Session = Depends(get_db)):
    """Creates a new course owned by the caller"""
    db_course = models.Course(
        title=course.title,
        description=course.description,
        is_visible=course.is_visible,
        is_enrollable=course.is_enrollable,
        teacher_id=teacher.id
    )
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

@app.get("/courses/", response_model=list[schemas.CourseResponse])
def list_all_courses(user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """Lists the courses the caller can see: visible ones, their own, and those they are enrolled in"""
    enrolled_course_ids = db.query(models.Enrollment.course_id).filter(models.Enrollment.user_id == user.id)
    return db.query(models.Course).filter(or_(
        models.Course.is_visible == True,
        models.Course.teacher_id == user.id,
        models.Course.id.in_(enrolled_course_ids)
    )).all()

@app.get("/courses/teaching", response_model=list[schemas.CourseResponse])
def list_teaching_courses(user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """Lists all courses created by the caller"""
    return db.query(models.Course).filter(models.Course.teacher_id == user.id).all()

@app.get("/courses/available", response_model=list[schemas.CourseResponse])
def list_available_courses(user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """Returns courses the caller can enroll in: visible, enrollable, not owned by them, and not already enrolled"""
    # Get courses the user is already enrolled in
    enrolled_course_ids = [
        e.course_id for e in db.query(models.Enrollment.course_id)
            .filter(models.Enrollment.user_id == user.id).all()
    ]
    
    return db.query(models.Course).filter(
        models.Course.is_visible == True,
        models.Course.is_enrollable == True,
        models.Course.teacher_id != user.id,
        ~models.Course.id.in_(enrolled_course_ids)
    ).all()

@app.delete("/courses/{course_id}")
def delete_course(course_id: int, user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    db_course = require_course_owner(db, user, course_id)
    
    # Delete related entities first (manual cascade to be safe)
    db.query(models.Enrollment).filter(models.Enrollment.course_id == course_id).delete()
    course_assignment_ids = db.query(models.Assignment.id).filter(models.Assignment.course_id == course_id)
    db.query(models.AssignmentSubmission).filter(
        models.AssignmentSubmission.assignment_id.in_(course_assignment_ids)
    ).delete(synchronize_session=False)
    db.query(models.Assignment).filter(models.Assignment.course_id == course_id).delete()
    db.query(models.TextBlock).filter(models.TextBlock.course_id == course_id).delete()
    db.query(models.File).filter(models.File.course_id == course_id).delete()
    
    db.delete(db_course)
    db.commit()
    return {"message": "Course and all related data deleted"}

@app.patch("/courses/{course_id}/image")
async def update_course_image(course_id: int, file: UploadFile = File(...), user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    course = require_course_owner(db, user, course_id)
    
    # Read file contents
    contents = await file.read()
    
    content_type = file.content_type
    if not content_type or content_type == 'application/octet-stream':
        guessed_type, _ = mimetypes.guess_type(file.filename)
        if guessed_type:
            content_type = guessed_type
        elif file.filename.lower().endswith('.webp'):
            content_type = 'image/webp'
            
    # Upload to GCS
    destination_path = f"courses/{course_id}/cover_{uuid.uuid4()}_{file.filename}"
    public_url = gcs_db.upload_file(contents, destination_path, content_type)
    
    course.image_url = public_url
    db.commit()
    db.refresh(course)
    return {"image_url": public_url}

@app.get("/files/{file_id}")
def get_file_redirect(file_id: int, user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """Redirects to a signed GCS URL to handle previewing files securely with range request support"""
    db_file = db.query(models.File).filter(models.File.id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    require_course_member(db, user, db_file.course_id)
    
    try:
        signed_url = gcs_db.get_signed_url(db_file.gcs_url)
        return RedirectResponse(url=signed_url)
    except Exception:
        try:
            contents, content_type = gcs_db.download_file_by_url(db_file.gcs_url)
            return Response(content=contents, media_type=content_type)
        except Exception:
            return RedirectResponse(url=db_file.gcs_url)

def is_own_bucket_url(url: str, folder: str) -> bool:
    """True only for an https URL inside the given folder of this app's own bucket"""
    if not gcs_db.bucket or any(ord(char) <= 32 or char == "\\" for char in url):
        return False
    parts = urlsplit(url)
    return (
        parts.scheme == "https"
        and parts.netloc == "storage.googleapis.com"
        and parts.path.startswith(f"/{gcs_db.bucket.name}/{folder}/")
        and not parts.query
        and not parts.fragment
        and ".." not in unquote(parts.path).split("/")
    )

@app.get("/proxy-image", dependencies=[Depends(auth.get_current_user)])
def proxy_image(url: str):
    """Redirects to a signed GCS URL for a course image in this app's bucket"""
    if not is_own_bucket_url(url, "courses"):
        raise HTTPException(status_code=400, detail="URL is not a course image in this app's storage")
    try:
        signed_url = gcs_db.get_signed_url(url)
        return RedirectResponse(url=signed_url)
    except Exception:
        try:
            contents, content_type = gcs_db.download_file_by_url(url)
            return Response(content=contents, media_type=content_type)
        except Exception:
            return RedirectResponse(url=url)

# (Redundant get_teacher_courses removed, use list_teacher_courses above)

@app.get("/courses/{course_id}", response_model=schemas.CourseResponse)
def get_course(course_id: int, user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    course = get_course_or_404(db, course_id)
    if not course.is_visible and not is_course_member(db, user, course):
        raise HTTPException(status_code=403, detail="You are not a member of this course")
    return course

@app.put("/courses/{course_id}", response_model=schemas.CourseResponse)
def update_course(course_id: int, course_update: schemas.CourseUpdate, user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """Updates a course"""
    course = require_course_owner(db, user, course_id)
    
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
def create_assignment(assignment: schemas.AssignmentCreate, user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """Creates a new assignment (task) in a course"""
    require_course_owner(db, user, assignment.course_id)
    
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
def list_assignments(course_id: int, user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """Lists all assignments for a course"""
    require_course_member(db, user, course_id)
    
    return db.query(models.Assignment).filter(models.Assignment.course_id == course_id).all()

@app.put("/assignments/{assignment_id}", response_model=schemas.AssignmentResponse)
def update_assignment(assignment_id: int, assignment_update: schemas.AssignmentUpdate, user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """Updates an assignment"""
    assignment = db.query(models.Assignment).filter(models.Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    require_course_owner(db, user, assignment.course_id)
    
    if assignment_update.title is not None:
        assignment.title = assignment_update.title
    if assignment_update.description is not None:
        assignment.description = assignment_update.description
    if assignment_update.due_date is not None:
        assignment.due_date = assignment_update.due_date
    
    db.commit()
    db.refresh(assignment)
    return assignment

@app.delete("/assignments/{assignment_id}")
def delete_assignment(assignment_id: int, user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """Deletes an assignment (task)"""
    assignment = db.query(models.Assignment).filter(models.Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    require_course_owner(db, user, assignment.course_id)
    
    # Delete related submissions first
    db.query(models.AssignmentSubmission).filter(
        models.AssignmentSubmission.assignment_id == assignment_id
    ).delete()
    
    db.delete(assignment)
    db.commit()
    return {"detail": "Task deleted successfully"}

# ================== ASSIGNMENT SUBMISSIONS ==================
@app.post("/submissions/", response_model=schemas.AssignmentSubmissionResponse)
def submit_assignment(submission: schemas.AssignmentSubmissionCreate, user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """Submits the caller's work for an assignment in a course they are enrolled in"""
    assignment = db.query(models.Assignment).filter(models.Assignment.id == submission.assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    if not is_enrolled(db, user, assignment.course_id):
        raise HTTPException(status_code=403, detail="You are not enrolled in this course")
    if submission.submission_file_url is not None and not is_own_bucket_url(submission.submission_file_url, "files/uploads"):
        raise HTTPException(status_code=400, detail="Submission file must be an upload in this app's storage")

    existing = db.query(models.AssignmentSubmission).filter(
        models.AssignmentSubmission.assignment_id == submission.assignment_id,
        models.AssignmentSubmission.user_id == user.id
    ).first()
    if existing:
         raise HTTPException(status_code=400, detail="Already submitted")
         
    db_sub = models.AssignmentSubmission(
        user_id=user.id,
        assignment_id=submission.assignment_id,
        submission_file_url=submission.submission_file_url
    )
    db.add(db_sub)
    db.commit()
    db.refresh(db_sub)
    return db_sub

@app.get("/submissions/course/{course_id}/me", response_model=list[schemas.AssignmentSubmissionResponse])
def list_my_submissions_in_course(course_id: int, user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """Lists the caller's own submissions in a course"""
    require_course_member(db, user, course_id)
    assignment_ids = [a.id for a in db.query(models.Assignment.id).filter(models.Assignment.course_id == course_id).all()]
    return db.query(models.AssignmentSubmission).filter(
        models.AssignmentSubmission.user_id == user.id,
        models.AssignmentSubmission.assignment_id.in_(assignment_ids)
    ).all()

@app.delete("/submissions/assignment/{assignment_id}/me")
def delete_my_submission(assignment_id: int, user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """Deletes the caller's own submission for an assignment"""
    db_sub = db.query(models.AssignmentSubmission).filter(
        models.AssignmentSubmission.assignment_id == assignment_id,
        models.AssignmentSubmission.user_id == user.id
    ).first()
    if not db_sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    db.delete(db_sub)
    db.commit()
    return {"message": "Submission deleted successfully"}

# ================== POSTS (TEXT BLOCKS) ==================

@app.post("/textblocks/", response_model=schemas.TextBlockResponse)
def create_textblock(textblock: schemas.TextBlockCreate, user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """Creates a new text block (post) in a course"""
    require_course_owner(db, user, textblock.course_id)
    
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
def list_textblocks(course_id: int, user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """Lists all text blocks for a course"""
    require_course_member(db, user, course_id)
    
    return db.query(models.TextBlock).filter(models.TextBlock.course_id == course_id).all()

@app.delete("/textblocks/{textblock_id}")
def delete_textblock(textblock_id: int, user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """Deletes a text block (post)"""
    db_textblock = db.query(models.TextBlock).filter(models.TextBlock.id == textblock_id).first()
    if not db_textblock:
        raise HTTPException(status_code=404, detail="Post not found")
    require_course_owner(db, user, db_textblock.course_id)
    
    db.delete(db_textblock)
    db.commit()
    return {"detail": "Post deleted successfully"}

# ================== ENROLLMENTS ==================

@app.post("/enrollments/", response_model=schemas.EnrollmentResponse)
def create_enrollment(enrollment: schemas.EnrollmentCreate, background_tasks: BackgroundTasks, user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """Enrolls the caller in a course and sends a welcome email"""
    course = get_course_or_404(db, enrollment.course_id)
    
    if course.teacher_id == user.id:
        raise HTTPException(status_code=400, detail="You cannot enroll in your own course")

    if is_enrolled(db, user, enrollment.course_id):
        raise HTTPException(status_code=400, detail="You are already enrolled in this course")
    
    if not course.is_visible or not course.is_enrollable:
        raise HTTPException(status_code=403, detail="This course is not open for enrollment")
    
    db_enrollment = models.Enrollment(
        user_id=user.id,
        course_id=enrollment.course_id
    )
    db.add(db_enrollment)
    db.commit()
    db.refresh(db_enrollment)
    
    # Trigger background queue processor
    background_tasks.add_task(process_email_queue)

    return db_enrollment

@app.get("/enrollments/me", response_model=list[schemas.EnrollmentListResponse])
def list_my_enrollments(user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """Lists all courses the caller is enrolled in"""
    return db.query(models.Enrollment).filter(models.Enrollment.user_id == user.id).all()

@app.get("/enrollments/course/{course_id}", response_model=list[schemas.EnrollmentRosterResponse])
def list_course_enrollments(course_id: int, user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """Lists all students enrolled in a course. Only the course's teacher sees their emails"""
    course = require_course_member(db, user, course_id)
    show_emails = course.teacher_id == user.id
    
    return [
        schemas.EnrollmentRosterResponse(
            user_id=enrollment.user_id,
            course_id=enrollment.course_id,
            enrollment_date=enrollment.enrollment_date,
            user=schemas.RosterUser(
                id=enrollment.user.id,
                first_name=enrollment.user.first_name,
                last_name=enrollment.user.last_name,
                email=enrollment.user.email if show_emails else None
            )
        )
        for enrollment in db.query(models.Enrollment).filter(models.Enrollment.course_id == course_id).all()
    ]

@app.delete("/enrollments/")
def unenroll_user(enrollment: schemas.EnrollmentCreate, user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """Unenrolls the caller from a course"""
    print(f"DEBUG: Unenrolling user_id={user.id} from course_id={enrollment.course_id}")
    try:
        # Delete related assignment submissions to prevent constraint violations
        db.query(models.AssignmentSubmission).filter(
            models.AssignmentSubmission.user_id == user.id,
            models.AssignmentSubmission.assignment_id.in_(
                db.query(models.Assignment.id).filter(models.Assignment.course_id == enrollment.course_id)
            )
        ).delete(synchronize_session=False)

        # Delete the enrollment
        deleted_count = db.query(models.Enrollment).filter(
            models.Enrollment.user_id == user.id,
            models.Enrollment.course_id == enrollment.course_id
        ).delete(synchronize_session=False)
        
        db.commit()
        print(f"DEBUG: Successfully deleted {deleted_count} enrollment(s)")
        
        if deleted_count == 0:
            return {"message": "No enrollment found to delete", "status": "no_change"}
            
        return {"message": "Successfully unenrolled", "status": "success"}
    except Exception as e:
        db.rollback()
        print(f"ERROR: Unenrollment failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ================== FILES (GCS HYBRID) ==================

@app.post("/files/upload", dependencies=[Depends(auth.get_current_user)])
def upload_generic_file(file: UploadFile = File(...)):
    """Uploads a generic file to GCS and returns its public URL"""
    try:
        contents = file.file.read()
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'bin'
        unique_name = f"{uuid.uuid4()}.{file_extension}"
        destination_path = f"files/uploads/{unique_name}"
        
        content_type = file.content_type
        if not content_type or content_type == 'application/octet-stream':
            guessed_type, _ = mimetypes.guess_type(file.filename)
            if guessed_type:
                content_type = guessed_type
            elif file.filename.lower().endswith('.webp'):
                content_type = 'image/webp'
                
        public_url = gcs_db.upload_file(contents, destination_path, content_type)
        
        return {"url": public_url, "filename": file.filename, "content_type": content_type}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@app.get("/files/course/{course_id}", response_model=list[schemas.FileResponse])
def get_course_files(course_id: int, user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """Retrieves all files associated with a course"""
    require_course_member(db, user, course_id)
    return db.query(models.File).filter(models.File.course_id == course_id).all()

@app.post("/files/course/{course_id}", response_model=schemas.FileResponse)
def upload_course_file(course_id: int, file: UploadFile = File(...), user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """Uploads a file to GCS and stores the reference in the Files table for a course"""
    require_course_owner(db, user, course_id)
    
    try:
        contents = file.file.read()
        file_extension = file.filename.split('.')[-1]
        unique_name = f"{uuid.uuid4()}.{file_extension}"
        destination_path = f"files/courses/{course_id}/{unique_name}"
        
        content_type = file.content_type
        if not content_type or content_type == 'application/octet-stream':
            guessed_type, _ = mimetypes.guess_type(file.filename)
            if guessed_type:
                content_type = guessed_type
            elif file.filename.lower().endswith('.webp'):
                content_type = 'image/webp'

        # Upload to GCS
        public_url = gcs_db.upload_file(contents, destination_path, content_type)
        
        # Save to Cloud SQL
        db_file = models.File(
            course_id=course_id,
            file_name=file.filename,
            mime_type=content_type,
            gcs_url=public_url
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        
        return db_file
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

# (Redundant list_course_files removed, use get_course_files above)

@app.delete("/files/{file_id}")
def delete_course_file(file_id: int, user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """Deletes a file from the course and from GCS"""
    db_file = db.query(models.File).filter(models.File.id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    require_course_owner(db, user, db_file.course_id)
    
    # Delete from GCS
    gcs_db.delete_file(db_file.gcs_url)
    
    # Delete from database
    db.delete(db_file)
    db.commit()
    
    return {"detail": "File deleted successfully"}

