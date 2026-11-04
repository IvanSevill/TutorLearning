import os
import datetime
import random
import secrets
from sqlalchemy.orm import Session
from database import engine, SessionLocal, Base
from models import User, Course, Enrollment, Assignment, AssignmentSubmission, TextBlock
from main import get_password_hash

# Invented people. example.com is reserved (RFC 2606), so these are not anyone's addresses.
TEACHERS = [
    ("Nora", "Vance", "nora.vance@example.com"),
    ("Theo", "Marsh", "theo.marsh@example.com"),
    ("Imani", "Castellan", "imani.castellan@example.com"),
    ("Rowan", "Pell", "rowan.pell@example.com"),
    ("Oriel", "Thackett", "oriel.thackett@example.com"),
    ("Soren", "Bly", "soren.bly@example.com"),
    ("Mina", "Okafor-Lund", "mina.okafor-lund@example.com"),
    ("Tomas", "Quill", "tomas.quill@example.com"),
    ("Adele", "Fenwick", "adele.fenwick@example.com"),
    ("Kiran", "Dovey", "kiran.dovey@example.com"),
]

STUDENTS = [
    ("Sam", "Rivera", "sam.rivera@example.com"),
    ("Lena", "Ortiz", "lena.ortiz@example.com"),
    ("Juno", "Arkwright", "juno.arkwright@example.com"),
    ("Milo", "Trent", "milo.trent@example.com"),
    ("Esme", "Varga", "esme.varga@example.com"),
    ("Dara", "Holloway", "dara.holloway@example.com"),
    ("Felix", "Noor", "felix.noor@example.com"),
    ("Wren", "Tallis", "wren.tallis@example.com"),
    ("Arlo", "Benn", "arlo.benn@example.com"),
    ("Talia", "Morrow", "talia.morrow@example.com"),
]

def get_seed_password():
    """SEED_USER_PASSWORD if set, otherwise a new random password for this run"""
    return os.getenv("SEED_USER_PASSWORD") or secrets.token_urlsafe(16)

def create_email_triggers():
    """Run after the seed rows exist: the triggers queue mail for every later insert"""
    with engine.begin() as conn:
        from sqlalchemy import text
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


def seed_database():
    print("Dropping all existing tables...")
    Base.metadata.drop_all(bind=engine)
    
    print("Recreating tables...")
    Base.metadata.create_all(bind=engine)
    
    seed_password = get_seed_password()
    password_hash = get_password_hash(seed_password)

    db: Session = SessionLocal()
    
    try:
        print("Inserting mock users (Teachers)...")
        teachers = []
        for first, last, email in TEACHERS:
            teacher = User(
                first_name=first,
                last_name=last,
                email=email,
                is_teacher=True,
                password_hash=password_hash
            )
            teachers.append(teacher)
            db.add(teacher)
        
        print("Inserting mock users (Students)...")
        students = []
        for first, last, email in STUDENTS:
            student = User(
                first_name=first,
                last_name=last,
                email=email,
                is_teacher=False,
                password_hash=password_hash
            )
            students.append(student)
            db.add(student)
        
        db.commit()
        for t in teachers: db.refresh(t)
        for s in students: db.refresh(s)
        
        print("Inserting a massive amount of courses...")
        
        course_templates = [
            # Pokemon
            ("Introduction to Pokemon Biology", "A comprehensive study on the habitats, behaviors, and evolution of species.", "Vance"),
            ("Advanced Potion Making", "Learn how to craft full restores, max potions, and elixirs.", "Marsh"),
            ("Hoenn Region Habitats", "Explore the diverse climates and unique Pokemon distributions of Hoenn.", "Castellan"),
            ("Pokemon Evolution Lore", "Deep dive into the ancient history of mythical evolutions.", "Pell"),
            
            # Magic
            ("Defense Against the Dark Arts", "Mastering defensive spells and recognizing dark creatures.", "Thackett"),
            ("Potions and Alchemy", "The delicate art of potion-making and chemical transformations.", "Bly"),
            ("Transfiguration 101", "The science of changing one object into another.", "Thackett"),
            ("Care of Magical Creatures", "How to feed, groom, and not get killed by a Hippogriff.", "Pell"),
            
            # Tech
            ("Kernel Development", "Understanding the heart of the Linux operating system.", "Okafor-Lund"),
            ("History of Computing", "From the Analytical Engine to modern AI.", "Dovey"),
            ("Fullstack Web Development", "Building modern applications with React and FastAPI.", "Dovey"),
            ("Cybersecurity Essentials", "Protecting systems from digital attacks and vulnerabilities.", "Okafor-Lund"),
            
            # Science
            ("Radioactivity and Physics", "The groundbreaking study of atomic decay and energy.", "Quill"),
            ("Organic Chemistry", "The study of carbon-based compounds and their reactions.", "Quill"),
            ("Quantum Mechanics", "Exploring the behavior of matter and energy at the molecular level.", "Pell"),
            
            # Arts & Cooking
            ("Mastering the Beef Wellington", "A classic showpiece dish explained step-by-step.", "Fenwick"),
            ("Kitchen Management", "How to run a 3-star Michelin kitchen without losing your mind.", "Fenwick"),
            ("Fine Arts History", "A journey through the Renaissance and Impressionism.", "Vance"),
            
            # Miscellaneous
            ("Modern Philosophy", "Analyzing the works of Kant, Nietzsche, and Satre.", "Marsh"),
            ("World War II Strategy", "An in-depth look at the major battles and political moves.", "Castellan"),
            ("Marine Biology", "Life under the sea, from coral reefs to the deep abyss.", "Quill"),
            ("Game Theory", "Mathematical models of strategic interaction between rational decision-makers.", "Dovey"),
            ("Ancient Egyptology", "Pyramids, pharaohs, and the secrets of the Nile.", "Pell"),
            ("Photography Basics", "Lighting, composition, and the soul of the image.", "Vance"),
            ("Introduction to Psychology", "Understanding human behavior and the mind.", "Marsh")
        ]
        
        course_image_map = {
            "Introduction to Pokemon Biology": "pokemon.jpg",
            "Advanced Potion Making": "pokemon.jpg",
            "Hoenn Region Habitats": "pokemon.jpg",
            "Pokemon Evolution Lore": "pokemon.jpg",
            "Defense Against the Dark Arts": "hogwarts.jpg",
            "Potions and Alchemy": "hogwarts.jpg",
            "Transfiguration 101": "hogwarts.jpg",
            "Care of Magical Creatures": "hogwarts.jpg",
            "Kernel Development": "tech.jpg",
            "History of Computing": "tech.jpg",
            "Fullstack Web Development": "tech.jpg",
            "Cybersecurity Essentials": "tech.jpg",
            "Radioactivity and Physics": "science.jpg",
            "Organic Chemistry": "science.jpg",
            "Quantum Mechanics": "science.jpg",
            "Mastering the Beef Wellington": "artscooking.jpg",
            "Kitchen Management": "artscooking.jpg",
            "Fine Arts History": "artscooking.jpg",
            "Modern Philosophy": "miscellaneous.jpg",
            "World War II Strategy": "miscellaneous.jpg",
            "Marine Biology": "miscellaneous.jpg",
            "Game Theory": "miscellaneous.jpg",
            "Ancient Egyptology": "miscellaneous.jpg",
            "Photography Basics": "miscellaneous.jpg",
            "Introduction to Psychology": "miscellaneous.jpg"
        }
        
        # Helper to find teacher by last name
        def get_teacher_by_name(last_name):
            for t in teachers:
                if t.last_name == last_name: return t.id
            return teachers[0].id # Fallback
            
        courses = []
        bucket_name = os.getenv("GCS_BUCKET_NAME", "tutorlearning-bucket")
        for title, desc, t_name in course_templates:
            img_file = course_image_map.get(title, "miscellaneous.jpg")
            img_url = f"https://storage.googleapis.com/{bucket_name}/courses/{img_file}"
            
            course = Course(
                title=title,
                description=desc,
                is_visible=True,
                is_enrollable=True,
                teacher_id=get_teacher_by_name(t_name),
                image_url=img_url
            )
            courses.append(course)
            db.add(course)
        
        db.commit()
        for c in courses: db.refresh(c)
        
        print(f"Total courses created: {len(courses)}")
        
        print("Enrolling students randomly...")
        enrollments = []
        for student in students:
            # Each student enrolls in 3-5 random courses
            my_courses = random.sample(courses, random.randint(3, 6))
            for c in my_courses:
                # Don't enroll if they are the teacher (though we split teachers and students, good practice)
                if c.teacher_id != student.id:
                    enrollments.append(Enrollment(user_id=student.id, course_id=c.id))
        
        db.add_all(enrollments)
        db.commit()
        
        print("Creating some assignments...")
        assignments = []
        for i, course in enumerate(courses[:10]): # Only first 10 courses for variety
            due = datetime.datetime.utcnow() + datetime.timedelta(days=random.randint(1, 20))
            a = Assignment(
                course_id=course.id,
                title=f"Initial Project: {course.title}",
                description=f"Research and submit your findings about {course.title.split()[-1]}.",
                due_date=due
            )
            assignments.append(a)
            db.add(a)
        
        db.commit()
        
        print("Creating text blocks (feed) for all courses...")
        posts = []
        welcome_messages = [
            "Welcome everyone! I'm excited to start this journey with you.",
            "Please read the syllabus before our first session.",
            "Assignments are now live. Good luck!",
            "Feel free to ask questions in the comments (if we had them).",
            "This course will challenge your limits. Be prepared.",
            "Science is about curiosity. Let's explore together.",
            "The magic of learning is real. Welcome!"
        ]
        
        for course in courses:
            post = TextBlock(
                course_id=course.id,
                title="Welcome to the course",
                content=random.choice(welcome_messages)
            )
            posts.append(post)
            # Add a second post to some courses
            if random.random() > 0.5:
                posts.append(TextBlock(
                    course_id=course.id,
                    title="Important Update",
                    content="The schedule for next week has been slightly adjusted. Check your email."
                ))
        
        db.add_all(posts)
        db.commit()

        print("Recreating triggers...")
        create_email_triggers()
        
        print("\nDatabase successfully seeded with MASSIVE data!")
        print("=============================")
        print(f"Teachers: {len(teachers)}")
        print(f"Students: {len(students)}")
        print(f"Courses: {len(courses)}")
        print(f"Enrollments: {len(enrollments)}")
        print("=============================")
        print(f"Test Accounts (Password: {seed_password})")
        print(f"- Teacher: {TEACHERS[0][2]}")
        print(f"- Student: {STUDENTS[0][2]}")
        print("=============================")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()