// Set VITE_API_URL (no trailing slash) when building for a deployed backend.
// The default uses localhost, not 127.0.0.1: the page is on localhost, and browsers
// only send a SameSite=Lax session cookie to the same site.
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
