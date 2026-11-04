import { useParams } from 'react-router-dom';

function RoomPage() {
  const { id } = useParams();

  return (
    <main>
      <h1>Комната</h1>
      <p>ID комнаты: {id}</p>
    </main>
  );
}

export default RoomPage;