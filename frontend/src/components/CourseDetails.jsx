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

      // Add Mock data if empty
      if (combined.length === 0) {
        combined = [
          { id: 'm1', type: 'lesson', title: 'Welcome to the Course!', content: 'In this course we will learn about modern web development...' },
          { id: 'm2', type: 'file', file_name: 'Syllabus.pdf', gcs_url: '#' },
          { id: 'm3', type: 'assignment', title: 'Initial Project Setup', due_date: '2026-05-10' }
        ];
      }

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

  return (
    <div>
      <div className="navbar glass-card" style={{ padding: '0.5rem 1.5rem', marginBottom: '2rem' }}>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <button onClick={onBack} style={{ background: '#64748b' }}>← Back</button>
          <h2 style={{ margin: 0 }}>{course.title}</h2>
        </div>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          {!user.is_teacher && !hasAssignments && (
            <button onClick={handleUnenroll} style={{ background: '#ef4444', padding: '0.5rem 1rem', fontSize: '0.8rem' }}>Leave Course</button>
          )}
          <div className="role-badge">Course Feed</div>
        </div>
      </div>

      <div className="grid" style={{ gridTemplateColumns: '1fr 300px', alignItems: 'start' }}>
        
        {/* MAIN FEED */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          {isOwner && (
            <section className="glass-card" style={{ border: '2px dashed #6366f1' }}>
              <h3>➕ Add Content</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <form onSubmit={handleAddTextBlock}>
                  <h4>New Lesson</h4>
                  <input placeholder="Title" value={newTextBlock.title} onChange={e => setNewTextBlock({...newTextBlock, title: e.target.value})} required />
                  <textarea placeholder="Content" value={newTextBlock.content} onChange={e => setNewTextBlock({...newTextBlock, content: e.target.value})} style={{ width: '100%', minHeight: '60px' }} />
                  <button type="submit">Post</button>
                </form>
                <form onSubmit={handleAddAssignment}>
                  <h4>New Assignment</h4>
                  <input placeholder="Task" value={newAssignment.title} onChange={e => setNewAssignment({...newAssignment, title: e.target.value})} required />
                  <input type="date" value={newAssignment.due_date} onChange={e => setNewAssignment({...newAssignment, due_date: e.target.value})} required />
                  <button type="submit">Add</button>
                </form>
              </div>
              <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid #e2e8f0' }}>
                <h4>Upload Resource</h4>
                <input type="file" onChange={handleFileUpload} disabled={uploading} />
              </div>
            </section>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
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
                
                {item.content && <p style={{ margin: 0, whiteSpace: 'pre-wrap', color: '#334155' }}>{item.content}</p>}
                
                {item.type === 'file' && (
                  <a href={item.gcs_url} target="_blank" rel="noreferrer" className="role-badge" style={{ display: 'inline-block', marginTop: '10px', textDecoration: 'none' }}>
                    📥 Download File
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* SIDEBAR */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {isOwner && (
            <section className="glass-card">
              <h3>👥 Students</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {students.map(s => (
                  <div key={s.user_id} style={{ fontSize: '0.9rem', padding: '0.5rem', borderBottom: '1px solid #e2e8f0' }}>
                    {s.user?.first_name} {s.user?.last_name}
                  </div>
                ))}
                {students.length === 0 && <p style={{ fontSize: '0.8rem', color: '#64748b' }}>No students yet.</p>}
              </div>
            </section>
          )}

          <section className="glass-card" style={{ background: 'linear-gradient(135deg, #6366f1, #a855f7)', color: 'white' }}>
            <h3 style={{ margin: 0 }}>Course Info</h3>
            <p style={{ fontSize: '0.9rem', opacity: 0.9 }}>{course.description}</p>
          </section>
        </div>

      </div>
    </div>
  );
};

export default CourseDetails;
