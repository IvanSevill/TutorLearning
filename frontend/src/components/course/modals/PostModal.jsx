import { useState } from 'react';
import Modal from '../../common/Modal';

const PostModal = ({ isOpen, onClose, onSave }) => {
  const [form, setForm] = useState({ title: '', content: '' });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(form);
    setForm({ title: '', content: '' });
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="📢 New Announcement">
      <form onSubmit={handleSubmit}>
        <label>Title</label>
        <input value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} required />
        <label>Content</label>
        <textarea rows="5" value={form.content} onChange={e => setForm({ ...form, content: e.target.value })} required />
        <div style={{ display: 'flex', gap: '10px' }}>
          <button type="submit" className="primary" style={{ flex: 1 }}>Post</button>
          <button type="button" onClick={onClose} style={{ flex: 1 }}>Cancel</button>
        </div>
      </form>
    </Modal>
  );
};

export default PostModal;
