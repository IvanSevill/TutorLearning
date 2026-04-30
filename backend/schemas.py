from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# ===================== USERS =====================

class UserBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    is_teacher: bool = False

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_teacher: Optional[bool] = None

class UserResponse(UserBase):
    id: int

    class Config:
        orm_mode = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    message: str
    user: UserResponse

# ===================== COURSES =====================

class CourseBase(BaseModel):
    title: str
    description: Optional[str] = None
    is_visible: bool = True
    is_enrollable: bool = True

class CourseCreate(CourseBase):
    pass

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_visible: Optional[bool] = None
    is_enrollable: Optional[bool] = None

class CourseResponse(CourseBase):
    id: int

    class Config:
        orm_mode = True

# ===================== ENROLLMENTS =====================

class EnrollmentCreate(BaseModel):
    course_id: int
    user_id: int

class EnrollmentResponse(BaseModel):
    user_id: int
    course_id: int
    enrollment_date: datetime

    class Config:
        orm_mode = True

class EnrollmentListResponse(BaseModel):
    user_id: int
    course_id: int
    enrollment_date: datetime
    user: Optional[UserResponse] = None
    course: Optional[CourseResponse] = None

    class Config:
        orm_mode = True

# ===================== ASSIGNMENTS =====================

class AssignmentBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None

class AssignmentCreate(AssignmentBase):
    pass

class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None

class AssignmentResponse(AssignmentBase):
    id: int
    course_id: int

    class Config:
        orm_mode = True

# ===================== ASSIGNMENT SUBMISSIONS =====================

class AssignmentSubmissionBase(BaseModel):
    grade: Optional[float] = None
    submission_file_url: Optional[str] = None

class AssignmentSubmissionCreate(AssignmentSubmissionBase):
    assignment_id: int

class AssignmentSubmissionUpdate(BaseModel):
    grade: Optional[float] = None

class AssignmentSubmissionResponse(AssignmentSubmissionBase):
    user_id: int
    assignment_id: int
    submission_date: datetime

    class Config:
        orm_mode = True

# ===================== FILES =====================

class FileResponse(BaseModel):
    id: int
    course_id: int
    file_name: str
    mime_type: Optional[str] = None
    gcs_url: str
    upload_date: datetime

    class Config:
        orm_mode = True

# ===================== TEXT BLOCKS =====================

class TextBlockBase(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class TextBlockCreate(TextBlockBase):
    pass

class TextBlockUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class TextBlockResponse(TextBlockBase):
    id: int
    course_id: int

    class Config:
        orm_mode = True