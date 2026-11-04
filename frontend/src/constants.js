// Set VITE_API_URL (no trailing slash) when building for a deployed backend.
export const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
