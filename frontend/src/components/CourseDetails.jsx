import { useState, useEffect, useCallback } from 'react';
import { API_URL } from '../constants';

const CourseDetails = ({ course: initialCourse, user, onBack }) => {
  const [course, setCourse] = useState(initialCourse);
  const [feed, setFeed] = useState([]);
  const [students, setStudents] = useState([]);
  const [files, setFiles] = useState([]);
  const [activeTab, setActiveTab] = useState('feed');
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState(null);
  
  // Modals state
  const [showEditModal, setShowEditModal] = useState(false);
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [showPostModal, setShowPostModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  
  const [tasks, setTasks] = useState([]);
  
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
  
  // Student task upload state
  const [studentUploads, setStudentUploads] = useState({}); // task.id -> file

  const isOwner = Number(course.teacher_id) === Number(user.id);

  const showNotify = (msg, type = 'success') => {
    setNotification({ msg, type });
    setTimeout(() => setNotification(null), 3000);
  };

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const feedRes = await fetch(`${API_URL}/textblocks/course/${course.id}`);
      if (feedRes.ok) setFeed(await feedRes.json());

      const tasksRes = await fetch(`${API_URL}/assignments/course/${course.id}`);
      if (tasksRes.ok) {
        setTasks(await tasksRes.json());
      }

      const stdRes = await fetch(`${API_URL}/enrollments/course/${course.id}`);
      if (stdRes.ok) setStudents(await stdRes.json());
      
      const filesRes = await fetch(`${API_URL}/files/course/${course.id}`);
      if (filesRes.ok) setFiles(await filesRes.json());
      
    } catch (error) {
      console.error(error);
      showNotify("Error fetching data", "error");
    } finally {
      setLoading(false);
    }
  }, [course.id]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleUpdateCourse = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_URL}/courses/${course.id}?teacher_id=${user.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editForm)
      });
      if (res.ok) {
        const updated = await res.json();
        setCourse(updated);
        setShowEditModal(false);
        showNotify("Course updated");
      }
    } catch (error) {
      console.error(error);
      showNotify("Update failed", "error");
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
        showNotify("Task added successfully");
        fetchData();
      }
    } catch (error) {
      console.error(error);
      showNotify("Failed to add assignment", "error");
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
        showNotify("Post added");
        fetchData();
      }
    } catch (error) {
      console.error(error);
      showNotify("Failed to add post", "error");
    }
  };

  const handleLeave = async () => {
    if (!window.confirm("Are you sure you want to leave this course?")) return;
    try {
      const res = await fetch(`${API_URL}/enrollments/`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: user.id, course_id: course.id })
      });
      if (res.ok) {
        showNotify("Successfully left the course");
        onBack();
      } else {
        const err = await res.json();
        showNotify(err.detail || "Failed to leave course", "error");
      }
    } catch (error) {
      console.error(error);
      showNotify("Error leaving course", "error");
    }
  };
  
  const handleStudentSubmit = async (taskId) => {
    const file = studentUploads[taskId];
    if (!file) return alert("Please select a file to submit");
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      showNotify("Uploading file...", "success");
      
      // Upload file generic endpoint
      const uploadRes = await fetch(`${API_URL}/files/upload`, {
        method: 'POST',
        body: formData
      });
      
      if (!uploadRes.ok) throw new Error("Upload failed");
      const { url } = await uploadRes.json();
      
      // Create submission
      const subRes = await fetch(`${API_URL}/submissions/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: user.id,
          assignment_id: taskId,
          submission_file_url: url
        })
      });
      
      if (subRes.ok) {
        showNotify("Task submitted successfully!");
        setStudentUploads(prev => ({...prev, [taskId]: null}));
      } else {
        throw new Error("Failed to submit task");
      }
    } catch (err) {
      console.error(err);
      showNotify(err.message, "error");
    }
  };
  
  const handleTeacherUploadFile = async (e) => {
    e.preventDefault();
    if (!uploadFile) return;
    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      
      // Create course material record
      const res = await fetch(`${API_URL}/files/course/${course.id}`, {
        method: 'POST',
        body: formData
      });
      
      if (res.ok) {
        setShowUploadModal(false);
        setUploadFile(null);
        showNotify("File uploaded to course");
        // Refresh files
        const fRes = await fetch(`${API_URL}/files/course/${course.id}`);
        if (fRes.ok) setFiles(await fRes.json());
      } else {
        throw new Error("Upload failed");
      }
    } catch (error) {
      console.error(error);
      showNotify("Failed to upload", "error");
    }
  };

  return (
    <div className="container" style={{ maxWidth: '1200px', margin: '0 auto', padding: '2rem' }}>
      {notification && (
        <div className={`toast ${notification.type === 'error' ? 'danger' : ''}`}>
          {notification.type === 'error' ? '❌' : '✅'} {notification.msg}
        </div>
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <button onClick={onBack} className="secondary">← Back to Dashboard</button>
        <div style={{ display: 'flex', gap: '10px' }}>
          {isOwner && (
            <>
              <button className="primary" onClick={() => setShowEditModal(true)}>⚙️ Edit Course</button>
              <button className="primary" onClick={() => setShowTaskModal(true)}>➕ Add Task</button>
              <button className="primary" onClick={() => setShowPostModal(true)}>➕ Add Post</button>
              <button className="primary" onClick={() => setShowUploadModal(true)}>📎 Upload File</button>
            </>
          )}
          {!isOwner && (
            <button className="danger" onClick={handleLeave}>🚪 Leave Course</button>
          )}
        </div>
      </div>

      <div className="glass-card" style={{ marginBottom: '2rem', padding: '3rem', position: 'relative', overflow: 'hidden' }}>
        <div style={{ position: 'relative', zIndex: 1 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <h1 style={{ fontSize: '3rem', margin: '0 0 1rem 0' }}>{course.title}</h1>
              <p style={{ fontSize: '1.2rem', color: 'var(--text-muted)', maxWidth: '800px', lineHeight: '1.6' }}>
                {course.description}
              </p>
            </div>
            <div className="role-badge" style={{ padding: '8px 16px' }}>
              ID: {course.id}
            </div>
          </div>
        </div>
        {course.image_url && (
          <div style={{ position: 'absolute', top: 0, right: 0, width: '40%', height: '100%', opacity: 0.2, maskImage: 'linear-gradient(to left, black, transparent)' }}>
            <img src={course.image_url} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          </div>
        )}
      </div>

      <div className="tabs">
        <div className={`tab ${activeTab === 'feed' ? 'active' : ''}`} onClick={() => setActiveTab('feed')}>📖 Feed</div>
        <div className={`tab ${activeTab === 'students' ? 'active' : ''}`} onClick={() => setActiveTab('students')}>👥 Students ({students.length})</div>
        <div className={`tab ${activeTab === 'tasks' ? 'active' : ''}`} onClick={() => setActiveTab('tasks')}>📝 Tasks</div>
        <div className={`tab ${activeTab === 'files' ? 'active' : ''}`} onClick={() => setActiveTab('files')}>📎 Files ({files.length})</div>
      </div>

      {loading && (
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <div className="spinner">Loading data...</div>
        </div>
      )}

      {!loading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {activeTab === 'feed' && feed.map(post => (
          <div key={post.id} className="glass-card" style={{ animation: 'fadeIn 0.5s ease' }}>
            <h3 style={{ marginTop: 0 }}>{post.title}</h3>
            <p style={{ color: 'var(--text-muted)', whiteSpace: 'pre-wrap' }}>{post.content}</p>
          </div>
        ))}

        {activeTab === 'tasks' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', width: '100%' }}>
            {tasks.length === 0 ? (
              <p style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>No assignments yet.</p>
            ) : (
              tasks.map(task => (
                <div key={task.id} className="glass-card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <h3 style={{ margin: 0 }}>{task.title}</h3>
                    <span className="badge warning">Due: {new Date(task.due_date).toLocaleDateString()}</span>
                  </div>
                  <p style={{ color: 'var(--text-muted)', margin: '1rem 0' }}>{task.description}</p>
                  
                  {!isOwner && (
                    <div style={{ marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid var(--border)' }}>
                      <h4 style={{ margin: '0 0 1rem 0' }}>Submit Work</h4>
                      <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                        <input 
                          type="file" 
                          onChange={(e) => setStudentUploads(prev => ({...prev, [task.id]: e.target.files[0]}))}
                          style={{ flex: 1 }}
                        />
                        <button className="primary" onClick={() => handleStudentSubmit(task.id)}>Submit File</button>
                      </div>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'students' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {students.map(enr => (
              <div key={enr.user_id} className="glass-card" style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1rem 1.5rem' }}>
                <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>
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

        {activeTab === 'files' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', width: '100%' }}>
            {files.length === 0 ? (
              <p style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>No files uploaded yet.</p>
            ) : (
              files.map(f => (
                <div key={f.id} className="glass-card">
                  <h3 style={{ margin: '0 0 1rem 0' }}>{f.file_name}</h3>
                  <div style={{ width: '100%', overflow: 'hidden', borderRadius: '8px', background: '#f8fafc', display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '200px' }}>
                    {f.mime_type?.startsWith('image/') ? (
                      <img src={f.gcs_url} alt={f.file_name} style={{ maxWidth: '100%', maxHeight: '400px', objectFit: 'contain' }} />
                    ) : f.mime_type?.startsWith('video/') ? (
                      <video src={f.gcs_url} controls style={{ maxWidth: '100%', maxHeight: '400px' }} />
                    ) : f.mime_type === 'application/pdf' ? (
                      <iframe src={f.gcs_url} title={f.file_name} width="100%" height="400px" style={{ border: 'none' }} />
                    ) : (
                      <div style={{ padding: '2rem', textAlign: 'center' }}>
                        <p>No preview available</p>
                        <a href={f.gcs_url} target="_blank" rel="noreferrer" className="primary" style={{ display: 'inline-block', padding: '8px 16px', borderRadius: '4px', background: 'var(--primary)', color: 'white', textDecoration: 'none' }}>Download File</a>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    )}

      {/* Edit Course Modal */}
      {showEditModal && (
        <div className="modal-overlay">
          <div className="modal-content glass-card">
            <h2>⚙️ Edit Course</h2>
            <form onSubmit={handleUpdateCourse}>
              <label>Title</label>
              <input value={editForm.title} onChange={e => setEditForm({...editForm, title: e.target.value})} required />
              <label>Description</label>
              <textarea rows="4" value={editForm.description} onChange={e => setEditForm({...editForm, description: e.target.value})} required />
              <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <input type="checkbox" checked={editForm.is_visible} onChange={e => setEditForm({...editForm, is_visible: e.target.checked})} style={{ width: 'auto', margin: 0 }} />
                  Visible
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <input type="checkbox" checked={editForm.is_enrollable} onChange={e => setEditForm({...editForm, is_enrollable: e.target.checked})} style={{ width: 'auto', margin: 0 }} />
                  Enrollable
                </label>
              </div>
              <div style={{ display: 'flex', gap: '10px' }}>
                <button type="submit" className="primary" style={{ flex: 1 }}>Save Changes</button>
                <button type="button" onClick={() => setShowEditModal(false)} style={{ flex: 1 }}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Task Modal */}
      {showTaskModal && (
        <div className="modal-overlay">
          <div className="modal-content glass-card">
            <h2>➕ New Assignment</h2>
            <form onSubmit={handleAddTask}>
              <label>Title</label>
              <input value={taskForm.title} onChange={e => setTaskForm({...taskForm, title: e.target.value})} required />
              <label>Description</label>
              <textarea rows="4" value={taskForm.description} onChange={e => setTaskForm({...taskForm, description: e.target.value})} required />
              <label>Due Date</label>
              <input type="date" value={taskForm.due_date} onChange={e => setTaskForm({...taskForm, due_date: e.target.value})} required />
              <div style={{ display: 'flex', gap: '10px' }}>
                <button type="submit" className="primary" style={{ flex: 1 }}>Create Task</button>
                <button type="button" onClick={() => setShowTaskModal(false)} style={{ flex: 1 }}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Post Modal */}
      {showPostModal && (
        <div className="modal-overlay">
          <div className="modal-content glass-card">
            <h2>📝 Add Feed Post</h2>
            <form onSubmit={handleAddPost}>
              <label>Title</label>
              <input value={postForm.title} onChange={e => setPostForm({...postForm, title: e.target.value})} required />
              <label>Content</label>
              <textarea rows="4" value={postForm.content} onChange={e => setPostForm({...postForm, content: e.target.value})} required />
              <div style={{ display: 'flex', gap: '10px' }}>
                <button type="submit" className="primary" style={{ flex: 1 }}>Post</button>
                <button type="button" onClick={() => setShowPostModal(false)} style={{ flex: 1 }}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Upload File Modal */}
      {showUploadModal && (
        <div className="modal-overlay">
          <div className="modal-content glass-card">
            <h2>📎 Upload Course Material</h2>
            <form onSubmit={handleTeacherUploadFile}>
              <label>Select File</label>
              <input type="file" onChange={e => setUploadFile(e.target.files[0])} required />
              <div style={{ display: 'flex', gap: '10px', marginTop: '1.5rem' }}>
                <button type="submit" className="primary" style={{ flex: 1 }}>Upload File</button>
                <button type="button" onClick={() => setShowUploadModal(false)} style={{ flex: 1 }}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default CourseDetails;
