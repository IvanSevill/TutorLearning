import { useState, useEffect, useCallback } from 'react';
import { API_URL } from '../App';

const CourseDetails = ({ course, user, onBack }) => {
  const [feed, setFeed] = useState([]);
  const [students, setStudents] = useState([]);
  
  const [newAssignment, setNewAssignment] = useState({ title: '', description: '', due_date: '' });
  const [newTextBlock, setNewTextBlock] = useState({ title: '', content: '' });
  const [uploading, setUploading] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [assRes, txtRes, filRes] = await Promise.all([
        fetch(`${API_URL}/assignments/course/${course.id}`),
        fetch(`${API_URL}/textblocks/course/${course.id}`),
        fetch(`${API_URL}/files/course/${course.id}`)
      ]);
      
      const assignments = (await assRes.json()).map(item => ({ ...item, type: 'assignment' }));
      const textBlocks = (await txtRes.json()).map(item => ({ ...item, type: 'lesson' }));
      const files = (await filRes.json()).map(item => ({ ...item, type: 'file' }));

      // Merge and sort (mocking sorting by ID for now)
      let combined = [...assignments, ...textBlocks, ...files].sort((a, b) => b.id - a.id);

      setFeed(combined);

      if (user.is_teacher && course.teacher_id === user.id) {
        const stdRes = await fetch(`${API_URL}/enrollments/course/${course.id}`);
        setStudents(await stdRes.json());
      }
    } catch (err) {
      console.error("Error fetching details", err);
    }
  }, [course.id, user.id, user.is_teacher, course.teacher_id]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleAddAssignment = async (e) => {
    e.preventDefault();
    const res = await fetch(`${API_URL}/assignments/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...newAssignment, course_id: course.id })
    });
    if (res.ok) {
      setNewAssignment({ title: '', description: '', due_date: '' });
      fetchData();
    }
  };

  const handleAddTextBlock = async (e) => {
    e.preventDefault();
    const res = await fetch(`${API_URL}/textblocks/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...newTextBlock, course_id: course.id })
    });
    if (res.ok) {
      setNewTextBlock({ title: '', content: '' });
      fetchData();
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_URL}/files/course/${course.id}`, {
        method: 'POST',
        body: formData
      });
      if (res.ok) fetchData();
    } catch (err) {
      console.error(err);
      alert("Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const isOwner = user.is_teacher && Number(course.teacher_id) === Number(user.id);
  const hasAssignments = feed.some(item => item.type === 'assignment');

  const handleUnenroll = async () => {
    if (!window.confirm("Are you sure you want to leave this course?")) return;
    try {
      const response = await fetch(`${API_URL}/enrollments/user/${user.id}/course/${course.id}`, {
        method: 'DELETE'
      });
      if (response.ok) {
        onBack();
      } else {
        const data = await response.json();
        alert(data.detail || "Unenrollment failed");
      }
    } catch (err) {
      console.error("Unenroll error:", err);
      alert("Network error during unenrollment");
    }
  };

  const handleImageUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await fetch(`${API_URL}/courses/${course.id}/image`, {
        method: 'PATCH',
        body: formData
      });
      if (response.ok) {
        alert("Image updated!");
        fetchData();
      }
    } catch (err) {
      console.error("Image upload error", err);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div style={{ height: 'calc(100vh - 40px)', display: 'flex', flexDirection: 'column' }}>
      {/* HEADER SECTION */}
      <div className="glass-card" style={{ padding: '1rem 1.5rem', marginBottom: '1rem', flexShrink: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <button onClick={onBack} style={{ background: '#64748b' }}>← Back</button>
            <div>
              <h2 style={{ margin: 0 }}>{course.title}</h2>
              <p style={{ margin: '4px 0 0 0', color: '#64748b', fontSize: '0.9rem' }}>{course.description}</p>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            {isOwner && (
              <label style={{ background: '#6366f1', color: 'white', padding: '0.5rem 1rem', borderRadius: '8px', cursor: 'pointer', fontSize: '0.8rem' }}>
                {uploading ? 'Updating...' : '📸 Change Image'}
                <input type="file" hidden onChange={handleImageUpload} accept="image/*" />
              </label>
            )}
            {!user.is_teacher && !hasAssignments && (
              <button onClick={handleUnenroll} style={{ background: '#ef4444', padding: '0.5rem 1rem', fontSize: '0.8rem' }}>Leave Course</button>
            )}
            <div className="role-badge">Course Feed</div>
          </div>
        </div>
      </div>

      {/* SCROLLABLE CONTENT */}
      <div style={{ flex: 1, overflowY: 'auto', paddingRight: '10px' }}>
        <div className="grid" style={{ gridTemplateColumns: '1fr 300px', alignItems: 'start', gap: '2rem' }}>
          
          {/* MAIN FEED */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            
            {isOwner && (
              <section className="glass-card" style={{ border: '2px dashed #6366f1' }}>
                <h3 style={{ marginTop: 0 }}>➕ Add Content</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <form onSubmit={handleAddTextBlock}>
                    <h4 style={{ marginTop: 0 }}>New Lesson</h4>
                    <input placeholder="Title" value={newTextBlock.title} onChange={e => setNewTextBlock({...newTextBlock, title: e.target.value})} required />
                    <textarea placeholder="Content" value={newTextBlock.content} onChange={e => setNewTextBlock({...newTextBlock, content: e.target.value})} style={{ width: '100%', minHeight: '60px' }} />
                    <button type="submit">Post</button>
                  </form>
                  <form onSubmit={handleAddAssignment}>
                    <h4 style={{ marginTop: 0 }}>New Assignment</h4>
                    <input placeholder="Task" value={newAssignment.title} onChange={e => setNewAssignment({...newAssignment, title: e.target.value})} required />
                    <input type="date" value={newAssignment.due_date} onChange={e => setNewAssignment({...newAssignment, due_date: e.target.value})} required />
                    <button type="submit">Add</button>
                  </form>
                </div>
                <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid #e2e8f0' }}>
                  <h4 style={{ marginTop: 0 }}>Upload Resource</h4>
                  <input type="file" onChange={handleFileUpload} disabled={uploading} />
                </div>
              </section>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {feed.length === 0 && <p className="glass-card" style={{ textAlign: 'center', padding: '2rem', color: '#64748b' }}>No content yet. {isOwner ? 'Start by adding a lesson or file!' : 'The teacher hasn\'t posted anything.'}</p>}
              {feed.map(item => (
                <div key={item.id} className="glass-card" style={{ 
                  padding: '1.5rem', 
                  borderLeft: `6px solid ${item.type === 'lesson' ? '#6366f1' : item.type === 'assignment' ? '#f59e0b' : '#10b981'}`,
                  background: '#fff'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <span style={{ fontSize: '0.7rem', fontWeight: 'bold', textTransform: 'uppercase', color: '#64748b' }}>
                      {item.type}
                    </span>
                    {item.due_date && <span style={{ fontSize: '0.8rem', color: '#f59e0b' }}>Due: {item.due_date}</span>}
                  </div>
                  
                  <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '1.2rem' }}>{item.title || item.file_name}</h4>
                  
                  {item.type === 'lesson' && <p style={{ whiteSpace: 'pre-wrap', color: '#334155' }}>{item.content}</p>}
                  
                  {item.type === 'file' && (
                    <a href={item.gcs_url} target="_blank" rel="noopener noreferrer" className="role-badge" style={{ display: 'inline-block', textDecoration: 'none', background: '#10b981' }}>
                      📥 Download Resource
                    </a>
                  )}

                  {item.type === 'assignment' && !user.is_teacher && (
                    <button style={{ background: '#f59e0b', fontSize: '0.8rem' }}>Submit Work</button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* SIDEBAR: STUDENTS LIST */}
          <aside>
            {user.is_teacher && (
              <div className="glass-card">
                <h3 style={{ marginTop: 0 }}>👥 Enrolled Students</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {students.map(enr => (
                    <div key={enr.user_id} style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '8px', borderBottom: '1px solid #f1f5f9' }}>
                      <div style={{ width: '32px', height: '32px', background: '#e2e8f0', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: '0.8rem' }}>
                        {enr.user?.first_name?.[0]}{enr.user?.last_name?.[0]}
                      </div>
                      <span style={{ fontSize: '0.9rem' }}>{enr.user?.first_name} {enr.user?.last_name}</span>
                    </div>
                  ))}
                  {students.length === 0 && <p style={{ color: '#64748b', fontSize: '0.9rem' }}>No students enrolled.</p>}
                </div>
              </div>
            )}
            
            <div className="glass-card" style={{ marginTop: '1.5rem' }}>
              <h3 style={{ marginTop: 0 }}>ℹ️ Course Info</h3>
              <p style={{ fontSize: '0.9rem', color: '#64748b' }}>
                Course ID: {course.id}<br/>
                Status: {course.is_enrollable ? 'Open' : 'Closed'}<br/>
              </p>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
};

export default CourseDetails;
