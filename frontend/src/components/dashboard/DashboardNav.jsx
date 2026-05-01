const DashboardNav = ({ user, onLogout }) => {
  return (
    <nav className="glass-card" style={{ 
      display: 'flex', justifyContent: 'space-between', alignItems: 'center', 
      marginBottom: '3rem', padding: '1rem 2rem' 
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{ 
          fontSize: '1.5rem', fontWeight: '800', 
          background: 'linear-gradient(135deg, #6366f1, #ec4899)', 
          WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' 
        }}>
          TutorLearning
        </div>
      </div>
      
      <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontWeight: '700' }}>{user.first_name} {user.last_name}</div>
          <div className="role-badge" style={{ fontSize: '0.65rem' }}>{user.is_teacher ? 'TEACHER' : 'STUDENT'}</div>
        </div>
        <button className="danger" onClick={onLogout}>Logout</button>
      </div>
    </nav>
  );
};

export default DashboardNav;
