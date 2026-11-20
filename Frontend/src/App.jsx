import { Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';
import RoomPage from './pages/RoomPage';
import SuperAdmin from './pages/SuperAdmin';

function App() {
  return (
    <div className="app-wrapper">
      <main className="app-main">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/room/:id" element={<RoomPage />} />
          <Route path="/superadmin" element={<SuperAdmin />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;