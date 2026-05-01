import { useState } from 'react';
import { API_URL } from '../../constants';
import { getFileType } from '../../utils';

const MediaPreview = ({ file }) => {
  const [failed, setFailed] = useState(false);
  const proxyUrl = `${API_URL}/files/${file.id}`;
  const type = getFileType(file);

  if (failed || type === 'other') {
    return (
      <div style={{ padding: '1.5rem', textAlign: 'center' }}>
        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📄</div>
        <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>{file.file_name}</p>
        <a href={proxyUrl} target="_blank" rel="noreferrer"
          style={{ 
            display: 'inline-block', 
            padding: '8px 20px', 
            borderRadius: '10px', 
            background: 'var(--primary)', 
            color: 'white', 
            textDecoration: 'none', 
            fontWeight: 600 
          }}>
          ⬇ Download
        </a>
      </div>
    );
  }

  if (type === 'image') {
    return (
      <img
        src={proxyUrl}
        alt={file.file_name}
        onError={() => setFailed(true)}
        style={{ maxWidth: '100%', maxHeight: '420px', objectFit: 'contain', borderRadius: '8px', display: 'block', margin: '0 auto' }}
      />
    );
  }

  if (type === 'video') {
    return (
      <video controls onError={() => setFailed(true)}
        style={{ maxWidth: '100%', maxHeight: '420px', borderRadius: '8px', display: 'block', margin: '0 auto' }}>
        <source src={proxyUrl} />
        Your browser does not support video.
      </video>
    );
  }

  if (type === 'pdf') {
    return (
      <iframe src={proxyUrl} title={file.file_name} width="100%" height="420px"
        style={{ border: 'none', borderRadius: '8px' }} onError={() => setFailed(true)} />
    );
  }

  return null;
};

export default MediaPreview;
