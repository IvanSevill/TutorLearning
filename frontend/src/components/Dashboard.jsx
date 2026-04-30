import { useState, useEffect, useCallback } from 'react';
import { API_URL } from '../App';

const Dashboard = ({ user, onLogout, onSelectCourse }) => {
  const [courses, setCourses] = useState([]);
  const [enrollments, setEnrollments] = useState([]);
  const [newCourse, setNewCourse] = useState({ title: '', description: '' });
  const [activeTab, setActiveTab] = useState('my-courses'); // 'my-courses' or 'explore'

  const fetchData = useCallback(async () => {
    try {
      const [coursesRes, enrollmentsRes] = await Promise.all([
        fetch(`${API_URL}/courses/`),
        fetch(`${API_URL}/enrollments/user/${user.id}`)
      ]);
      setCourses(await coursesRes.json());
      setEnrollments(await enrollmentsRes.json());
    } catch (err) {
      console.error("Failed to fetch dashboard data", err);
    }
  }, [user.id]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleEnroll = async (courseId) => {
    try {
      const response = await fetch(`${API_URL}/enrollments/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: user.id, course_id: courseId })
      });
      if (response.ok) {
        fetchData();
      } else {
        const data = await response.json();
        alert(data.detail || "Enrollment failed");
      }
    } catch (err) {
      console.error("Enroll error:", err);
      alert("Network error during enrollment");
    }
  };

  const handleUnenroll = async (courseId) => {
    if (!window.confirm("Are you sure you want to leave this course?")) return;
    try {
      const response = await fetch(`${API_URL}/enrollments/user/${user.id}/course/${courseId}`, {
        method: 'DELETE'
      });
      if (response.ok) {
        fetchData();
      } else {
        const data = await response.json();
        alert(data.detail || "Unenrollment failed");
      }
    } catch (err) {
      console.error("Unenroll error:", err);
      alert("Network error during unenrollment");
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
        fetchData();
      } else {
        const data = await response.json();
        alert(data.detail || "Creation failed");
      }
    } catch (err) {
      console.error("Create error:", err);
      alert("Network error during course creation");
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
                <h3 style={{ marginTop: 0 }}>👨‍🏫 My Taught Courses</h3>
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
                  <button type="submit" style={{ whiteSpace: 'nowrap' }}>Create New</button>
                </form>
                
                <div className="grid">
                  {courses.filter(c => Number(c.teacher_id) === Number(user.id)).map(course => (
                    <div key={`teacher-course-${course.id}`} className="glass-card" style={{ padding: '1rem' }}>
                      <h4 style={{ margin: 0 }}>{course.title}</h4>
                      <p style={{ color: '#64748b', fontSize: '0.9rem' }}>{course.description}</p>
                      <button onClick={() => onSelectCourse(course)} style={{ padding: '0.25rem 0.75rem', fontSize: '0.8rem', marginTop: '10px' }}>Manage Course</button>
                    </div>
                  ))}
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
                      <button onClick={() => handleUnenroll(enrollment.course_id)} style={{ padding: '0.25rem 0.75rem', fontSize: '0.8rem', background: '#ef4444' }}>Leave</button>
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
              {courses.filter(c => !enrolledIds.includes(c.id) && Number(c.teacher_id) !== Number(user.id)).map(course => (
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
    </div>
  );
};

export default Dashboard;
