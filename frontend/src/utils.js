export const formatDate = (dateStr) => {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return d.toLocaleDateString('es-ES', { 
    day: '2-digit', 
    month: 'short', 
    year: 'numeric', 
    hour: '2-digit', 
    minute: '2-digit' 
  });
};

export const getFileType = (f) => {
  const mime = f.mime_type || '';
  const name = (f.file_name || '').toLowerCase();
  if (mime.startsWith('image/') || /\.(jpg|jpeg|png|gif|webp|svg)$/.test(name)) return 'image';
  if (mime.startsWith('video/') || /\.(mp4|webm|ogg|mov)$/.test(name)) return 'video';
  if (mime === 'application/pdf' || name.endsWith('.pdf')) return 'pdf';
  return 'other';
};
