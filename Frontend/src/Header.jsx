import { Link } from 'react-router-dom';

function Header() {
  return (
    <header className="app-header">
      <h1>Каталог участников</h1>
      <nav>
        <Link to="/" className="nav-link">На главную</Link>
      </nav>
    </header>
  );
}

export default Header;