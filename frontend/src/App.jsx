import { useState } from 'react';
import './index.css';
import Auth from './components/Auth';
import Dashboard from './components/Dashboard';
import CourseDetails from './components/CourseDetails';

import { API_URL } from './constants';

function App() {
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem('user');
    return savedUser ? JSON.parse(savedUser) : null;
  });
  const [selectedCourse, setSelectedCourse] = useState(null);

  const handleLogin = (userData) => {
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
  };

  const handleLogout = () => {
    setUser(null);
    setSelectedCourse(null);
    localStorage.removeItem('user');
  };

  if (!user) return <div className="container"><Auth onLogin={handleLogin} /></div>;

  return (
    <div className="container">
      {selectedCourse ? (
        <CourseDetails 
          course={selectedCourse} 
          user={user} 
          onBack={() => setSelectedCourse(null)} 
        />
      ) : (
        <Dashboard 
          user={user} 
          onLogout={handleLogout} 
          onSelectCourse={setSelectedCourse} 
        />
      )}
    </div>
  );
}

export default App;
