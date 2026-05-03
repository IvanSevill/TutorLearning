import { useState } from 'react';
import Modal from '../../common/Modal';

const EditCourseModal = ({ isOpen, onClose, course, onUpdate }) => {
  const [form, setForm] = useState({
    title: course.title,
    description: course.description,
    is_visible: course.is_visible,
    is_enrollable: course.is_enrollable
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onUpdate(form);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="⚙️ Edit Course">
      <form onSubmit={handleSubmit}>
        <label>Title</label>
        <input value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} required />
        <label>Description</label>
        <textarea rows="4" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} required />
        <div style={{ display: 'flex', gap: '1.5rem', marginBottom: '1.5rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: 0 }}>
            <input type="checkbox" checked={form.is_visible} onChange={e => setForm({ ...form, is_visible: e.target.checked })} style={{ width: 'auto', margin: 0 }} />
            Visible
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: 0 }}>
            <input type="checkbox" checked={form.is_enrollable} onChange={e => setForm({ ...form, is_enrollable: e.target.checked })} style={{ width: 'auto', margin: 0 }} />
            Enrollable
          </label>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button type="submit" className="primary" style={{ flex: 1 }}>Save</button>
          <button type="button" onClick={onClose} style={{ flex: 1 }}>Cancel</button>
        </div>
      </form>
    </Modal>
  );
};

export default EditCourseModal;
