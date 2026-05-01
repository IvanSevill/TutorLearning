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
        print("Inserting mock users (Teachers)...")
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
        teacher3 = User(
            first_name="Prof",
            last_name="Birch",
            email="birch@tutorlearning.com",
            is_teacher=True,
            password_hash=get_password_hash("password123")
        )
        teacher4 = User(
            first_name="Prof",
            last_name="Rowan",
            email="rowan@tutorlearning.com",
            is_teacher=True,
            password_hash=get_password_hash("password123")
        )
        
        print("Inserting mock users (Students)...")
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
        student3 = User(
            first_name="Brock",
            last_name="Harrison",
            email="brock@tutorlearning.com",
            is_teacher=False,
            password_hash=get_password_hash("password123")
        )
        student4 = User(
            first_name="Dawn",
            last_name="Berlitz",
            email="dawn@tutorlearning.com",
            is_teacher=False,
            password_hash=get_password_hash("password123")
        )
        student5 = User(
            first_name="Gary",
            last_name="Oak",
            email="gary@tutorlearning.com",
            is_teacher=False,
            password_hash=get_password_hash("password123")
        )
        
        db.add_all([
            teacher1, teacher2, teacher3, teacher4, 
            student1, student2, student3, student4, student5
        ])
        db.commit()
        
        # Refresh to get IDs
        for user in [teacher1, teacher2, teacher3, teacher4, student1, student2, student3, student4, student5]:
            db.refresh(user)
        
        print("Inserting mock courses...")
        course1 = Course(
            title="Introduction to Pokemon Biology",
            description="A comprehensive study on the habitats, behaviors, and evolution of various Pokemon species.",
            is_visible=True,
            is_enrollable=True,
            teacher_id=teacher1.id
        )
        course2 = Course(
            title="Advanced Potion Making",
            description="Learn how to craft full restores, max potions, and elixirs from natural ingredients.",
            is_visible=True,
            is_enrollable=True,
            teacher_id=teacher2.id
        )
        course3 = Course(
            title="Draft Course (Hidden)",
            description="This course is not visible to students yet.",
            is_visible=False,
            is_enrollable=False,
            teacher_id=teacher1.id
        )
        course4 = Course(
            title="Field Habitats of the Hoenn Region",
            description="Explore the diverse climates and unique Pokemon distributions of Hoenn.",
            is_visible=True,
            is_enrollable=True,
            teacher_id=teacher3.id
        )
        course5 = Course(
            title="Pokemon Evolution Mythology",
            description="Deep dive into the lore and ancient history surrounding mythical and legendary evolutions.",
            is_visible=True,
            is_enrollable=True,
            teacher_id=teacher4.id
        )
        
        db.add_all([course1, course2, course3, course4, course5])
        db.commit()
        
        for course in [course1, course2, course3, course4, course5]:
            db.refresh(course)
        
        print("Enrolling students...")
        enrollments = [
            Enrollment(user_id=student1.id, course_id=course1.id),
            Enrollment(user_id=student2.id, course_id=course1.id),
            Enrollment(user_id=student1.id, course_id=course2.id),
            Enrollment(user_id=student3.id, course_id=course2.id), # Brock en pociones
            Enrollment(user_id=student4.id, course_id=course4.id), # Dawn en hábitats
            Enrollment(user_id=student5.id, course_id=course1.id), # Gary en biología
            Enrollment(user_id=student5.id, course_id=course5.id), # Gary en mitología
            Enrollment(user_id=student2.id, course_id=course4.id)  # Misty en hábitats
        ]
        
        db.add_all(enrollments)
        db.commit()
        
        print("Creating assignments...")
        future_date_1 = datetime.datetime.utcnow() + datetime.timedelta(days=7)
        future_date_2 = datetime.datetime.utcnow() + datetime.timedelta(days=14)
        past_date = datetime.datetime.utcnow() - datetime.timedelta(days=2)
        
        assignment1 = Assignment(
            course_id=course1.id,
            title="Field Report: Route 1",
            description="Observe and document the behavior of at least 3 wild Pokemon on Route 1.",
            due_date=future_date_1
        )
        assignment2 = Assignment(
            course_id=course1.id,
            title="Evolution Essay",
            description="Write a 500-word essay on the mechanics of evolution stones.",
            due_date=past_date
        )
        assignment3 = Assignment(
            course_id=course2.id,
            title="Berry Blending Practical",
            description="Submit a video of your attempt at creating a perfect Oran Berry blend.",
            due_date=future_date_2
        )
        assignment4 = Assignment(
            course_id=course4.id,
            title="Weather Institute Case Study",
            description="Analyze the impact of Castform's weather changes on local flora.",
            due_date=future_date_1
        )
        
        db.add_all([assignment1, assignment2, assignment3, assignment4])
        db.commit()
        
        for assignment in [assignment1, assignment2, assignment3, assignment4]:
            db.refresh(assignment)
        
        print("Submitting assignments...")
        submissions = [
            AssignmentSubmission(
                user_id=student1.id,
                assignment_id=assignment1.id,
                grade=None,
                submission_file_url="https://example.com/ash_report.pdf"
            ),
            AssignmentSubmission(
                user_id=student2.id,
                assignment_id=assignment2.id,
                grade=95.5,
                submission_file_url="https://example.com/misty_essay.pdf"
            ),
            AssignmentSubmission(
                user_id=student5.id,
                assignment_id=assignment2.id,
                grade=99.0, # A Gary siempre le va bien
                submission_file_url="https://example.com/gary_superior_essay.pdf"
            ),
            AssignmentSubmission(
                user_id=student3.id,
                assignment_id=assignment3.id,
                grade=None,
                submission_file_url="https://example.com/brock_berry_video.mp4"
            )
        ]
        
        db.add_all(submissions)
        db.commit()
        
        print("Creating text blocks (feed)...")
        posts = [
            TextBlock(
                course_id=course1.id,
                title="Welcome to the class!",
                content="Hello everyone. I'm excited to start this semester. Please check the assignments tab for your first task."
            ),
            TextBlock(
                course_id=course1.id,
                title="Reminder: Field Trip tomorrow",
                content="Don't forget your Pokedex and some pokeballs. We meet at 8 AM sharp."
            ),
            TextBlock(
                course_id=course2.id,
                title="Safety Warning",
                content="Please remember to wear safety goggles when mixing Pecha berries with paralyzants."
            ),
            TextBlock(
                course_id=course4.id,
                title="Syllabus Update",
                content="We will be covering the desert routes of Hoenn earlier than expected. Please read chapter 4."
            )
        ]
        
        db.add_all(posts)
        db.commit()
        
        print("\nDatabase successfully seeded!")
        print("=============================")
        print("Test Accounts (Password: password123)")
        print("--- TEACHERS ---")
        print("- Prof Oak: oak@tutorlearning.com")
        print("- Dr. Elm: elm@tutorlearning.com")
        print("- Prof Birch: birch@tutorlearning.com")
        print("- Prof Rowan: rowan@tutorlearning.com")
        print("--- STUDENTS ---")
        print("- Ash: ash@tutorlearning.com")
        print("- Misty: misty@tutorlearning.com")
        print("- Brock: brock@tutorlearning.com")
        print("- Dawn: dawn@tutorlearning.com")
        print("- Gary: gary@tutorlearning.com")
        print("=============================")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()