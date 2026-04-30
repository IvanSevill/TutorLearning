import React, { useState } from 'react';
import { API_URL } from '../App';

const Auth = ({ onLogin }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    is_teacher: false
  });
  const [error, setError] = useState('');

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    try {
      const endpoint = isLogin ? '/login/' : '/users/';
      const body = isLogin 
        ? { email: formData.email, password: formData.password }
        : { ...formData };

      const response = await fetch(`${API_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      const data = await response.json();
      if (response.ok) {
        if (isLogin) {
          onLogin(data.user);
        } else {
          alert('Registration successful! Please login.');
          setIsLogin(true);
        }
      } else {
        setError(data.detail || 'Operation failed');
      }
    } catch (err) {
      setError('Server unreachable. Make sure backend is running.');
    }
  };

  return (
    <div className="glass-card" style={{ maxWidth: '400px', margin: '4rem auto' }}>
      <h2 style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
        {isLogin ? 'Welcome Back' : 'Join Tutor-Learning'}
      </h2>
      
      <form onSubmit={handleSubmit}>
        {!isLogin && (
          <>
            <input type="text" name="first_name" placeholder="First Name" onChange={handleChange} required />
            <input type="text" name="last_name" placeholder="Last Name" onChange={handleChange} required />
          </>
        )}
        <input type="email" name="email" placeholder="Email" onChange={handleChange} required />
        <input type="password" name="password" placeholder="Password" onChange={handleChange} required />
        
        {!isLogin && (
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '1rem' }}>
            <input type="checkbox" name="is_teacher" checked={formData.is_teacher} onChange={handleChange} style={{ width: 'auto', margin: 0 }} />
            Register as Teacher
          </label>
        )}

        <button type="submit" style={{ width: '100%', marginTop: '1rem' }}>
          {isLogin ? 'Login' : 'Sign Up'}
        </button>
      </form>

      {error && <p style={{ color: '#ef4444', textAlign: 'center', marginTop: '1rem' }}>{error}</p>}

      <p style={{ textAlign: 'center', marginTop: '1.5rem', color: '#64748b' }}>
        {isLogin ? "Don't have an account? " : "Already have an account? "}
        <a href="#" onClick={() => setIsLogin(!isLogin)} style={{ color: '#6366f1', textDecoration: 'none', fontWeight: 'bold' }}>
          {isLogin ? 'Register' : 'Login'}
        </a>
      </p>
    </div>
  );
};

export default Auth;
