import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate, useParams } from 'react-router-dom';
import './index.css';
import Auth from './components/Auth';
import Dashboard from './components/Dashboard';
import CourseDetails from './components/CourseDetails';
import { courseService } from './api';

const ProtectedRoute = ({ user, children }) => {
  if (!user) return <Navigate to="/login" replace />;
  return children;
};

function AppContent() {
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem('user');
    return savedUser ? JSON.parse(savedUser) : null;
  });
  
  const navigate = useNavigate();

  const handleLogin = (userData) => {
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
    navigate('/');
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('user');
    navigate('/login');
  };

  return (
    <Routes>
      <Route path="/login" element={
        user ? <Navigate to="/" replace /> : <div className="container"><Auth onLogin={handleLogin} /></div>
      } />
      
      <Route path="/" element={
        <ProtectedRoute user={user}>
          <Dashboard 
            user={user} 
            onLogout={handleLogout} 
            onSelectCourse={(course) => navigate(`/course/${course.id}`, { state: { course } })} 
          />
        </ProtectedRoute>
      } />
      
      <Route path="/course/:id" element={
        <ProtectedRoute user={user}>
          <CourseDetailsWrapper user={user} onBack={() => navigate('/')} />
        </ProtectedRoute>
      } />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

const CourseDetailsWrapper = ({ user, onBack }) => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [course, setCourse] = useState(navigate.state?.course || null);
  const [loading, setLoading] = useState(!course);

  useEffect(() => {
    if (!course) {
      courseService.getById(id)
        .then(setCourse)
        .catch(() => onBack())
        .finally(() => setLoading(false));
    }
  }, [id, course, onBack]);

  if (loading) return <div className="container"><div className="spinner" /></div>;
  if (!course) return null;

  return <CourseDetails course={course} user={user} onBack={onBack} />;
};

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;
