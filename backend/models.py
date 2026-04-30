from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, Numeric, Enum, text
from sqlalchemy.orm import relationship
from database import Base
import datetime
import enum

class User(Base):
    __tablename__ = "Users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    is_teacher = Column(Boolean, default=False, nullable=False)
    password_hash = Column(String(255), nullable=False)

    enrollments = relationship("Enrollment", back_populates="user")
    submissions = relationship("AssignmentSubmission", back_populates="user")

class Course(Base):
    __tablename__ = "Courses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    is_visible = Column(Boolean, nullable=False, default=True)
    is_enrollable = Column(Boolean, nullable=False, default=True)
    teacher_id = Column(Integer, ForeignKey("Users.id"), nullable=True)

    teacher = relationship("User")
    enrollments = relationship("Enrollment", back_populates="course")
    assignments = relationship("Assignment", back_populates="course")
    files = relationship("File", back_populates="course")
    text_blocks = relationship("TextBlock", back_populates="course")

class Enrollment(Base):
    __tablename__ = "Enrollments"

    user_id = Column(Integer, ForeignKey("Users.id"), primary_key=True)
    course_id = Column(Integer, ForeignKey("Courses.id"), primary_key=True)
    enrollment_date = Column(DateTime, default=datetime.datetime.utcnow, server_default=text("CURRENT_TIMESTAMP"))

    user = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")

class Assignment(Base):
    __tablename__ = "Assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("Courses.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True)

    course = relationship("Course", back_populates="assignments")
    submissions = relationship("AssignmentSubmission", back_populates="assignment")

class AssignmentSubmission(Base):
    __tablename__ = "AssignmentSubmissions"

    user_id = Column(Integer, ForeignKey("Users.id"), primary_key=True)
    assignment_id = Column(Integer, ForeignKey("Assignments.id"), primary_key=True)
    submission_date = Column(DateTime, default=datetime.datetime.utcnow, server_default=text("CURRENT_TIMESTAMP"))
    grade = Column(Numeric(5, 2), nullable=True)
    submission_file_url = Column(String(500), nullable=True)

    user = relationship("User", back_populates="submissions")
    assignment = relationship("Assignment", back_populates="submissions")

class File(Base):
    __tablename__ = "Files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("Courses.id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    mime_type = Column(String(50), nullable=True)
    gcs_url = Column(String(500), nullable=False)
    upload_date = Column(DateTime, default=datetime.datetime.utcnow, server_default=text("CURRENT_TIMESTAMP"))

    course = relationship("Course", back_populates="files")

class TextBlock(Base):
    __tablename__ = "TextBlocks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("Courses.id"), nullable=False)
    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=True)

    course = relationship("Course", back_populates="text_blocks")

class EmailStatus(enum.Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"

class EmailQueue(Base):
    __tablename__ = "EmailQueue"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recipient_email = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(Enum(EmailStatus), default=EmailStatus.PENDING)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, server_default=text("CURRENT_TIMESTAMP"))