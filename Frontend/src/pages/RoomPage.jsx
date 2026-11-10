import { useParams } from 'react-router-dom';
import { useState, useEffect } from 'react';
import './RoomPage.css';

// --- ИКОНКИ (SVG) ---
const ClockIcon = () => (
  <svg viewBox="0 0 24 24"><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm.5-13H11v6l5.2 3.2.8-1.3-4.5-2.7V7z"/></svg>
);

const UsersIcon = () => (
  <svg viewBox="0 0 24 24"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg>
);

const GiftIcon = () => (
  <svg viewBox="0 0 24 24"><path d="M20 6h-2.18c.11-.31.18-.65.18-1 0-1.66-1.34-3-3-3-1.05 0-1.96.54-2.5 1.35l-.5.67-.5-.68C10.96 2.54 10.05 2 9 2 7.34 2 6 3.34 6 5c0 .35.07.69.18 1H4c-1.11 0-1.99.89-1.99 2L2 19c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2zm-5-2c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zM9 4c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm11 15H4v-2h16v2zm0-5H4V8h5.08L7 10.83 8.62 12 11 8.76l1-1.36 1 1.36L15.38 12 17 10.83 14.92 8H20v6z"/></svg>
);

const StarIcon = () => (
  <svg className="player-star" viewBox="0 0 24 24" fill="#ffcc00" stroke="#e6a800" strokeWidth="2">
    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
  </svg>
);

function RoomPage() {
  const { id } = useParams();

  const [shuffleLoading, setShuffleLoading] = useState(false);
  const [shuffleDone, setShuffleDone] = useState(false);
  const [shuffleError, setShuffleError] = useState('');

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [wish, setWish] = useState('');

  const [participants, setParticipants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('players');

  const getParticipants = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`http://localhost:5000/api/rooms/${id}/users`);
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || 'Ошибка загрузки участников');
      setParticipants(result.data || []);
    } catch (error) {
      setError(error.message || 'Не удалось загрузить участников');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    getParticipants();
  }, [id]);

const handleShuffle = async () => {
  if (shuffleLoading || shuffleDone) return;

  setShuffleLoading(true);
  setShuffleError('');

  try {
    const response = await fetch(
      `http://localhost:5000/api/rooms/${id}/shuffle`,
      {
        method: 'POST'
      }
    );

    const result = await response.json();

    if (!response.ok || !result.success) {
      throw new Error(result.error || 'Не удалось провести жеребьёвку');
    }

    setShuffleDone(true);

  } catch (error) {
    setShuffleError(error.message || 'Ошибка соединения с сервером');
  } finally {
    setShuffleLoading(false);
  }
};

const handleSubmit = async (e) => {
  e.preventDefault();
  setSubmitting(true);
  setError('');

  try {
    const response = await fetch(
      `http://localhost:5000/api/rooms/${id}/users`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name, email, wish })
      }
    );

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.error || 'Ошибка при добавлении участника');
    }

    setName('');
    setEmail('');
    setWish('');

    await getParticipants();

  } catch (error) {
    setError(error.message || 'Не удалось связаться с сервером');
  } finally {
    setSubmitting(false);
  }
};


return (
  <div className="room-page">

    {/* Отдельная верхняя белая плашка */}
    <header className="room-header">
      <img
        src="/logo.png"
        alt="Логотип"
        className="room-logo"
      />
      <div className="room-account">
        <span>Б</span>
      </div>
    </header>

    {/* Большая белая карточка комнаты */}
    <main className="main-card">

        <div className="room-info-header">
          <div className="room-info-text">
            <h2>Название комнаты</h2>
            <p>Организатор: Имя пользователя</p>
            <p>Бюджет: 700-1000₽</p>
            <p>Дата обмена подарками: 07.01.2027</p>
            <p>Место сбора (комментарий): -</p>
          </div>
          <div className="status-badge">
            <ClockIcon /> Ожидание жеребьёвки
          </div>
        </div>

        <div className="room-tabs">
          <button
            className={`tab-btn ${activeTab === 'players' ? 'active' : 'inactive'}`}
            onClick={() => setActiveTab('players')}
          >
            <UsersIcon /> Все игроки
          </button>
          <button
            className={`tab-btn ${activeTab === 'ward' ? 'active' : 'inactive'}`}
            onClick={() => setActiveTab('ward')}
          >
            <GiftIcon /> Мой подопечный
          </button>
        </div>

        {activeTab === 'players' && (
          <>
            <h2 className="players-title">Игроки({participants.length})</h2>
            {loading ? (
              <p className="room-loading">Загрузка...</p>
            ) : (
              <div className="players-grid">
                {participants.map((participant, index) => (
                  <div className="player-card" key={participant.id}>
                    {index === 0 && <StarIcon />}
                    <div className="player-avatar"></div>
                    <span className="player-name">
                      {participant.name} {index === 0 && '(Организатор)'}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {activeTab === 'ward' && (
          <p style={{ fontSize: '18px', marginBottom: '40px' }}>
            Информация о подопечном пока недоступна.
          </p>
        )}

        <form className="join-form" onSubmit={handleSubmit}>
          <h2>Присоединиться к игре</h2>
          <input type="text" placeholder="Имя" value={name} onChange={(e) => setName(e.target.value)} required />
          <input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <textarea placeholder="Пожелания" value={wish} onChange={(e) => setWish(e.target.value)} />
          <button type="submit" disabled={submitting}>{submitting ? 'Добавление...' : 'Присоединиться'}</button>
          {error && <p className="room-error">{error}</p>}
        </form>
        <section className="admin-panel">
  <h2>Панель администратора</h2>

  {shuffleDone ? (
    <div className="shuffle-success">
      ✓ Жеребьёвка завершена
    </div>
  ) : (
    <button
      className="draw-button"
      onClick={handleShuffle}
      disabled={shuffleLoading}
    >
      {shuffleLoading ? (
        <>
          <span className="shuffle-spinner"></span>
          Жеребьёвка проводится...
        </>
      ) : (
        'Запустить жеребьёвку'
      )}
    </button>
  )}

  {shuffleError && (
    <p className="room-error">{shuffleError}</p>
  )}
</section>
      </main>

      {/* Кнопка внизу (вне белой карточки) */}
    
    </div>
  );
}

export default RoomPage;