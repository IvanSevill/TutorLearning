const StudentList = ({ students }) => {
  if (students.length === 0) {
    return (
      <div className="glass-card" style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
        No students enrolled yet.
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {students.map(enr => (
        <div key={enr.user_id} className="glass-card" style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1rem 1.5rem' }}>
          <div style={{ 
            width: '48px', height: '48px', borderRadius: '50%', 
            background: 'linear-gradient(135deg, var(--primary), var(--secondary))', 
            display: 'flex', alignItems: 'center', justifyContent: 'center', 
            fontWeight: 'bold', fontSize: '1.1rem', flexShrink: 0 
          }}>
            {enr.user?.first_name?.[0]}{enr.user?.last_name?.[0]}
          </div>
          <div>
            <div style={{ fontWeight: '600' }}>{enr.user?.first_name} {enr.user?.last_name}</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{enr.user?.email}</div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default StudentList;
