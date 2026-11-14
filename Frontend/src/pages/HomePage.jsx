import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../Header';

function HomePage() {
  const [title, setTitle] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();

  async function handleSubmit(event) {
    event.preventDefault();

    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:5000/api/rooms', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ title }),
      });

      const result = await response.json();

      if (!response.ok || !result.success) {
        throw new Error(result.error || 'Не удалось создать комнату');
      }

      // Сохраняем секретный код администратора
localStorage.setItem(
  `room_${result.data.id}_admin_code`,
  result.data.admin_code
);

// Переходим в комнату
navigate(`/room/${result.data.id}`);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <Header />

      <main>
        <h1>Создать комнату</h1>

        <form onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Название комнаты"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            required
          />

          <button type="submit" disabled={loading}>
            {loading ? 'Создание...' : 'Создать комнату'}
          </button>
        </form>

        {error && <p>{error}</p>}
      </main>
    </>
  );
}

export default HomePage;