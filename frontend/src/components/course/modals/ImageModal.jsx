import { useState } from 'react';
import Modal from '../../common/Modal';

const ImageModal = ({ isOpen, onClose, currentImage, onUpload }) => {
  const [file, setFile] = useState(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (file) {
      onUpload(file);
      setFile(null);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="🖼️ Change Cover Image">
      {currentImage && (
        <img src={currentImage} alt="current cover"
          style={{ width: '100%', height: '180px', objectFit: 'cover', borderRadius: '12px', marginBottom: '1.5rem' }} />
      )}
      <form onSubmit={handleSubmit}>
        <label>Select new image</label>
        <input type="file" accept="image/*" onChange={e => setFile(e.target.files[0])} required />
        <div style={{ display: 'flex', gap: '10px', marginTop: '0.5rem' }}>
          <button type="submit" className="primary" style={{ flex: 1 }}>Upload</button>
          <button type="button" onClick={onClose} style={{ flex: 1 }}>Cancel</button>
        </div>
      </form>
    </Modal>
  );
};

export default ImageModal;
