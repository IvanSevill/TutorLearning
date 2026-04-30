import { useState, useEffect, useCallback } from 'react';
import { API_URL } from '../constants';

// Helper to format timestamps
const formatDate = (dateStr) => {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return d.toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
};

// Helper to detect file type from mime_type or filename
const getFileType = (f) => {
  const mime = f.mime_type || '';
  const name = (f.file_name || '').toLowerCase();
  if (mime.startsWith('image/') || /\.(jpg|jpeg|png|gif|webp|svg)$/.test(name)) return 'image';
  if (mime.startsWith('video/') || /\.(mp4|webm|ogg|mov)$/.test(name)) return 'video';
  if (mime === 'application/pdf' || name.endsWith('.pdf')) return 'pdf';
  return 'other';
};

// MediaPreview: proxies through backend redirect to avoid CORS on direct GCS URLs
const MediaPreview = ({ file }) => {
  const [failed, setFailed] = useState(false);
  const proxyUrl = `${API_URL}/files/${file.id}`;
  const type = getFileType(file);

  if (failed || type === 'other') {
    return (
      <div style={{ padding: '1.5rem', textAlign: 'center' }}>
        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📄</div>
        <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>{file.file_name}</p>
        <a href={proxyUrl} target="_blank" rel="noreferrer"
          style={{ display: 'inline-block', padding: '8px 20px', borderRadius: '10px', background: 'var(--primary)', color: 'white', textDecoration: 'none', fontWeight: 600 }}>
          ⬇ Download
        </a>
      </div>
    );
  }

  if (type === 'image') {
    return (
      <img
        src={proxyUrl}
        alt={file.file_name}
        onError={() => setFailed(true)}
        style={{ maxWidth: '100%', maxHeight: '420px', objectFit: 'contain', borderRadius: '8px', display: 'block', margin: '0 auto' }}
      />
    );
  }

  if (type === 'video') {
    return (
      <video controls onError={() => setFailed(true)}
        style={{ maxWidth: '100%', maxHeight: '420px', borderRadius: '8px', display: 'block', margin: '0 auto' }}>
        <source src={proxyUrl} />
        Your browser does not support video.
      </video>
    );
  }

  if (type === 'pdf') {
    return (
      <iframe src={proxyUrl} title={file.file_name} width="100%" height="420px"
        style={{ border: 'none', borderRadius: '8px' }} onError={() => setFailed(true)} />
    );
  }

  return null;
};

const CourseDetails = ({ course: initialCourse, user, onBack }) => {
  const [course, setCourse] = useState(initialCourse);
  const [feed, setFeed] = useState([]);
  const [students, setStudents] = useState([]);
  const [files, setFiles] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [activeTab, setActiveTab] = useState('feed');
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState(null);

  // Modals state
  const [showEditModal, setShowEditModal] = useState(false);
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [showPostModal, setShowPostModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showImageModal, setShowImageModal] = useState(false);

  // Form states
  const [editForm, setEditForm] = useState({
    title: course.title,
    description: course.description,
    is_visible: course.is_visible,
    is_enrollable: course.is_enrollable
  });
  const [taskForm, setTaskForm] = useState({ title: '', description: '', due_date: '' });
  const [postForm, setPostForm] = useState({ title: '', content: '' });
  const [uploadFile, setUploadFile] = useState(null);
  const [coverImageFile, setCoverImageFile] = useState(null);

  // Student task upload state
  const [studentUploads, setStudentUploads] = useState({});

  const isOwner = Number(course.teacher_id) === Number(user.id);

  const showNotify = (msg, type = 'success') => {
    setNotification({ msg, type });
    setTimeout(() => setNotification(null), 3500);
  };

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [feedRes, tasksRes, stdRes, filesRes] = await Promise.all([
        fetch(`${API_URL}/textblocks/course/${course.id}`),
        fetch(`${API_URL}/assignments/course/${course.id}`),
        fetch(`${API_URL}/enrollments/course/${course.id}`),
        fetch(`${API_URL}/files/course/${course.id}`)
      ]);
      if (feedRes.ok) setFeed(await feedRes.json());
      if (tasksRes.ok) setTasks(await tasksRes.json());
      if (stdRes.ok) setStudents(await stdRes.json());
      if (filesRes.ok) setFiles(await filesRes.json());
    } catch (error) {
      console.error(error);
      showNotify('Error fetching data', 'error');
    } finally {
      setLoading(false);
    }
  }, [course.id]);

  useEffect(() => { fetchData(); }, [fetchData]);

  // Build unified sorted feed
  const unifiedFeed = [
    ...feed.map(p => ({ ...p, _type: 'post', _date: p.created_at })),
    ...tasks.map(t => ({ ...t, _type: 'task', _date: t.created_at })),
    ...files.map(f => ({ ...f, _type: 'file', _date: f.upload_date })),
  ].sort((a, b) => new Date(a._date || 0) - new Date(b._date || 0));

  const handleUpdateCourse = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_URL}/courses/${course.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editForm)
      });
      if (res.ok) {
        const updated = await res.json();
        setCourse(updated);
        setShowEditModal(false);
        showNotify('Course updated');
      }
    } catch (error) {
      showNotify('Update failed', 'error');
    }
  };

  const handleChangeCoverImage = async (e) => {
    e.preventDefault();
    if (!coverImageFile) return;
    try {
      const formData = new FormData();
      formData.append('file', coverImageFile);
      const res = await fetch(`${API_URL}/courses/${course.id}/image`, {
        method: 'PATCH',
        body: formData
      });
      if (res.ok) {
        const data = await res.json();
        setCourse(prev => ({ ...prev, image_url: data.image_url }));
        setShowImageModal(false);
        setCoverImageFile(null);
        showNotify('Cover image updated');
      } else {
        throw new Error('Upload failed');
      }
    } catch (err) {
      showNotify('Failed to update image', 'error');
    }
  };

  const handleAddTask = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_URL}/assignments/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...taskForm, course_id: course.id })
      });
      if (res.ok) {
        setShowTaskModal(false);
        setTaskForm({ title: '', description: '', due_date: '' });
        showNotify('Task added successfully');
        fetchData();
      }
    } catch (error) {
      showNotify('Failed to add assignment', 'error');
    }
  };

  const handleAddPost = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_URL}/textblocks/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...postForm, course_id: course.id })
      });
      if (res.ok) {
        setShowPostModal(false);
        setPostForm({ title: '', content: '' });
        showNotify('Post added');
        fetchData();
      }
    } catch (error) {
      showNotify('Failed to add post', 'error');
    }
  };

  const handleLeave = async () => {
    if (!window.confirm('Are you sure you want to leave this course?')) return;
    try {
      const res = await fetch(`${API_URL}/enrollments/`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: user.id, course_id: course.id })
      });
      if (res.ok) {
        showNotify('Successfully left the course');
        onBack();
      } else {
        const err = await res.json();
        showNotify(err.detail || 'Failed to leave course', 'error');
      }
    } catch (error) {
      showNotify('Error leaving course', 'error');
    }
  };

  const handleStudentSubmit = async (taskId) => {
    const file = studentUploads[taskId];
    if (!file) return alert('Please select a file to submit');
    try {
      const formData = new FormData();
      formData.append('file', file);
      showNotify('Uploading file...', 'success');
      const uploadRes = await fetch(`${API_URL}/files/upload`, { method: 'POST', body: formData });
      if (!uploadRes.ok) throw new Error('Upload failed');
      const { url } = await uploadRes.json();
      const subRes = await fetch(`${API_URL}/submissions/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: user.id, assignment_id: taskId, submission_file_url: url })
      });
      if (subRes.ok) {
        showNotify('Task submitted successfully!');
        setStudentUploads(prev => ({ ...prev, [taskId]: null }));
      } else {
        throw new Error('Failed to submit task');
      }
    } catch (err) {
      showNotify(err.message, 'error');
    }
  };

  const handleTeacherUploadFile = async (e) => {
    e.preventDefault();
    if (!uploadFile) return;
    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      const res = await fetch(`${API_URL}/files/course/${course.id}`, { method: 'POST', body: formData });
      if (res.ok) {
        setShowUploadModal(false);
        setUploadFile(null);
        showNotify('File uploaded to course');
        fetchData();
      } else {
        throw new Error('Upload failed');
      }
    } catch (error) {
      showNotify('Failed to upload', 'error');
    }
  };

  return (
    <div className="container" style={{ maxWidth: '900px', margin: '0 auto', padding: '2rem' }}>
      {notification && (
        <div className={`toast ${notification.type === 'error' ? 'danger' : ''}`}>
          {notification.type === 'error' ? '❌' : '✅'} {notification.msg}
        </div>
      )}

      {/* Top bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <button onClick={onBack} className="secondary">← Back</button>
        <div style={{ display: 'flex', gap: '10px' }}>
          {isOwner && (
            <>
              <button className="primary" onClick={() => setShowEditModal(true)}>⚙️ Edit</button>
              <button className="primary" onClick={() => setShowTaskModal(true)}>➕ Task</button>
              <button className="primary" onClick={() => setShowPostModal(true)}>📢 Post</button>
              <button className="primary" onClick={() => setShowUploadModal(true)}>📎 File</button>
            </>
          )}
          {!isOwner && (
            <button className="danger" onClick={handleLeave}>🚪 Leave</button>
          )}
        </div>
      </div>

      {/* Course header card */}
      <div className="glass-card" style={{ marginBottom: '2rem', padding: '2.5rem', position: 'relative', overflow: 'hidden' }}>
        {/* Background image overlay */}
        {course.image_url && (
          <div style={{ position: 'absolute', top: 0, right: 0, width: '45%', height: '100%', opacity: 0.15, maskImage: 'linear-gradient(to left, black 40%, transparent)' }}>
            <img src={course.image_url} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          </div>
        )}

        <div style={{ position: 'relative', zIndex: 1, display: 'flex', gap: '2rem', alignItems: 'flex-start' }}>
          {/* Clickable thumbnail */}
          <div
            onClick={() => isOwner && setShowImageModal(true)}
            style={{
              width: '120px', height: '120px', borderRadius: '16px', overflow: 'hidden', flexShrink: 0,
              background: 'rgba(99,102,241,0.2)', border: '2px solid rgba(255,255,255,0.1)',
              cursor: isOwner ? 'pointer' : 'default', position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}>
            {course.image_url
              ? <img src={course.image_url} alt="cover" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
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
            <p style={{ color: 'var(--text-muted)', lineHeight: '1.6', margin: '0 0 1rem 0' }}>{course.description}</p>
            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
              <span className={`badge ${course.is_visible ? 'success' : 'warning'}`}>{course.is_visible ? '🌐 Public' : '🔒 Draft'}</span>
              <span className={`badge ${course.is_enrollable ? 'success' : 'warning'}`}>{course.is_enrollable ? '✅ Enrollable' : '⛔ Closed'}</span>
              {isOwner && <span className="badge" style={{ background: 'rgba(99,102,241,0.15)', color: '#a5b4fc' }}>👑 Your course</span>}
            </div>
          </div>
        </div>
      </div>

      {/* Tabs — only Feed and Students */}
      <div className="tabs" style={{ marginBottom: '2rem' }}>
        <div className={`tab ${activeTab === 'feed' ? 'active' : ''}`} onClick={() => setActiveTab('feed')}>📖 Feed</div>
        <div className={`tab ${activeTab === 'students' ? 'active' : ''}`} onClick={() => setActiveTab('students')}>👥 Students ({students.length})</div>
      </div>

      {loading && (
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <div className="spinner" />
        </div>
      )}

      {!loading && activeTab === 'feed' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {unifiedFeed.length === 0 && (
            <div className="glass-card" style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-muted)' }}>
              No activity yet in this course.
            </div>
          )}

          {unifiedFeed.map((item) => {
            if (item._type === 'post') {
              return (
                <div key={`post-${item.id}`} className="glass-card" style={{ animation: 'fadeIn 0.4s ease' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <span className="badge" style={{ background: 'rgba(99,102,241,0.15)', color: '#a5b4fc' }}>📢 Announcement</span>
                    {item._date && <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{formatDate(item._date)}</span>}
                  </div>
                  <h3 style={{ margin: '0 0 0.5rem 0' }}>{item.title}</h3>
                  <p style={{ color: 'var(--text-muted)', whiteSpace: 'pre-wrap', margin: 0 }}>{item.content}</p>
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
                  <p style={{ color: 'var(--text-muted)', margin: '0.5rem 0 0 0' }}>{item.description}</p>

                  {!isOwner && (
                    <div style={{ marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid var(--border-glass)' }}>
                      <h4 style={{ margin: '0 0 0.75rem 0', fontSize: '0.9rem' }}>Submit your work</h4>
                      <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                        <input type="file" style={{ flex: 1, marginBottom: 0 }}
                          onChange={(e) => setStudentUploads(prev => ({ ...prev, [item.id]: e.target.files[0] }))} />
                        <button className="primary" onClick={() => handleStudentSubmit(item.id)}>Submit</button>
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
                </div>
              );
            }

            return null;
          })}
        </div>
      )}

      {!loading && activeTab === 'students' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {students.length === 0 && (
            <div className="glass-card" style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
              No students enrolled yet.
            </div>
          )}
          {students.map(enr => (
            <div key={enr.user_id} className="glass-card" style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1rem 1.5rem' }}>
              <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: 'linear-gradient(135deg, var(--primary), var(--secondary))', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: '1.1rem', flexShrink: 0 }}>
                {enr.user?.first_name?.[0]}{enr.user?.last_name?.[0]}
              </div>
              <div>
                <div style={{ fontWeight: '600' }}>{enr.user?.first_name} {enr.user?.last_name}</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{enr.user?.email}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ======= MODALS ======= */}

      {showImageModal && (
        <div className="modal-overlay">
          <div className="modal-content glass-card">
            <h2>🖼️ Change Cover Image</h2>
            {course.image_url && (
              <img src={course.image_url} alt="current cover"
                style={{ width: '100%', height: '180px', objectFit: 'cover', borderRadius: '12px', marginBottom: '1.5rem' }} />
            )}
            <form onSubmit={handleChangeCoverImage}>
              <label>Select new image</label>
              <input type="file" accept="image/*" onChange={e => setCoverImageFile(e.target.files[0])} required />
              <div style={{ display: 'flex', gap: '10px', marginTop: '0.5rem' }}>
                <button type="submit" className="primary" style={{ flex: 1 }}>Upload</button>
                <button type="button" onClick={() => { setShowImageModal(false); setCoverImageFile(null); }} style={{ flex: 1 }}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showEditModal && (
        <div className="modal-overlay">
          <div className="modal-content glass-card">
            <h2>⚙️ Edit Course</h2>
            <form onSubmit={handleUpdateCourse}>
              <label>Title</label>
              <input value={editForm.title} onChange={e => setEditForm({ ...editForm, title: e.target.value })} required />
              <label>Description</label>
              <textarea rows="4" value={editForm.description} onChange={e => setEditForm({ ...editForm, description: e.target.value })} required />
              <div style={{ display: 'flex', gap: '1.5rem', marginBottom: '1.5rem' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: 0 }}>
                  <input type="checkbox" checked={editForm.is_visible} onChange={e => setEditForm({ ...editForm, is_visible: e.target.checked })} style={{ width: 'auto', margin: 0 }} />
                  Visible
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: 0 }}>
                  <input type="checkbox" checked={editForm.is_enrollable} onChange={e => setEditForm({ ...editForm, is_enrollable: e.target.checked })} style={{ width: 'auto', margin: 0 }} />
                  Enrollable
                </label>
              </div>
              <div style={{ display: 'flex', gap: '10px' }}>
                <button type="submit" className="primary" style={{ flex: 1 }}>Save</button>
                <button type="button" onClick={() => setShowEditModal(false)} style={{ flex: 1 }}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showTaskModal && (
        <div className="modal-overlay">
          <div className="modal-content glass-card">
            <h2>➕ New Task</h2>
            <form onSubmit={handleAddTask}>
              <label>Title</label>
              <input value={taskForm.title} onChange={e => setTaskForm({ ...taskForm, title: e.target.value })} required />
              <label>Description</label>
              <textarea rows="4" value={taskForm.description} onChange={e => setTaskForm({ ...taskForm, description: e.target.value })} required />
              <label>Due Date</label>
              <input type="date" value={taskForm.due_date} onChange={e => setTaskForm({ ...taskForm, due_date: e.target.value })} required />
              <div style={{ display: 'flex', gap: '10px' }}>
                <button type="submit" className="primary" style={{ flex: 1 }}>Create</button>
                <button type="button" onClick={() => setShowTaskModal(false)} style={{ flex: 1 }}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showPostModal && (
        <div className="modal-overlay">
          <div className="modal-content glass-card">
            <h2>📢 New Announcement</h2>
            <form onSubmit={handleAddPost}>
              <label>Title</label>
              <input value={postForm.title} onChange={e => setPostForm({ ...postForm, title: e.target.value })} required />
              <label>Content</label>
              <textarea rows="5" value={postForm.content} onChange={e => setPostForm({ ...postForm, content: e.target.value })} required />
              <div style={{ display: 'flex', gap: '10px' }}>
                <button type="submit" className="primary" style={{ flex: 1 }}>Post</button>
                <button type="button" onClick={() => setShowPostModal(false)} style={{ flex: 1 }}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showUploadModal && (
        <div className="modal-overlay">
          <div className="modal-content glass-card">
            <h2>📎 Upload Course Material</h2>
            <form onSubmit={handleTeacherUploadFile}>
              <label>Select File</label>
              <input type="file" onChange={e => setUploadFile(e.target.files[0])} required />
              <div style={{ display: 'flex', gap: '10px', marginTop: '0.5rem' }}>
                <button type="submit" className="primary" style={{ flex: 1 }}>Upload</button>
                <button type="button" onClick={() => { setShowUploadModal(false); setUploadFile(null); }} style={{ flex: 1 }}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default CourseDetails;
