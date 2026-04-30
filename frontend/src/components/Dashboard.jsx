import React, { useState, useEffect } from 'react';
import { API_URL } from '../App';

const Dashboard = ({ user, onLogout }) => {
  const [courses, setCourses] = useState([]);
  const [enrollments, setEnrollments] = useState([]);
  const [newCourse, setNewCourse] = useState({ title: '', description: '' });

  const fetchData = async () => {
    try {
      const [coursesRes, enrollmentsRes] = await Promise.all([
        fetch(`${API_URL}/courses/`),
        fetch(`${API_URL}/enrollments/user/${user.id}`)
      ]);
      const coursesData = await coursesRes.json();
      const enrollmentsData = await enrollmentsRes.json();
      setCourses(coursesData);
      setEnrollments(enrollmentsData);
    } catch (err) {
      console.error("Failed to fetch dashboard data", err);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleEnroll = async (courseId) => {
    const response = await fetch(`${API_URL}/enrollments/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: user.id, course_id: courseId })
    });
    if (response.ok) fetchData();
  };

  const handleCreateCourse = async (e) => {
    e.preventDefault();
    const response = await fetch(`${API_URL}/courses/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...newCourse, is_visible: true, is_enrollable: true })
    });
    if (response.ok) {
      setNewCourse({ title: '', description: '' });
      fetchData();
    }
  };

  const enrolledIds = enrollments.map(e => e.course_id);

  return (
    <div>
      <div className="navbar glass-card" style={{ padding: '0.5rem 1.5rem', marginBottom: '2rem' }}>
        <h2 style={{ margin: 0, fontSize: '1.25rem' }}>Tutor-Learning</h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          <div>
            <span style={{ fontWeight: 'bold' }}>{user.first_name} {user.last_name}</span>
            <span className="role-badge" style={{ marginLeft: '10px' }}>{user.is_teacher ? 'Teacher' : 'Student'}</span>
          </div>
          <button onClick={onLogout} style={{ background: '#ef4444', padding: '0.5rem 1rem' }}>Logout</button>
        </div>
      </div>

      <div style={{ display: 'grid', gap: '2rem' }}>
        
        {/* TEACHER SECTION */}
        {user.is_teacher && (
          <section className="glass-card" style={{ borderLeft: '4px solid #6366f1' }}>
            <h3 style={{ marginTop: 0 }}>👨‍🏫 Teacher Management</h3>
            <form onSubmit={handleCreateCourse} style={{ display: 'flex', gap: '10px', marginBottom: '1.5rem' }}>
              <input 
                placeholder="Course Title" 
                value={newCourse.title} 
                onChange={e => setNewCourse({...newCourse, title: e.target.value})}
                required 
                style={{ margin: 0 }}
              />
              <input 
                placeholder="Description" 
                value={newCourse.description} 
                onChange={e => setNewCourse({...newCourse, description: e.target.value})}
                style={{ margin: 0 }}
              />
              <button type="submit" style={{ whiteSpace: 'nowrap' }}>Create Course</button>
            </form>
            
            <div className="grid">
              {courses.filter(c => true /* In real app, filter by teacher_id */).map(course => (
                <div key={course.id} className="glass-card" style={{ padding: '1rem' }}>
                  <h4 style={{ margin: 0 }}>{course.title}</h4>
                  <p style={{ color: '#64748b', fontSize: '0.9rem' }}>{course.description}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* STUDENT SECTION */}
        <section className="glass-card">
          <h3 style={{ marginTop: 0 }}>🎓 Student Dashboard</h3>
          
          <h4>My Enrollments</h4>
          <div className="grid">
            {enrollments.map(enrollment => (
              <div key={enrollment.course_id} className="glass-card" style={{ padding: '1rem', borderLeft: '4px solid #10b981' }}>
                <h4 style={{ margin: 0 }}>{enrollment.course?.title || `Course ${enrollment.course_id}`}</h4>
                <p style={{ color: '#10b981', fontSize: '0.8rem', fontWeight: 'bold' }}>Enrolled</p>
              </div>
            ))}
          </div>

          <h4 style={{ marginTop: '2rem' }}>Explore Available Courses</h4>
          <div className="grid">
            {courses.filter(c => !enrolledIds.includes(c.id)).map(course => (
              <div key={course.id} className="glass-card" style={{ padding: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                  <h4 style={{ margin: 0 }}>{course.title}</h4>
                  <button onClick={() => handleEnroll(course.id)} style={{ padding: '0.25rem 0.75rem', fontSize: '0.8rem' }}>Enroll</button>
                </div>
                <p style={{ color: '#64748b', fontSize: '0.9rem', marginTop: '0.5rem' }}>{course.description}</p>
              </div>
            ))}
          </div>
        </section>

      </div>
    </div>
  );
};

export default Dashboard;
