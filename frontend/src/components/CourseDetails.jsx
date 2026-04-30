import { useState, useEffect, useCallback } from 'react';
import { API_URL } from '../App';

const CourseDetails = ({ course, user, onBack }) => {
  const [assignments, setAssignments] = useState([]);
  const [textBlocks, setTextBlocks] = useState([]);
  const [files, setFiles] = useState([]);
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
      setAssignments(await assRes.json());
      setTextBlocks(await txtRes.json());
      setFiles(await filRes.json());

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

  const isOwner = user.is_teacher && course.teacher_id === user.id;

  return (
    <div>
      <div className="navbar glass-card" style={{ padding: '0.5rem 1.5rem', marginBottom: '2rem' }}>
        <button onClick={onBack} style={{ background: '#64748b' }}>← Back</button>
        <h2 style={{ margin: 0 }}>{course.title}</h2>
        <div className="role-badge">Course Details</div>
      </div>

      <div className="grid" style={{ gridTemplateColumns: '2fr 1fr' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          {/* TEXT BLOCKS */}
          <section className="glass-card">
            <h3>📖 Lessons & Info</h3>
            {isOwner && (
              <form onSubmit={handleAddTextBlock} style={{ marginBottom: '1.5rem' }}>
                <input placeholder="Topic Title" value={newTextBlock.title} onChange={e => setNewTextBlock({...newTextBlock, title: e.target.value})} required />
                <textarea 
                  placeholder="Content..." 
                  value={newTextBlock.content} 
                  onChange={e => setNewTextBlock({...newTextBlock, content: e.target.value})}
                  style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', marginBottom: '1rem', minHeight: '100px' }}
                />
                <button type="submit">Post Info</button>
              </form>
            )}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {textBlocks.map(tb => (
                <div key={tb.id} className="glass-card" style={{ padding: '1rem', background: '#fff' }}>
                  <h4 style={{ margin: 0 }}>{tb.title}</h4>
                  <p style={{ whiteSpace: 'pre-wrap' }}>{tb.content}</p>
                </div>
              ))}
            </div>
          </section>

          {/* ASSIGNMENTS */}
          <section className="glass-card">
            <h3>📝 Assignments</h3>
            {isOwner && (
              <form onSubmit={handleAddAssignment} style={{ marginBottom: '1.5rem' }}>
                <input placeholder="Task Title" value={newAssignment.title} onChange={e => setNewAssignment({...newAssignment, title: e.target.value})} required />
                <input type="date" value={newAssignment.due_date} onChange={e => setNewAssignment({...newAssignment, due_date: e.target.value})} required />
                <button type="submit">Create Task</button>
              </form>
            )}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {assignments.map(as => (
                <div key={as.id} className="glass-card" style={{ padding: '1rem', borderLeft: '4px solid #f59e0b' }}>
                  <h4 style={{ margin: 0 }}>{as.title}</h4>
                  <p style={{ fontSize: '0.8rem', color: '#64748b' }}>Due: {as.due_date}</p>
                </div>
              ))}
            </div>
          </section>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* FILES */}
          <section className="glass-card">
            <h3>📁 Resources</h3>
            {isOwner && (
              <div style={{ marginBottom: '1.5rem' }}>
                <input type="file" onChange={handleFileUpload} disabled={uploading} style={{ fontSize: '0.8rem' }} />
                {uploading && <p style={{ fontSize: '0.8rem' }}>Uploading...</p>}
              </div>
            )}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {files.map(f => (
                <a key={f.id} href={f.gcs_url} target="_blank" rel="noreferrer" style={{ textDecoration: 'none', color: '#6366f1', fontSize: '0.9rem' }}>
                  📄 {f.file_name}
                </a>
              ))}
            </div>
          </section>

          {/* STUDENTS LIST */}
          {isOwner && (
            <section className="glass-card">
              <h3>👥 Enrolled Students</h3>
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
        </div>
      </div>
    </div>
  );
};

export default CourseDetails;
