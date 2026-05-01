import { useState } from 'react';
import MediaPreview from './MediaPreview';
import { formatDate } from '../../utils';

const CourseFeed = ({ items, isOwner, onDeletePost, onDeleteTask, onDeleteFile, onEditTask, onStudentSubmit }) => {
  const [studentUploads, setStudentUploads] = useState({});

  if (items.length === 0) {
    return (
      <div className="glass-card" style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-muted)' }}>
        No activity yet in this course.
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {items.map((item) => {
        if (item._type === 'post') {
          return (
            <div key={`post-${item.id}`} className="glass-card" style={{ animation: 'fadeIn 0.4s ease' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <span className="badge" style={{ background: 'rgba(99,102,241,0.15)', color: '#a5b4fc' }}>📢 Announcement</span>
                {item._date && <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{formatDate(item._date)}</span>}
              </div>
              <h3 style={{ margin: '0 0 0.5rem 0' }}>{item.title}</h3>
              <p style={{ color: 'var(--text-muted)', whiteSpace: 'pre-wrap', margin: 0 }}>{item.content}</p>
              {isOwner && (
                <div style={{ marginTop: '1rem', textAlign: 'right' }}>
                  <button className="danger" style={{ padding: '6px 16px', fontSize: '0.8rem' }} onClick={() => onDeletePost(item.id)}>🗑️ Delete</button>
                </div>
              )}
            </div>
          );
        }

        if (item._type === 'task') {
          return (
            <div key={`task-${item.id}`} className="glass-card" style={{ animation: 'fadeIn 0.4s ease' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <span className="badge warning">📝 Task</span>
                {item._date && <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{formatDate(item._date)}</span>}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <h3 style={{ margin: '0 0 0.5rem 0' }}>{item.title}</h3>
                {item.due_date && (
                  <span className="badge warning" style={{ flexShrink: 0, marginLeft: '1rem' }}>
                    Due: {new Date(item.due_date).toLocaleDateString()}
                  </span>
                )}
              </div>
              <p style={{ color: 'var(--text-muted)', margin: '0.5rem 0 0 0', whiteSpace: 'pre-wrap' }}>{item.description}</p>

              {isOwner && (
                <div style={{ marginTop: '1rem', textAlign: 'right', display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                  <button className="secondary" onClick={() => onEditTask(item)}>✏️ Edit Task</button>
                  <button className="danger" style={{ padding: '6px 16px', fontSize: '0.8rem' }} onClick={() => onDeleteTask(item.id)}>🗑️ Delete</button>
                </div>
              )}

              {!isOwner && (
                <div style={{ marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid var(--border-glass)' }}>
                  <h4 style={{ margin: '0 0 0.75rem 0', fontSize: '0.9rem' }}>Submit your work</h4>
                  <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                    <input type="file" style={{ flex: 1, marginBottom: 0 }}
                      onChange={(e) => setStudentUploads(prev => ({ ...prev, [item.id]: e.target.files[0] }))} />
                    <button className="primary" onClick={() => onStudentSubmit(item.id, studentUploads[item.id])}>Submit</button>
                  </div>
                </div>
              )}
            </div>
          );
        }

        if (item._type === 'file') {
          return (
            <div key={`file-${item.id}`} className="glass-card" style={{ animation: 'fadeIn 0.4s ease' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <span className="badge" style={{ background: 'rgba(16,185,129,0.15)', color: '#6ee7b7' }}>📎 Material</span>
                {item._date && <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{formatDate(item._date)}</span>}
              </div>
              <h3 style={{ margin: '0 0 1rem 0' }}>{item.file_name}</h3>
              <div style={{ borderRadius: '12px', overflow: 'hidden', background: 'rgba(0,0,0,0.2)', minHeight: '80px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <MediaPreview file={item} />
              </div>
              {isOwner && (
                <div style={{ marginTop: '1rem', textAlign: 'right' }}>
                  <button className="danger" style={{ padding: '6px 16px', fontSize: '0.8rem' }} onClick={() => onDeleteFile(item.id)}>🗑️ Delete</button>
                </div>
              )}
            </div>
          );
        }

        return null;
      })}
    </div>
  );
};

export default CourseFeed;
