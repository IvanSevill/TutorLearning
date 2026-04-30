import { useState, useEffect, useCallback } from 'react';
import { API_URL } from '../App';

const Dashboard = ({ user, onLogout, onSelectCourse }) => {
  const [courses, setCourses] = useState([]);
  const [enrollments, setEnrollments] = useState([]);
  const [newCourse, setNewCourse] = useState({ title: '', description: '' });
  const [activeTab, setActiveTab] = useState('my-courses');
  const [isModalOpen, setIsModalOpen] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [coursesRes, enrollmentsRes] = await Promise.all([
        fetch(`${API_URL}/courses/`),
        fetch(`${API_URL}/enrollments/user/${user.id}`)
      ]);
      const coursesData = await coursesRes.json();
      const enrollmentsData = await enrollmentsRes.json();
      
      console.log("Dashboard fetch:", { coursesCount: coursesData.length, userId: user.id });
      
      setCourses(coursesData);
      setEnrollments(enrollmentsData);
    } catch (err) {
      console.error("Failed to fetch dashboard data", err);
    }
  }, [user.id]);

  useEffect(() => {
    fetchData();
  }, [fetchData, activeTab]);

  const handleEnroll = async (courseId) => {
    try {
      const response = await fetch(`${API_URL}/enrollments/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: user.id, course_id: courseId })
      });
      if (response.ok) {
        fetchData();
        alert("Enrolled successfully!");
      } else {
        const data = await response.json();
        alert(data.detail || "Enrollment failed");
      }
    } catch (err) {
      console.error("Enroll error:", err);
    }
  };

  const handleCreateCourse = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API_URL}/courses/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          title: newCourse.title, 
          description: newCourse.description, 
          teacher_id: user.id,
          is_visible: true, 
          is_enrollable: true 
        })
      });
      if (response.ok) {
        setNewCourse({ title: '', description: '' });
        setIsModalOpen(false);
        fetchData();
      } else {
        const data = await response.json();
        alert(data.detail || "Creation failed");
      }
    } catch (err) {
      console.error("Create error:", err);
    }
  };

  const handleDeleteCourse = async (courseId) => {
    if (!window.confirm("Are you sure you want to PERMANENTLY delete this course and all its data?")) return;
    try {
      const response = await fetch(`${API_URL}/courses/${courseId}`, {
        method: 'DELETE'
      });
      if (response.ok) {
        fetchData();
      } else {
        const data = await response.json();
        alert(data.detail || "Delete failed");
      }
    } catch (err) {
      console.error("Delete error:", err);
    }
  };

  const enrolledIds = enrollments.map(e => e.course_id);

  return (
    <div>
      {/* NAVBAR */}
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

      {/* TABS */}
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem' }}>
        <button 
          onClick={() => setActiveTab('my-courses')}
          style={{ 
            background: activeTab === 'my-courses' ? 'linear-gradient(135deg, #6366f1, #a855f7)' : 'white',
            color: activeTab === 'my-courses' ? 'white' : '#64748b',
            flex: 1
          }}
        >
          My Courses
        </button>
        <button 
          onClick={() => setActiveTab('explore')}
          style={{ 
            background: activeTab === 'explore' ? 'linear-gradient(135deg, #6366f1, #a855f7)' : 'white',
            color: activeTab === 'explore' ? 'white' : '#64748b',
            flex: 1
          }}
        >
          Explore Available
        </button>
      </div>

      <div style={{ display: 'grid', gap: '2rem' }}>
        
        {activeTab === 'my-courses' && (
          <>
            {/* TEACHER SECTION */}
            {user.is_teacher && (
              <section className="glass-card" style={{ borderLeft: '4px solid #6366f1' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                  <h3 style={{ margin: 0 }}>👨‍🏫 My Taught Courses</h3>
                  <button onClick={() => setIsModalOpen(true)} style={{ background: '#6366f1' }}>+ Create New Course</button>
                </div>
                
                <div className="grid">
                  {courses.filter(c => Number(c.teacher_id) === Number(user.id)).map(course => (
                    <div key={`teacher-course-${course.id}`} className="glass-card" style={{ padding: '1rem' }}>
                      <h4 style={{ margin: 0 }}>{course.title}</h4>
                      <p style={{ color: '#64748b', fontSize: '0.9rem' }}>{course.description}</p>
                      <div style={{ display: 'flex', gap: '8px', marginTop: '10px' }}>
                        <button onClick={() => onSelectCourse(course)} style={{ padding: '0.25rem 0.75rem', fontSize: '0.8rem', flex: 1 }}>Manage</button>
                        <button onClick={() => handleDeleteCourse(course.id)} style={{ padding: '0.25rem 0.75rem', fontSize: '0.8rem', background: '#ef4444' }}>🗑️</button>
                      </div>
                    </div>
                  ))}
                  {courses.filter(c => Number(c.teacher_id) === Number(user.id)).length === 0 && (
                    <p style={{ color: '#64748b' }}>You haven't created any courses yet.</p>
                  )}
                </div>
              </section>
            )}

            {/* ENROLLMENTS SECTION */}
            <section className="glass-card">
              <h3 style={{ marginTop: 0 }}>🎓 My Enrolled Courses</h3>
              <div className="grid">
                {enrollments.map(enrollment => (
                  <div key={`enrollment-${enrollment.course_id}`} className="glass-card" style={{ padding: '1rem', borderLeft: '4px solid #10b981' }}>
                    <h4 style={{ margin: 0 }}>{enrollment.course?.title || `Course ${enrollment.course_id}`}</h4>
                    <div style={{ display: 'flex', gap: '8px', marginTop: '10px' }}>
                      <button onClick={() => onSelectCourse(enrollment.course)} style={{ padding: '0.25rem 0.75rem', fontSize: '0.8rem' }}>Enter</button>
                    </div>
                  </div>
                ))}
                {enrollments.length === 0 && <p style={{ color: '#64748b' }}>No enrollments yet.</p>}
              </div>
            </section>
          </>
        )}

        {activeTab === 'explore' && (
          <section className="glass-card">
            <h3 style={{ marginTop: 0 }}>🌍 Discover Courses</h3>
            <div className="grid">
              {courses
                .filter(c => !enrolledIds.includes(c.id) && Number(c.teacher_id) !== Number(user.id))
                .map(course => (
                <div key={`available-course-${course.id}`} className="glass-card" style={{ padding: '1rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                    <h4 style={{ margin: 0 }}>{course.title}</h4>
                    <button onClick={() => handleEnroll(course.id)} style={{ padding: '0.25rem 0.75rem', fontSize: '0.8rem' }}>Enroll Now</button>
                  </div>
                  <p style={{ color: '#64748b', fontSize: '0.9rem', marginTop: '0.5rem' }}>{course.description}</p>
                </div>
              ))}
              {courses.filter(c => !enrolledIds.includes(c.id) && Number(c.teacher_id) !== Number(user.id)).length === 0 && (
                <p style={{ color: '#64748b' }}>No other courses available right now.</p>
              )}
            </div>
          </section>
        )}
      </div>

      {/* CREATE COURSE MODAL (Toast-style) */}
      {isModalOpen && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 1000
        }}>
          <div className="glass-card" style={{ width: '90%', maxWidth: '500px', padding: '2rem', background: 'white' }}>
            <h3 style={{ marginTop: 0 }}>New Course</h3>
            <form onSubmit={handleCreateCourse}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem' }}>Title</label>
                <input 
                  placeholder="Course Title" 
                  value={newCourse.title} 
                  onChange={e => setNewCourse({...newCourse, title: e.target.value})}
                  required 
                />
              </div>
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem' }}>Description</label>
                <textarea 
                  placeholder="What is this course about?" 
                  value={newCourse.description} 
                  onChange={e => setNewCourse({...newCourse, description: e.target.value})}
                  style={{ width: '100%', minHeight: '100px' }}
                />
              </div>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <button type="submit" style={{ flex: 1 }}>Create Course</button>
                <button type="button" onClick={() => setIsModalOpen(false)} style={{ flex: 1, background: '#64748b' }}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
