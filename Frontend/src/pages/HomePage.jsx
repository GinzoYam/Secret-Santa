import { useState, useMemo } from 'react'; // <-- ДОБАВЛЕН useMemo
import { useNavigate } from 'react-router-dom';
import './HomePage.css';

const Snowflake = ({ style, char }) => {
  return (
    <div className="snowflake" style={style}>
      {char}
    </div>
  );
};

function HomePage() {
  const [title, setTitle] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();

  // ИСПОЛЬЗУЕМ useMemo, чтобы снежинки сгенерировались ОДИН РАЗ при загрузке
  const snowflakes = useMemo(() => {
    const symbols = ['❅', '❆', '★', '🎄', '🎁', '🔔', '❄️'];
    
    return Array.from({ length: 40 }).map((_, i) => {
      const size = Math.random() * 20 + 10; 
      const left = Math.random() * 100; 
      const duration = Math.random() * 10 + 5; 
      const delay = Math.random() * 10; 
      
      const colors = ['#ffffff', '#ff4c4c', '#ffd700', '#a3e4d7'];
      const color = colors[Math.floor(Math.random() * colors.length)];
      
      // Выбираем случайный символ один раз
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
  }, []); // <-- Пустой массив зависимостей означает "выполнить 1 раз"

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:5000/api/rooms', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title }),
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
      
      {/* Снежинки теперь берут готовый массив из useMemo */}
      <div className="snow-container">
        {snowflakes.map((flake) => (
          <Snowflake key={flake.id} style={flake.style} char={flake.char} />
        ))}
      </div>

      <div className="home-card">
        <div className="home-card-header">
          <h1>ТАЙНЫЙ САНТА</h1>
        </div>
        
        <div className="home-card-body">
          <form onSubmit={handleSubmit} className="home-form">
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
                
                <button type="submit" className="home-btn-inline" disabled={loading}>
                  {loading ? '...' : 'Создать'}
                </button>
              </div>
            </div>

            {error && <p className="home-error">{error}</p>}
          </form>
        </div>
      </div>
    </div>
  );
}

export default HomePage;