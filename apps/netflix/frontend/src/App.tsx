import React, { useState, useEffect, useCallback } from 'react';
import { authApi, contentApi, searchApi, type ContentItem, type CategoryGroup, type User } from './api';

// ─── Video Modal Component ──────────────────────────────────
function VideoModal({ item, onClose }: { item: ContentItem; onClose: () => void }) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>✕</button>
        <iframe
          className="modal-video"
          src={`https://www.youtube-nocookie.com/embed/${item.youtube_id}?autoplay=1&rel=0&modestbranding=1`}
          allow="autoplay; encrypted-media; fullscreen"
          allowFullScreen
          title={item.title}
        />
        <div className="modal-info">
          <h2 className="modal-title">{item.title}</h2>
          <div className="modal-meta">
            <span className="content-card-rating">{Math.round(item.rating * 10)}% Match</span>
            <span>{item.release_year}</span>
            <span>{item.maturity_rating}</span>
            <span>{item.duration_minutes}m</span>
          </div>
          <p className="modal-desc">{item.description}</p>
        </div>
      </div>
    </div>
  );
}

// ─── Content Card ───────────────────────────────────────────
function ContentCard({ item, onClick }: { item: ContentItem; onClick: () => void }) {
  return (
    <div className="content-card" onClick={onClick}>
      <img src={item.thumbnail_url || `https://img.youtube.com/vi/${item.youtube_id}/mqdefault.jpg`}
        alt={item.title} loading="lazy" />
      <div className="content-card-overlay">
        <div className="content-card-title">{item.title}</div>
        <div className="content-card-meta">
          <span className="content-card-rating">{Math.round(item.rating * 10)}%</span>
          <span>{item.release_year}</span>
          <span>{item.maturity_rating}</span>
        </div>
      </div>
    </div>
  );
}

// ─── Content Row ────────────────────────────────────────────
function ContentRow({ title, items, onPlay }: { title: string; items: ContentItem[]; onPlay: (item: ContentItem) => void }) {
  if (!items.length) return null;
  return (
    <div className="content-row">
      <h2 className="content-row-title">{title}</h2>
      <div className="content-row-items">
        {items.map(item => (
          <ContentCard key={item.id} item={item} onClick={() => onPlay(item)} />
        ))}
      </div>
    </div>
  );
}

// ─── Navbar ─────────────────────────────────────────────────
function Navbar({ user, onLogout, onSearch }: { user: User | null; onLogout: () => void; onSearch: (q: string) => void }) {
  const [scrolled, setScrolled] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [query, setQuery] = useState('');

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 50);
    window.addEventListener('scroll', handler);
    return () => window.removeEventListener('scroll', handler);
  }, []);

  return (
    <nav className={`navbar ${scrolled ? 'scrolled' : ''}`}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 40 }}>
        <a href="/" className="navbar-logo">NETFLIXOS</a>
        <ul className="navbar-links">
          <li><a href="/">Home</a></li>
          <li><a href="/">TV Shows</a></li>
          <li><a href="/">Movies</a></li>
          <li><a href="/">New & Popular</a></li>
        </ul>
      </div>
      <div className="navbar-right">
        <input
          className={`search-input ${searchOpen ? 'open' : ''}`}
          placeholder="Titles, people, genres"
          value={query}
          onChange={e => { setQuery(e.target.value); if (e.target.value.length > 1) onSearch(e.target.value); }}
          onBlur={() => { if (!query) setSearchOpen(false); }}
        />
        <button onClick={() => setSearchOpen(!searchOpen)} style={{ color: 'white', fontSize: '1.2rem' }}>🔍</button>
        {user && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: '0.85rem', color: '#aaa' }}>{user.display_name}</span>
            <button onClick={onLogout} style={{ color: '#aaa', fontSize: '0.8rem' }}>Sign Out</button>
          </div>
        )}
      </div>
    </nav>
  );
}

// ─── Hero Banner ────────────────────────────────────────────
function Hero({ item, onPlay }: { item: ContentItem; onPlay: () => void }) {
  return (
    <div className="hero">
      <div className="hero-backdrop" style={{
        backgroundImage: `url(https://img.youtube.com/vi/${item.youtube_id}/maxresdefault.jpg)`
      }} />
      <div className="hero-content">
        <h1 className="hero-title">{item.title}</h1>
        <p className="hero-description">{item.description}</p>
        <div className="hero-actions">
          <button className="btn btn-play" onClick={onPlay}>▶ Play</button>
          <button className="btn btn-info">ℹ More Info</button>
        </div>
      </div>
    </div>
  );
}

// ─── Login Page ─────────────────────────────────────────────
function LoginPage({ onLogin }: { onLogin: (token: string, user: User) => void }) {
  const [email, setEmail] = useState('user1@netflix.com');
  const [password, setPassword] = useState('sentinels123');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true); setError('');
    try {
      const { data } = await authApi.login(email, password);
      onLogin(data.access_token, data.user);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed');
    }
    setLoading(false);
  };

  return (
    <div className="auth-page">
      <form className="auth-form" onSubmit={handleSubmit}>
        <h1>Sign In</h1>
        {error && <div style={{ color: '#E50914', marginBottom: 16, fontSize: '0.9rem' }}>{error}</div>}
        <input type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} required />
        <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} required />
        <button type="submit" className="btn btn-red" disabled={loading}>
          {loading ? 'Signing in...' : 'Sign In'}
        </button>
        <p className="auth-toggle">Demo credentials pre-filled. <a href="#">Just click Sign In.</a></p>
      </form>
    </div>
  );
}

// ─── Browse Page ────────────────────────────────────────────
function BrowsePage({ user, onLogout }: { user: User; onLogout: () => void }) {
  const [categories, setCategories] = useState<CategoryGroup[]>([]);
  const [featured, setFeatured] = useState<ContentItem | null>(null);
  const [selectedItem, setSelectedItem] = useState<ContentItem | null>(null);
  const [searchResults, setSearchResults] = useState<ContentItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [browseRes, featuredRes] = await Promise.all([
          contentApi.browse(), contentApi.featured()
        ]);
        setCategories(browseRes.data);
        if (featuredRes.data.length > 0) {
          setFeatured(featuredRes.data[Math.floor(Math.random() * Math.min(5, featuredRes.data.length))]);
        }
      } catch (err) {
        console.error('Failed to load content:', err);
      }
      setLoading(false);
    };
    load();
  }, []);

  const handleSearch = useCallback(async (q: string) => {
    if (q.length < 2) { setSearchResults([]); return; }
    try {
      const { data } = await searchApi.search(q);
      setSearchResults(data);
    } catch { setSearchResults([]); }
  }, []);

  if (loading) return <div className="loading-screen"><div className="spinner" /></div>;

  return (
    <>
      <Navbar user={user} onLogout={onLogout} onSearch={handleSearch} />
      {featured && <Hero item={featured} onPlay={() => setSelectedItem(featured)} />}
      <div className="content-section">
        {searchResults.length > 0 && (
          <ContentRow title="Search Results" items={searchResults} onPlay={setSelectedItem} />
        )}
        {categories.map(cat => (
          <ContentRow key={cat.category} title={cat.category} items={cat.items} onPlay={setSelectedItem} />
        ))}
      </div>
      {selectedItem && <VideoModal item={selectedItem} onClose={() => setSelectedItem(null)} />}
    </>
  );
}

// ─── App Root ───────────────────────────────────────────────
export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('netflix_token'));

  useEffect(() => {
    const saved = localStorage.getItem('netflix_user');
    if (saved && token) { try { setUser(JSON.parse(saved)); } catch {} }
  }, [token]);

  const handleLogin = (t: string, u: User) => {
    localStorage.setItem('netflix_token', t);
    localStorage.setItem('netflix_user', JSON.stringify(u));
    setToken(t); setUser(u);
  };

  const handleLogout = () => {
    localStorage.removeItem('netflix_token');
    localStorage.removeItem('netflix_user');
    setToken(null); setUser(null);
  };

  if (!user || !token) return <LoginPage onLogin={handleLogin} />;
  return <BrowsePage user={user} onLogout={handleLogout} />;
}
