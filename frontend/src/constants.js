// Detect if we are in local development
const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';

// If local, use the default FastAPI port. Otherwise, assume the backend is on the same origin (production).
export const API_URL = isLocal 
  ? 'http://localhost:8000' 
  : window.location.origin;
