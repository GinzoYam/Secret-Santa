import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import './HomePage.css';

// Компонент снежинки
const Snowflake = ({ style, char }) => {
  return (
    <div className="snowflake" style={style}>
      {char}
    </div>
  );
};

function HomePage() {
  const [title, setTitle] = useState('');
  const [budget, setBudget] = useState('');
  const [eventDate, setEventDate] = useState('');
  const [rules, setRules] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();

  // Генерация снежинок (1 раз при загрузке)
  const snowflakes = useMemo(() => {
    const symbols = ['❅', '❆', '★', '🎄', '🎁', '🔔', '❄️'];
    
    return Array.from({ length: 40 }).map((_, i) => {
      const size = Math.random() * 20 + 10; 
      const left = Math.random() * 100; 
      const duration = Math.random() * 10 + 5; 
      const delay = Math.random() * 10; 
      
      const colors = ['#ffffff', '#ff4c4c', '#ffd700', '#a3e4d7'];
      const color = colors[Math.floor(Math.random() * colors.length)];
      const char = symbols[Math.floor(Math.random() * symbols.length)];

      return {
        id: i,
        char: char,
        style: {
          left: `${left}%`,
          animationDuration: `${duration}s`,
          animationDelay: `${delay}s`,
          fontSize: `${size}px`,
          color: color,
          opacity: Math.random() * 0.5 + 0.3, 
        },
      };
    });
  }, []);

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:5000/api/rooms', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          title, 
          budget: budget ? Number(budget) : null, // <-- ИСПРАВЛЕНИЕ: бюджет как число
          event_date: eventDate || null, 
          rules: rules || null 
        }),
      });

      const result = await response.json();

      if (!response.ok || !result.success) {
        throw new Error(result.error || 'Не удалось создать комнату');
      }

      localStorage.setItem(`room_${result.data.id}_admin_code`, result.data.admin_code);
      navigate(`/room/${result.data.id}`);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="home-page">
      
      {/* Слой снежинок (позади всего) */}
      <div className="snow-container">
        {snowflakes.map((flake) => (
          <Snowflake key={flake.id} style={flake.style} char={flake.char} />
        ))}
      </div>

      {/* Слой снежных сугробов (поверх снежинок, но под карточкой) */}
      <div className="snowdrift-container">
        <div className="snowdrift snow-back back-1"></div>
        <div className="snowdrift snow-back back-2"></div>
        <div className="snowdrift snow-mid mid-1"></div>
        <div className="snowdrift snow-mid mid-2"></div>
        <div className="snowdrift snow-front front-1"></div>
        <div className="snowdrift snow-front front-2"></div>
        
        {/* Центральный сугроб под кнопкой */}
        <div className="snowdrift snow-front snow-center"></div>
      </div>

      {/* Карточка создания комнаты (поверх всего) */}
      <div className="home-card">
        <div className="home-card-header">
          <h1>ТАЙНЫЙ САНТА</h1>
        </div>
        
        <div className="home-card-body">
          <form onSubmit={handleSubmit} className="home-form">
            
            {/* Поле 1: Название */}
            <div className="home-form-group">
              <label className="home-label">Название комнаты</label>
              <div className="home-input-wrapper">
                <input
                  type="text"
                  className="home-input"
                  placeholder="Введите название..."
                  value={title}
                  onChange={(event) => setTitle(event.target.value)}
                  required
                />
              </div>
            </div>

            {/* Поле 2: Бюджет */}
            <div className="home-form-group">
              <label className="home-label">Бюджет (например, 700-1000)</label>
              <div className="home-input-wrapper">
                <input
                  type="number"
                  className="home-input"
                  placeholder="Введите сумму..."
                  value={budget}
                  onChange={(event) => setBudget(event.target.value)}
                />
              </div>
            </div>

            {/* Поле 3: Дата */}
            <div className="home-form-group">
              <label className="home-label">Дата обмена подарками</label>
              <div className="home-input-wrapper">
                <input
                  type="date"
                  className="home-input"
                  value={eventDate}
                  onChange={(event) => setEventDate(event.target.value)}
                />
              </div>
            </div>

            {/* Поле 4: Правила */}
            <div className="home-form-group">
              <label className="home-label">Правила / Место сбора</label>
              <div className="home-input-wrapper">
                <textarea
                  className="home-input home-textarea"
                  placeholder="Введите правила или комментарий..."
                  value={rules}
                  onChange={(event) => setRules(event.target.value)}
                  rows="3"
                />
              </div>
            </div>

            {/* Кнопка в самом низу */}
            <div className="home-form-group">
              <button type="submit" className="home-btn-inline" disabled={loading}>
                {loading ? 'Создание...' : 'Создать комнату'}
              </button>
            </div>

            {error && <p className="home-error">{error}</p>}
          </form>
        </div>
      </div>
      
    </div>
  );
}

export default HomePage;