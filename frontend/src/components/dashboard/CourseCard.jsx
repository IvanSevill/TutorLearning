import { API_URL } from '../../constants';

const CourseCard = ({ course, user, activeTab, onSelect, onEnroll, onUnenroll }) => {
  const getImageUrl = (url) => {
    if (!url) return null;
    return url.includes('storage.googleapis.com') 
      ? `${API_URL}/proxy-image?url=${encodeURIComponent(url)}` 
      : url;
  };

  const isTeacherOfCourse = Number(course.teacher_id) === Number(user.id);

  return (
    <div className="glass-card" style={{ display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
      <div style={{ 
        width: '90px', height: '90px', borderRadius: '14px', overflow: 'hidden', flexShrink: 0,
        background: 'rgba(99,102,241,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' 
      }}>
        {course.image_url
          ? <img src={getImageUrl(course.image_url)} alt={course.title} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
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
          {course.description && course.description.length > 100 
            ? course.description.substring(0, 100) + '...' 
            : course.description}
        </p>
        {course.teacher && (
          <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', margin: 0 }}>
            👤 <strong>{course.teacher.first_name} {course.teacher.last_name}</strong>
          </p>
        )}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', minWidth: '130px' }}>
        <button className="primary" onClick={() => onSelect(course)}>Open →</button>
        {activeTab === 'all' && !isTeacherOfCourse && (
          <button onClick={() => onEnroll(course.id)}>Enroll</button>
        )}
        {activeTab === 'my' && (
          <button className="danger" onClick={() => onUnenroll(course.id)}>Leave</button>
        )}
      </div>
    </div>
  );
};

export default CourseCard;
