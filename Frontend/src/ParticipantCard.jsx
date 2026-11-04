
function ParticipantCard({ name, email, wish }) {
  return (
    <div>
      <h2>{name}</h2>
      <p>Email: {email}</p>
      <p>Пожелание: {wish}</p>
    </div>
  );
}

export default ParticipantCard;
