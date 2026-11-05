import { API_URL } from '../constants';

// Kept in memory only. After a page reload, authService.getSession() fetches it again.
let csrfToken = null;
let onUnauthorized = () => {};

export const setUnauthorizedHandler = (handler) => {
  onUnauthorized = handler;
};

const csrfHeaders = (method) => (
  method !== 'GET' && csrfToken ? { 'X-CSRF-Token': csrfToken } : {}
);

const request = async (endpoint, options = {}) => {
  const { headers, ...rest } = options;
  const config = {
    ...rest,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...csrfHeaders(rest.method),
      ...headers,
    },
  };

  const response = await fetch(`${API_URL}${endpoint}`, config);
  
  if (response.status === 401) onUnauthorized();
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || 'Something went wrong');
  }

  return response.status === 204 ? null : response.json();
};

export const api = {
  get: (endpoint, options) => request(endpoint, { ...options, method: 'GET' }),
  post: (endpoint, body, options) => request(endpoint, { ...options, method: 'POST', body: JSON.stringify(body) }),
  put: (endpoint, body, options) => request(endpoint, { ...options, method: 'PUT', body: JSON.stringify(body) }),
  patch: (endpoint, body, options) => request(endpoint, { ...options, method: 'PATCH', body: JSON.stringify(body) }),
  delete: (endpoint, options) => request(endpoint, { ...options, method: 'DELETE' }),
  
  // Specialized for FormData (uploads)
  upload: async (endpoint, formData, method = 'POST') => {
    const response = await fetch(`${API_URL}${endpoint}`, {
      method,
      body: formData,
      credentials: 'include',
      headers: csrfHeaders(method),
    });
    if (response.status === 401) onUnauthorized();
    if (!response.ok) throw new Error('Upload failed');
    return response.json();
  }
};

const startSession = (session) => {
  csrfToken = session.csrf_token;
  return session.user;
};

export const authService = {
  register: (data) => api.post('/users/', data),
  login: async (credentials) => startSession(await api.post('/login/', credentials)),
  getSession: async () => startSession(await api.get('/session/')),
  logout: async () => {
    await api.post('/logout/');
    csrfToken = null;
  },
};

export const adminService = {
  getUsers: () => api.get('/users/'),
  setTeacher: (email, isTeacher) => api.put(`/users/${encodeURIComponent(email)}/teacher`, { is_teacher: isTeacher }),
};

export const courseService = {
  getAllAvailable: () => api.get('/courses/available'),
  getMyEnrollments: () => api.get('/enrollments/me'),
  getTeaching: () => api.get('/courses/teaching'),
  create: (data) => api.post('/courses/', data),
  update: (id, data) => api.put(`/courses/${id}`, data),
  updateImage: (id, formData) => api.upload(`/courses/${id}/image`, formData, 'PATCH'),
  getById: (id) => api.get(`/courses/${id}`),
  getFeed: (id) => api.get(`/textblocks/course/${id}`),
  getTasks: (id) => api.get(`/assignments/course/${id}`),
  getStudents: (id) => api.get(`/enrollments/course/${id}`),
  getFiles: (id) => api.get(`/files/course/${id}`),
};

export const assignmentService = {
  create: (data) => api.post('/assignments/', data),
  update: (id, data) => api.put(`/assignments/${id}`, data),
  delete: (id) => api.delete(`/assignments/${id}`),
  submit: (data) => api.post('/submissions/', data),
  getMySubmissionsForCourse: (courseId) => api.get(`/submissions/course/${courseId}/me`),
  deleteMySubmission: (assignmentId) => api.delete(`/submissions/assignment/${assignmentId}/me`),
};

export const postService = {
  create: (data) => api.post('/textblocks/', data),
  delete: (id) => api.delete(`/textblocks/${id}`),
};

export const enrollmentService = {
  enroll: (data) => api.post('/enrollments/', data),
  leave: (data) => api.delete('/enrollments/', { body: JSON.stringify(data) }),
};

export const fileService = {
  uploadToCourse: (courseId, formData) => api.upload(`/files/course/${courseId}`, formData),
  uploadGeneral: (formData) => api.upload('/files/upload', formData),
  delete: (id) => api.delete(`/files/${id}`),
};
