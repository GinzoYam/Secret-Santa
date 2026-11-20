import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './SuperAdmin.css';

function SuperAdmin() {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:5000/api/superadmin/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
      });

      const result = await response.json();

      if (!response.ok || !result.success) {
        throw new Error(result.error || 'Неверный пароль');
      }

      localStorage.setItem('superadmin_token', result.token || 'true');
      navigate('/superadmin/dashboard');
    } catch (err) {
      setError(err.message || 'Ошибка соединения');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="superadmin-page">
      <div className="superadmin-card">
        <h2>Вход в панель супер-админа</h2>
        <form onSubmit={handleSubmit} className="superadmin-form">
          <input
            type="password"
            placeholder="Введите пароль"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <button type="submit" disabled={loading}>
            {loading ? 'Проверка...' : 'Войти'}
          </button>
          {error && <p className="error-message">{error}</p>}
        </form>
      </div>
    </div>
  );
}

export default SuperAdmin;