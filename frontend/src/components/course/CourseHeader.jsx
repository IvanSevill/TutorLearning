import { useState } from 'react';
import { API_URL } from '../../constants';

const CourseHeader = ({ course, isOwner, onEditImage }) => {
  const [isDescExpanded, setIsDescExpanded] = useState(false);

  const getImageUrl = (url) => {
    if (!url) return null;
    return url.includes('storage.googleapis.com') 
      ? `${API_URL}/proxy-image?url=${encodeURIComponent(url)}` 
      : url;
  };

  const desc = course.description || '';
  const isLong = desc.length > 150;
  const displayDesc = isLong && !isDescExpanded ? desc.substring(0, 150) + '...' : desc;

  return (
    <div className="glass-card" style={{ marginBottom: '2rem', padding: '2.5rem', position: 'relative', overflow: 'hidden' }}>
      {course.image_url && (
        <div style={{ 
          position: 'absolute', top: 0, right: 0, width: '45%', height: '100%', 
          opacity: 0.15, maskImage: 'linear-gradient(to left, black 40%, transparent)' 
        }}>
          <img src={getImageUrl(course.image_url)} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
        </div>
      )}

      <div style={{ position: 'relative', zIndex: 1, display: 'flex', gap: '2rem', alignItems: 'flex-start' }}>
        <div
          onClick={() => isOwner && onEditImage()}
          style={{
            width: '120px', height: '120px', borderRadius: '16px', overflow: 'hidden', flexShrink: 0,
            background: 'rgba(99,102,241,0.2)', border: '2px solid rgba(255,255,255,0.1)',
            cursor: isOwner ? 'pointer' : 'default', position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
          {course.image_url
            ? <img src={getImageUrl(course.image_url)} alt="cover" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            : <span style={{ fontSize: '3rem' }}>📚</span>
          }
          {isOwner && (
            <div style={{
              position: 'absolute', bottom: 0, left: 0, right: 0,
              background: 'rgba(0,0,0,0.6)', color: 'white', textAlign: 'center',
              fontSize: '0.65rem', fontWeight: 700, padding: '4px', letterSpacing: '0.05em'
            }}>CHANGE</div>
          )}
        </div>

        <div style={{ flex: 1 }}>
          <h1 style={{ fontSize: '2.2rem', margin: '0 0 0.75rem 0', lineHeight: 1.2 }}>{course.title}</h1>
          <p style={{ color: 'var(--text-muted)', lineHeight: '1.6', margin: '0 0 1rem 0' }}>
            {displayDesc}
            {isLong && (
              <span 
                style={{ color: 'var(--primary)', cursor: 'pointer', marginLeft: '8px', fontWeight: 'bold' }} 
                onClick={() => setIsDescExpanded(!isDescExpanded)}
              >
                {isDescExpanded ? 'Show less' : 'Read more'}
              </span>
            )}
          </p>
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            <span className={`badge ${course.is_visible ? 'success' : 'warning'}`}>{course.is_visible ? '🌐 Public' : '🔒 Draft'}</span>
            <span className={`badge ${course.is_enrollable ? 'success' : 'warning'}`}>{course.is_enrollable ? '✅ Enrollable' : '⛔ Closed'}</span>
            {isOwner && <span className="badge" style={{ background: 'rgba(99,102,241,0.15)', color: '#a5b4fc' }}>👑 Your course</span>}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CourseHeader;
