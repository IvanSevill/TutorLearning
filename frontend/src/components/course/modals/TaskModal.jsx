import { useState, useEffect } from 'react';
import Modal from '../../common/Modal';

const TaskModal = ({ isOpen, onClose, onSave, editingTask }) => {
  const [form, setForm] = useState({ title: '', description: '', due_date: '' });

  useEffect(() => {
    if (editingTask) {
      setForm({
        title: editingTask.title,
        description: editingTask.description || '',
        due_date: editingTask.due_date ? new Date(editingTask.due_date).toISOString().split('T')[0] : ''
      });
    } else {
      setForm({ title: '', description: '', due_date: '' });
    }
  }, [editingTask, isOpen]);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(form);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={editingTask ? "✏️ Edit Task" : "➕ New Task"}>
      <form onSubmit={handleSubmit}>
        <label>Title</label>
        <input value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} required />
        <label>Description</label>
        <textarea rows="4" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} required />
        <label>Due Date</label>
        <input type="date" value={form.due_date} onChange={e => setForm({ ...form, due_date: e.target.value })} required />
        <div style={{ display: 'flex', gap: '10px' }}>
          <button type="submit" className="primary" style={{ flex: 1 }}>{editingTask ? 'Save' : 'Create'}</button>
          <button type="button" onClick={onClose} style={{ flex: 1 }}>Cancel</button>
        </div>
      </form>
    </Modal>
  );
};

export default TaskModal;
