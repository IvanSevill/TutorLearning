import { useState, useEffect } from 'react';
import { adminService } from '../../api';
import { useNotification } from '../../hooks/useNotification';

const AdminUsers = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const { showNotify } = useNotification();

  useEffect(() => {
    adminService.getUsers()
      .then(setUsers)
      .catch(err => showNotify(err.message, 'error'))
      .finally(() => setLoading(false));
  }, [showNotify]);

  const handleToggleTeacher = async (target) => {
    try {
      const updated = await adminService.setTeacher(target.email, !target.is_teacher);
      setUsers(prev => prev.map(other => (other.id === updated.id ? updated : other)));
      showNotify(`${target.email} updated`);
    } catch (err) {
      showNotify(err.message, 'error');
    }
  };

  if (loading) return <div style={{ textAlign: 'center', padding: '5rem' }}><div className="spinner" /></div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {users.map(target => (
        <div key={target.id} className="glass-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem 1.5rem' }}>
          <div>
            <div style={{ fontWeight: '600' }}>{target.first_name} {target.last_name}</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{target.email}</div>
          </div>
          <button className={target.is_teacher ? 'danger' : 'primary'} onClick={() => handleToggleTeacher(target)}>
            {target.is_teacher ? 'Remove teacher role' : 'Make teacher'}
          </button>
        </div>
      ))}
    </div>
  );
};

export default AdminUsers;
