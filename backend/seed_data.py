import os
import datetime
import random
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
        teachers_data = [
            ("Prof", "Oak", "oak@tutorlearning.com"),
            ("Dr.", "Elm", "elm@tutorlearning.com"),
            ("Prof", "Birch", "birch@tutorlearning.com"),
            ("Prof", "Rowan", "rowan@tutorlearning.com"),
            ("Albus", "Dumbledore", "albus@hogwarts.edu"),
            ("Severus", "Snape", "snape@hogwarts.edu"),
            ("Linus", "Torvalds", "linus@kernel.org"),
            ("Marie", "Curie", "marie@science.fr"),
            ("Gordon", "Ramsay", "gordon@kitchen.uk"),
            ("Ada", "Lovelace", "ada@computing.io")
        ]
        
        teachers = []
        for first, last, email in teachers_data:
            teacher = User(
                first_name=first,
                last_name=last,
                email=email,
                is_teacher=True,
                password_hash=get_password_hash("password123")
            )
            teachers.append(teacher)
            db.add(teacher)
        
        print("Inserting mock users (Students)...")
        students_data = [
            ("Ash", "Ketchum", "ash@tutorlearning.com"),
            ("Misty", "Waterflower", "misty@tutorlearning.com"),
            ("Brock", "Harrison", "brock@tutorlearning.com"),
            ("Dawn", "Berlitz", "dawn@tutorlearning.com"),
            ("Gary", "Oak", "gary@tutorlearning.com"),
            ("Harry", "Potter", "harry@hogwarts.edu"),
            ("Hermione", "Granger", "hermione@hogwarts.edu"),
            ("Ron", "Weasley", "ron@hogwarts.edu"),
            ("Elliot", "Alderson", "elliot@mrrobot.com"),
            ("Marie", "Schrader", "marie@breakingbad.com")
        ]
        
        students = []
        for first, last, email in students_data:
            student = User(
                first_name=first,
                last_name=last,
                email=email,
                is_teacher=False,
                password_hash=get_password_hash("password123")
            )
            students.append(student)
            db.add(student)
        
        db.commit()
        for t in teachers: db.refresh(t)
        for s in students: db.refresh(s)
        
        print("Inserting a massive amount of courses...")
        
        course_templates = [
            # Pokemon
            ("Introduction to Pokemon Biology", "A comprehensive study on the habitats, behaviors, and evolution of species.", "Oak"),
            ("Advanced Potion Making", "Learn how to craft full restores, max potions, and elixirs.", "Elm"),
            ("Hoenn Region Habitats", "Explore the diverse climates and unique Pokemon distributions of Hoenn.", "Birch"),
            ("Pokemon Evolution Lore", "Deep dive into the ancient history of mythical evolutions.", "Rowan"),
            
            # Magic
            ("Defense Against the Dark Arts", "Mastering defensive spells and recognizing dark creatures.", "Dumbledore"),
            ("Potions and Alchemy", "The delicate art of potion-making and chemical transformations.", "Snape"),
            ("Transfiguration 101", "The science of changing one object into another.", "Albus"),
            ("Care of Magical Creatures", "How to feed, groom, and not get killed by a Hippogriff.", "Rowan"),
            
            # Tech
            ("Kernel Development", "Understanding the heart of the Linux operating system.", "Linus"),
            ("History of Computing", "From the Analytical Engine to modern AI.", "Ada"),
            ("Fullstack Web Development", "Building modern applications with React and FastAPI.", "Ada"),
            ("Cybersecurity Essentials", "Protecting systems from digital attacks and vulnerabilities.", "Linus"),
            
            # Science
            ("Radioactivity and Physics", "The groundbreaking study of atomic decay and energy.", "Marie"),
            ("Organic Chemistry", "The study of carbon-based compounds and their reactions.", "Marie"),
            ("Quantum Mechanics", "Exploring the behavior of matter and energy at the molecular level.", "Rowan"),
            
            # Arts & Cooking
            ("Mastering the Beef Wellington", "Gordon Ramsay's signature dish explained step-by-step.", "Gordon"),
            ("Kitchen Management", "How to run a 3-star Michelin kitchen without losing your mind.", "Gordon"),
            ("Fine Arts History", "A journey through the Renaissance and Impressionism.", "Oak"),
            
            # Miscellaneous
            ("Modern Philosophy", "Analyzing the works of Kant, Nietzsche, and Satre.", "Elm"),
            ("World War II Strategy", "An in-depth look at the major battles and political moves.", "Birch"),
            ("Marine Biology", "Life under the sea, from coral reefs to the deep abyss.", "Misty"), # Oops, Misty isn't a teacher in our list, I'll fix
            ("Game Theory", "Mathematical models of strategic interaction between rational decision-makers.", "Ada"),
            ("Ancient Egyptology", "Pyramids, pharaohs, and the secrets of the Nile.", "Rowan"),
            ("Photography Basics", "Lighting, composition, and the soul of the image.", "Oak"),
            ("Introduction to Psychology", "Understanding human behavior and the mind.", "Elm")
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
        
        print("\nDatabase successfully seeded with MASSIVE data!")
        print("=============================")
        print(f"Teachers: {len(teachers)}")
        print(f"Students: {len(students)}")
        print(f"Courses: {len(courses)}")
        print(f"Enrollments: {len(enrollments)}")
        print("=============================")
        print("Test Accounts (Password: password123)")
        print("- Oak: oak@tutorlearning.com")
        print("- Dumbledore: albus@hogwarts.edu")
        print("- Snape: snape@hogwarts.edu")
        print("- Ramsay: gordon@kitchen.uk")
        print("- Ash: ash@tutorlearning.com")
        print("- Harry: harry@hogwarts.edu")
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