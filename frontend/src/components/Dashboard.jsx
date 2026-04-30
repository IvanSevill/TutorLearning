import { useState, useEffect, useCallback } from 'react';
import { API_URL } from '../constants';

const Dashboard = ({ user, onLogout, onSelectCourse }) => {
  const [courses, setCourses] = useState([]);
  const [activeTab, setActiveTab] = useState('my');
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState(null);

  const showNotify = (msg, type = 'success') => {
    setNotification({ msg, type });
    setTimeout(() => setNotification(null), 3000);
  };

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      let url = `${API_URL}/courses/available/${user.id}`;
      if (activeTab === 'my') {
        url = `${API_URL}/enrollments/user/${user.id}`;
      } else if (activeTab === 'teaching') {
        url = `${API_URL}/courses/teacher/${user.id}`;
      }
      
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        // If it's the enrollment list, extract courses
        if (activeTab === 'my') {
          setCourses(data.map(enr => enr.course));
        } else {
          setCourses(data);
        }
      }
    } catch (err) {
      console.error(err);
      showNotify("Failed to fetch courses", "error");
    } finally {
      setLoading(false);
    }
  }, [user.id, activeTab]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleEnroll = async (courseId) => {
    try {
      const res = await fetch(`${API_URL}/enrollments/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: user.id, course_id: courseId })
      });
      if (res.ok) {
        showNotify("Successfully enrolled!");
        fetchData();
      } else {
        const err = await res.json();
        showNotify(err.detail || "Enrollment failed", "error");
      }
    } catch (err) {
      showNotify("Error enrolling", "error");
    }
  };

  const handleUnenroll = async (courseId) => {
    if (!window.confirm("Are you sure you want to unenroll?")) return;
    try {
      const res = await fetch(`${API_URL}/enrollments/`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: user.id, course_id: courseId })
      });
      if (res.ok) {
        showNotify("Successfully unenrolled");
        fetchData();
      } else {
        showNotify("Failed to unenroll", "error");
      }
    } catch (err) {
      showNotify("Error unenrolling", "error");
    }
  };

  return (
    <div className="container" style={{ maxWidth: '1400px', margin: '0 auto', padding: '2rem' }}>
      {notification && (
        <div className={`toast ${notification.type === 'error' ? 'danger' : ''}`}>
          {notification.type === 'error' ? '❌' : '✅'} {notification.msg}
        </div>
      )}

      <nav className="glass-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '3rem', padding: '1rem 2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ fontSize: '1.5rem', fontWeight: '800', background: 'linear-gradient(135deg, #6366f1, #ec4899)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            TutorLearning
          </div>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontWeight: '700' }}>{user.first_name} {user.last_name}</div>
            <div className="role-badge" style={{ fontSize: '0.65rem' }}>{user.is_teacher ? 'TEACHER' : 'STUDENT'}</div>
          </div>
          <button className="danger" onClick={onLogout}>Logout</button>
        </div>
      </nav>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '2rem' }}>
        <div>
          <h2 style={{ fontSize: '2.5rem', margin: 0 }}>Courses</h2>
          <p style={{ color: 'var(--text-muted)' }}>Explore and manage your academic journey.</p>
        </div>
        <div className="tabs">
          <div className={`tab ${activeTab === 'all' ? 'active' : ''}`} onClick={() => setActiveTab('all')}>🌐 Discover</div>
          <div className={`tab ${activeTab === 'my' ? 'active' : ''}`} onClick={() => setActiveTab('my')}>📚 Learning</div>
          {user.is_teacher && (
            <div className={`tab ${activeTab === 'teaching' ? 'active' : ''}`} onClick={() => setActiveTab('teaching')}>🎓 Teaching</div>
          )}
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '5rem' }}>
          <div className="spinner">Loading courses...</div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {courses.length === 0 && (
            <div className="glass-card" style={{ textAlign: 'center', padding: '4rem' }}>
              <p style={{ fontSize: '1.2rem', color: 'var(--text-muted)' }}>No courses found in this category.</p>
            </div>
          )}
          {courses.map(course => (
            <div key={course.id} className="glass-card" style={{ display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
              {/* Course thumbnail */}
              <div style={{ width: '90px', height: '90px', borderRadius: '14px', overflow: 'hidden', flexShrink: 0,
                background: 'rgba(99,102,241,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {course.image_url
                  ? <img src={course.image_url} alt={course.title} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                  : <span style={{ fontSize: '2.5rem' }}>📚</span>
                }
              </div>

              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                  <h3 style={{ margin: 0, fontSize: '1.3rem' }}>{course.title}</h3>
                  <span className={`badge ${course.is_visible ? 'success' : 'warning'}`}>
                    {course.is_visible ? 'Public' : 'Draft'}
                  </span>
                </div>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', lineHeight: '1.5', margin: '0 0 0.5rem 0' }}>
                  {course.description}
                </p>
                {course.teacher && (
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', margin: 0 }}>
                    👤 <strong>{course.teacher.first_name} {course.teacher.last_name}</strong>
                  </p>
                )}
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', minWidth: '130px' }}>
                <button className="primary" onClick={() => onSelectCourse(course)}>Open →</button>
                {activeTab === 'all' && Number(course.teacher_id) !== Number(user.id) && (
                  <button onClick={() => handleEnroll(course.id)}>Enroll</button>
                )}
                {activeTab === 'my' && (
                  <button className="danger" onClick={() => handleUnenroll(course.id)}>Leave</button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Dashboard;
