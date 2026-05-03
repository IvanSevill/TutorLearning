import { useState } from 'react';
import Modal from '../../common/Modal';

const UploadModal = ({ isOpen, onClose, onUpload }) => {
  const [file, setFile] = useState(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (file) {
      onUpload(file);
      setFile(null);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="📎 Upload Course Material">
      <form onSubmit={handleSubmit}>
        <label>Select File</label>
        <input type="file" onChange={e => setFile(e.target.files[0])} required />
        <div style={{ display: 'flex', gap: '10px', marginTop: '0.5rem' }}>
          <button type="submit" className="primary" style={{ flex: 1 }}>Upload</button>
          <button type="button" onClick={onClose} style={{ flex: 1 }}>Cancel</button>
        </div>
      </form>
    </Modal>
  );
};

export default UploadModal;
