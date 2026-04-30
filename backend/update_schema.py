from database import engine
from sqlalchemy import text

with engine.connect() as conn:
    print("Updating schema...")
    try:
        conn.execute(text('ALTER TABLE Courses ADD COLUMN teacher_id INT'))
        print("Column teacher_id added.")
    except Exception as e:
        print(f"Column might already exist: {e}")
        
    try:
        conn.execute(text('ALTER TABLE Courses ADD CONSTRAINT fk_teacher FOREIGN KEY (teacher_id) REFERENCES Users(id)'))
        print("Foreign key constraint added.")
    except Exception as e:
        print(f"Constraint might already exist: {e}")
        
    conn.commit()
    print("Done.")
