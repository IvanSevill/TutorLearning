import { useState } from 'react';
import { authService } from '../api';

const Auth = ({ onLogin }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: ''
  });
  const [error, setError] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    console.log("Submitting Auth form", { isLogin, email: formData.email });
    
    try {
      if (isLogin) {
        onLogin(await authService.login({ email: formData.email, password: formData.password }));
      } else {
        await authService.register({
          first_name: formData.first_name,
          last_name: formData.last_name,
          email: formData.email,
          password: formData.password
        });
        alert('Registration successful! Please login.');
        setIsLogin(true);
      }
    } catch (err) {
      console.error("Auth error:", err);
      // fetch() throws a TypeError when it cannot reach the server at all.
      setError(err instanceof TypeError ? 'Server unreachable. Make sure backend is running.' : err.message);
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
