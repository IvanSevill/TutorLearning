import { useState, useEffect, useCallback } from 'react';
import { courseService, enrollmentService } from '../api';
import { useNotification } from '../hooks/useNotification';
import DashboardNav from './dashboard/DashboardNav';
import CourseCard from './dashboard/CourseCard';
import Modal from './common/Modal';

const Dashboard = ({ user, onLogout, onSelectCourse }) => {
  const [courses, setCourses] = useState([]);
  const [activeTab, setActiveTab] = useState('my');
  const [loading, setLoading] = useState(false);
  const { showNotify } = useNotification();
  
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newCourse, setNewCourse] = useState({ title: '', description: '' });

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      let data;
      if (activeTab === 'my') {
        const enrollments = await courseService.getMyEnrollments(user.id);
        data = enrollments.map(enr => enr.course);
      } else if (activeTab === 'teaching') {
        data = await courseService.getTeaching(user.id);
      } else {
        data = await courseService.getAllAvailable(user.id);
      }
      setCourses(data);
    } catch {
      showNotify("Failed to fetch courses", "error");
    } finally {
      setLoading(false);
    }
  }, [user.id, activeTab, showNotify]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleEnroll = async (courseId) => {
    try {
      await enrollmentService.enroll({ user_id: user.id, course_id: courseId });
      showNotify("Successfully enrolled!");
      fetchData();
    } catch (err) {
      showNotify(err.message, "error");
    }
  };

  const handleUnenroll = async (courseId) => {
    if (!window.confirm("Are you sure you want to unenroll?")) return;
    try {
      await enrollmentService.leave({ user_id: user.id, course_id: courseId });
      showNotify("Successfully unenrolled");
      fetchData();
    } catch (err) {
      showNotify(err.message, "error");
    }
  };

  const handleCreateCourse = async (e) => {
    e.preventDefault();
    try {
      await courseService.create({
        ...newCourse,
        is_visible: false,
        is_enrollable: true,
        teacher_id: user.id
      });
      showNotify("Course created successfully!");
      setShowCreateModal(false);
      setNewCourse({ title: '', description: '' });
      fetchData();
    } catch (err) {
      showNotify(err.message, "error");
    }
  };

  return (
    <div className="container" style={{ maxWidth: '1400px', margin: '0 auto', padding: '2rem' }}>
      <DashboardNav user={user} onLogout={onLogout} />

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
        <div style={{ textAlign: 'center', padding: '5rem' }}><div className="spinner" /></div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {activeTab === 'teaching' && user.is_teacher && (
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
              <button className="primary" onClick={() => setShowCreateModal(true)}>+ Create New Class</button>
            </div>
          )}
          
          {courses.length === 0 ? (
            <div className="glass-card" style={{ textAlign: 'center', padding: '4rem' }}>
              <p style={{ fontSize: '1.2rem', color: 'var(--text-muted)' }}>No courses found in this category.</p>
            </div>
          ) : (
            courses.map(course => (
              <CourseCard 
                key={course.id} 
                course={course} 
                user={user} 
                activeTab={activeTab}
                onSelect={onSelectCourse}
                onEnroll={handleEnroll}
                onUnenroll={handleUnenroll}
              />
            ))
          )}
        </div>
      )}

      <Modal isOpen={showCreateModal} onClose={() => setShowCreateModal(false)} title="Create New Class">
        <form onSubmit={handleCreateCourse} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label>Course Title</label>
            <input 
              type="text" 
              value={newCourse.title} 
              onChange={e => setNewCourse({ ...newCourse, title: e.target.value })} 
              required 
            />
          </div>
          <div>
            <label>Description</label>
            <textarea 
              value={newCourse.description} 
              onChange={e => setNewCourse({ ...newCourse, description: e.target.value })} 
              rows={4}
              required 
              style={{ resize: 'vertical' }}
            />
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1rem' }}>
            <button type="button" onClick={() => setShowCreateModal(false)}>Cancel</button>
            <button type="submit" className="primary">Create Course</button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default Dashboard;
