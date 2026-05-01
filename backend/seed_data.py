import os
import datetime
from sqlalchemy.orm import Session
from database import engine, SessionLocal, Base
from models import User, Course, Enrollment, Assignment, AssignmentSubmission, TextBlock
from main import get_password_hash

def seed_database():
    print("Dropping all existing tables...")
    Base.metadata.drop_all(bind=engine)
    
    print("Recreating tables...")
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    
    try:
        print("Inserting mock users...")
        teacher1 = User(
            first_name="Prof",
            last_name="Oak",
            email="oak@tutorlearning.com",
            is_teacher=True,
            password_hash=get_password_hash("password123")
        )
        teacher2 = User(
            first_name="Dr.",
            last_name="Elm",
            email="elm@tutorlearning.com",
            is_teacher=True,
            password_hash=get_password_hash("password123")
        )
        
        student1 = User(
            first_name="Ash",
            last_name="Ketchum",
            email="ash@tutorlearning.com",
            is_teacher=False,
            password_hash=get_password_hash("password123")
        )
        student2 = User(
            first_name="Misty",
            last_name="Waterflower",
            email="misty@tutorlearning.com",
            is_teacher=False,
            password_hash=get_password_hash("password123")
        )
        
        db.add_all([teacher1, teacher2, student1, student2])
        db.commit()
        
        # Refresh to get IDs
        db.refresh(teacher1)
        db.refresh(teacher2)
        db.refresh(student1)
        db.refresh(student2)
        
        print("Inserting mock courses...")
        course1 = Course(
            title="Introduction to Pokemon Biology",
            description="A comprehensive study on the habitats, behaviors, and evolution of various Pokemon species.",
            is_visible=True,
            is_enrollable=True,
            teacher_id=teacher1.id,
            image_url="https://images.unsplash.com/photo-1613771404784-3a5686aa2be3?q=80&w=2069&auto=format&fit=crop"
        )
        course2 = Course(
            title="Advanced Potion Making",
            description="Learn how to craft full restores, max potions, and elixirs from natural ingredients.",
            is_visible=True,
            is_enrollable=True,
            teacher_id=teacher2.id,
            image_url="https://images.unsplash.com/photo-1585250015549-9dfa891007d6?q=80&w=2071&auto=format&fit=crop"
        )
        course3 = Course(
            title="Draft Course (Hidden)",
            description="This course is not visible to students yet.",
            is_visible=False,
            is_enrollable=False,
            teacher_id=teacher1.id
        )
        
        db.add_all([course1, course2, course3])
        db.commit()
        
        db.refresh(course1)
        db.refresh(course2)
        
        print("Enrolling students...")
        enrollment1 = Enrollment(user_id=student1.id, course_id=course1.id)
        enrollment2 = Enrollment(user_id=student2.id, course_id=course1.id)
        enrollment3 = Enrollment(user_id=student1.id, course_id=course2.id)
        
        db.add_all([enrollment1, enrollment2, enrollment3])
        db.commit()
        
        print("Creating assignments...")
        future_date = datetime.datetime.utcnow() + datetime.timedelta(days=7)
        past_date = datetime.datetime.utcnow() - datetime.timedelta(days=2)
        
        assignment1 = Assignment(
            course_id=course1.id,
            title="Field Report: Route 1",
            description="Observe and document the behavior of at least 3 wild Pokemon on Route 1.",
            due_date=future_date
        )
        assignment2 = Assignment(
            course_id=course1.id,
            title="Evolution Essay",
            description="Write a 500-word essay on the mechanics of evolution stones.",
            due_date=past_date
        )
        
        db.add_all([assignment1, assignment2])
        db.commit()
        
        db.refresh(assignment1)
        db.refresh(assignment2)
        
        print("Submitting assignments...")
        submission1 = AssignmentSubmission(
            user_id=student1.id,
            assignment_id=assignment1.id,
            grade=None,
            submission_file_url="https://example.com/ash_report.pdf"
        )
        submission2 = AssignmentSubmission(
            user_id=student2.id,
            assignment_id=assignment2.id,
            grade=95.5,
            submission_file_url="https://example.com/misty_essay.pdf"
        )
        
        db.add_all([submission1, submission2])
        db.commit()
        
        print("Creating text blocks (feed)...")
        post1 = TextBlock(
            course_id=course1.id,
            title="Welcome to the class!",
            content="Hello everyone. I'm excited to start this semester. Please check the assignments tab for your first task."
        )
        post2 = TextBlock(
            course_id=course1.id,
            title="Reminder: Field Trip tomorrow",
            content="Don't forget your Pokedex and some pokeballs. We meet at 8 AM sharp."
        )
        
        db.add_all([post1, post2])
        db.commit()
        
        print("\nDatabase successfully seeded!")
        print("=============================")
        print("Test Accounts (Password: password123)")
        print("- Teacher 1: oak@tutorlearning.com")
        print("- Teacher 2: elm@tutorlearning.com")
        print("- Student 1: ash@tutorlearning.com")
        print("- Student 2: misty@tutorlearning.com")
        print("=============================")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
