import { useState, createContext, useContext, useCallback } from 'react';

const NotificationContext = createContext();

export const NotificationProvider = ({ children }) => {
  const [notification, setNotification] = useState(null);

  const showNotify = useCallback((msg, type = 'success', duration = 3500) => {
    setNotification({ msg, type });
    setTimeout(() => setNotification(null), duration);
  }, []);

  return (
    <NotificationContext.Provider value={{ showNotify }}>
      {children}
      {notification && (
        <div className={`toast ${notification.type === 'error' ? 'danger' : ''}`}>
          {notification.type === 'error' ? '❌' : '✅'} {notification.msg}
        </div>
      )}
    </NotificationContext.Provider>
  );
};

export const useNotification = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
};
