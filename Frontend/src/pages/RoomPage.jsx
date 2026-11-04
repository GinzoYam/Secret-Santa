
import { useParams } from 'react-router-dom';
import { useState, useEffect } from 'react';
import ParticipantCard from '../ParticipantCard';

function RoomPage() {
  const { id } = useParams();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [wish, setWish] = useState('');

  const [participants, setParticipants] = useState([]);

  const getParticipants = async () => {
    try {
      const response = await fetch(
        `http://localhost:5000/api/rooms/${id}/users`
      );

      const result = await response.json();

      if (!response.ok) {
        alert(result.error || 'Ошибка загрузки участников');
        return;
      }

      setParticipants(result.data);
    } catch (error) {
      console.error('Ошибка:', error);
    }
  };

  useEffect(() => {
    getParticipants();
  }, [id]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      const response = await fetch(
        `http://localhost:5000/api/rooms/${id}/users`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            name,
            email,
            wish
          })
        }
      );

      const result = await response.json();

      if (!response.ok) {
        alert(result.error || 'Ошибка при добавлении участника');
        return;
      }

      alert('Вы успешно присоединились к игре!');

      setName('');
      setEmail('');
      setWish('');

      getParticipants();

    } catch (error) {
      console.error('Ошибка:', error);
      alert('Не удалось связаться с сервером');
    }
  };

  return (
    <main>
      <h1>Комната</h1>
      <p>ID комнаты: {id}</p>

      <h2>Присоединиться к игре</h2>

      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Имя"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          style={{
            width: '250px',
            height: '35px',
            boxSizing: 'border-box'
          }}
        />

        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          style={{
            width: '250px',
            height: '35px',
            boxSizing: 'border-box'
          }}
        />

        <textarea
          placeholder="Пожелания"
          value={wish}
          onChange={(e) => setWish(e.target.value)}
          style={{
            width: '250px',
            height: '35px',
            boxSizing: 'border-box',
            resize: 'none',
            verticalAlign: 'top',
            padding: '8px',
            fontFamily: 'Arial',
            fontSize: '13.33px'
          }}
        />

        <button type="submit">
          Присоединиться
        </button>
      </form>

      <h2>Участники комнаты</h2>

      {participants.map((participant) => (
        <ParticipantCard
          key={participant.id}
          name={participant.name}
          email={participant.email}
          wish={participant.wish}
        />
      ))}
    </main>
  );
}

export default RoomPage;
