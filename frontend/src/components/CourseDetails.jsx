import { useState, useEffect, useCallback, useMemo } from 'react';
import { courseService, assignmentService, postService, enrollmentService, fileService } from '../api';
import { useNotification } from '../hooks/useNotification';

// Sub-components
import CourseHeader from './course/CourseHeader';
import CourseFeed from './course/CourseFeed';
import StudentList from './course/StudentList';

// Modals
import EditCourseModal from './course/modals/EditCourseModal';
import TaskModal from './course/modals/TaskModal';
import PostModal from './course/modals/PostModal';
import UploadModal from './course/modals/UploadModal';
import ImageModal from './course/modals/ImageModal';

const CourseDetails = ({ course: initialCourse, user, onBack }) => {
  const [course, setCourse] = useState(initialCourse);
  const [feed, setFeed] = useState([]);
  const [students, setStudents] = useState([]);
  const [files, setFiles] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [submissions, setSubmissions] = useState([]);
  const [activeTab, setActiveTab] = useState('feed');
  const [loading, setLoading] = useState(false);
  const { showNotify } = useNotification();

  // Modals state
  const [activeModal, setActiveModal] = useState(null); // 'edit', 'task', 'post', 'upload', 'image'
  const [editingTask, setEditingTask] = useState(null);

  const isOwner = Number(course.teacher_id) === Number(user.id);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [feedData, tasksData, studentsData, filesData, submissionsData] = await Promise.all([
        courseService.getFeed(course.id),
        courseService.getTasks(course.id),
        courseService.getStudents(course.id),
        courseService.getFiles(course.id),
        assignmentService.getSubmissionsForCourse(course.id, user.id)
      ]);
      setFeed(feedData);
      setTasks(tasksData);
      setStudents(studentsData);
      setFiles(filesData);
      setSubmissions(submissionsData);
    } catch {
      showNotify('Error fetching course data', 'error');
    } finally {
      setLoading(false);
    }
  }, [course.id, user.id, showNotify]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const unifiedFeed = useMemo(() => [
    ...feed.map(p => ({ ...p, _type: 'post', _date: p.created_at })),
    ...tasks.map(t => ({ ...t, _type: 'task', _date: t.created_at })),
    ...files.map(f => ({ ...f, _type: 'file', _date: f.upload_date })),
  ].sort((a, b) => new Date(b._date || 0) - new Date(a._date || 0)), [feed, tasks, files]);

  // Handlers
  const handleUpdateCourse = async (formData) => {
    try {
      const updated = await courseService.update(course.id, formData);
      setCourse(updated);
      setActiveModal(null);
      showNotify('Course updated');
    } catch (error) {
      showNotify(error.message, 'error');
    }
  };

  const handleUpdateImage = async (file) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      const data = await courseService.updateImage(course.id, formData);
      setCourse(prev => ({ ...prev, image_url: data.image_url }));
      setActiveModal(null);
      showNotify('Cover image updated');
    } catch (error) {
      showNotify(error.message, 'error');
    }
  };

  const handleSaveTask = async (taskData) => {
    try {
      const payload = { ...taskData };
      if (payload.due_date) payload.due_date = new Date(payload.due_date).toISOString();

      if (editingTask) {
        await assignmentService.update(editingTask.id, payload);
        showNotify('Task updated');
      } else {
        await assignmentService.create({ ...payload, course_id: course.id });
        showNotify('Task created');
      }
      setActiveModal(null);
      setEditingTask(null);
      fetchData();
    } catch (error) {
      showNotify(error.message, 'error');
    }
  };

  const handleSavePost = async (postData) => {
    try {
      await postService.create({ ...postData, course_id: course.id });
      setActiveModal(null);
      showNotify('Announcement posted');
      fetchData();
    } catch (error) {
      showNotify(error.message, 'error');
    }
  };

  const handleUploadFile = async (file) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      await fileService.uploadToCourse(course.id, formData);
      setActiveModal(null);
      showNotify('File uploaded');
      fetchData();
    } catch (error) {
      showNotify(error.message, 'error');
    }
  };

  const handleDelete = async (type, id) => {
    if (!window.confirm(`Are you sure you want to delete this ${type}?`)) return;
    try {
      if (type === 'post') await postService.delete(id);
      if (type === 'task') await assignmentService.delete(id);
      if (type === 'file') await fileService.delete(id);
      showNotify(`${type} deleted`);
      fetchData();
    } catch (error) {
      showNotify(error.message, 'error');
    }
  };

  const handleLeaveCourse = async () => {
    if (!window.confirm('Are you sure you want to leave this course?')) return;
    try {
      await enrollmentService.leave({ user_id: user.id, course_id: course.id });
      showNotify('Left course successfully');
      onBack();
    } catch (error) {
      showNotify(error.message, 'error');
    }
  };

  const handleStudentSubmit = async (taskId, file) => {
    if (!file) return showNotify('Please select a file', 'error');
    try {
      showNotify('Uploading...', 'success', 1000);
      const formData = new FormData();
      formData.append('file', file);
      const { url } = await fileService.uploadGeneral(formData);
      await assignmentService.submit({ user_id: user.id, assignment_id: taskId, submission_file_url: url });
      showNotify('Submitted successfully!');
      fetchData();
    } catch (error) {
      showNotify(error.message, 'error');
    }
  };

  return (
    <div className="container" style={{ maxWidth: '900px', margin: '0 auto', padding: '2rem' }}>
      {/* Top Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <button onClick={onBack} className="secondary">← Back</button>
        <div style={{ display: 'flex', gap: '10px' }}>
          {isOwner ? (
            <>
              <button className="primary" onClick={() => setActiveModal('edit')}>⚙️ Edit</button>
              <button className="primary" onClick={() => { setEditingTask(null); setActiveModal('task'); }}>➕ Task</button>
              <button className="primary" onClick={() => setActiveModal('post')}>📢 Post</button>
              <button className="primary" onClick={() => setActiveModal('upload')}>📎 File</button>
            </>
          ) : (
            <button className="danger" onClick={handleLeaveCourse}>🚪 Leave</button>
          )}
        </div>
      </div>

      <CourseHeader course={course} isOwner={isOwner} onEditImage={() => setActiveModal('image')} />

      {/* Tabs */}
      <div className="tabs" style={{ marginBottom: '2rem' }}>
        <div className={`tab ${activeTab === 'feed' ? 'active' : ''}`} onClick={() => setActiveTab('feed')}>📖 Feed</div>
        <div className={`tab ${activeTab === 'students' ? 'active' : ''}`} onClick={() => setActiveTab('students')}>👥 Students ({students.length})</div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '3rem' }}><div className="spinner" /></div>
      ) : (
        <>
          {activeTab === 'feed' && (
            <CourseFeed 
              items={unifiedFeed} 
              isOwner={isOwner} 
              onDeletePost={id => handleDelete('post', id)}
              onDeleteTask={id => handleDelete('task', id)}
              onDeleteFile={id => handleDelete('file', id)}
              onEditTask={task => { setEditingTask(task); setActiveModal('task'); }}
              onStudentSubmit={handleStudentSubmit}
              submissions={submissions}
            />
          )}
          {activeTab === 'students' && <StudentList students={students} />}
        </>
      )}

      {/* Modals */}
      <EditCourseModal 
        isOpen={activeModal === 'edit'} 
        onClose={() => setActiveModal(null)} 
        course={course} 
        onUpdate={handleUpdateCourse} 
      />
      <TaskModal 
        isOpen={activeModal === 'task'} 
        onClose={() => { setActiveModal(null); setEditingTask(null); }} 
        editingTask={editingTask} 
        onSave={handleSaveTask} 
      />
      <PostModal 
        isOpen={activeModal === 'post'} 
        onClose={() => setActiveModal(null)} 
        onSave={handleSavePost} 
      />
      <UploadModal 
        isOpen={activeModal === 'upload'} 
        onClose={() => setActiveModal(null)} 
        onUpload={handleUploadFile} 
      />
      <ImageModal 
        isOpen={activeModal === 'image'} 
        onClose={() => setActiveModal(null)} 
        currentImage={course.image_url} 
        onUpload={handleUpdateImage} 
      />
    </div>
  );
};

export default CourseDetails;
