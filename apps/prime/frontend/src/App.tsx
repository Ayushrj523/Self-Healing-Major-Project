import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const api = axios.create({ baseURL: '' });

interface ContentItem {
  id: number; title: string; description: string; category: string;
  youtube_id: string; thumbnail_url?: string; release_year: number;
  rating: number; is_prime_exclusive: number; duration_minutes: number;
}
interface CategoryGroup { category: string; items: ContentItem[]; total: number; }

function VideoModal({ item, onClose }: { item: ContentItem; onClose: () => void }) {
  useEffect(() => { const h = (e: KeyboardEvent) => { if (e.key==='Escape') onClose() }; window.addEventListener('keydown',h); return ()=>window.removeEventListener('keydown',h); }, [onClose]);
  return (
    <div className="prime-modal-overlay" onClick={onClose}>
      <div className="prime-modal" onClick={e=>e.stopPropagation()}>
        <button className="prime-modal-close" onClick={onClose}>✕</button>
        <iframe src={`https://www.youtube-nocookie.com/embed/${item.youtube_id}?autoplay=1&rel=0`}
          allow="autoplay; encrypted-media; fullscreen" allowFullScreen title={item.title} />
        <div className="prime-modal-info">
          <h2 style={{fontSize:'1.3rem',fontWeight:700,marginBottom:8}}>{item.title}</h2>
          <div style={{display:'flex',gap:10,marginBottom:8,color:'#8197A4',fontSize:'0.85rem'}}>
            <span style={{color:'#00A8E1',fontWeight:600}}>{Math.round(item.rating*10)}% Match</span>
            <span>{item.release_year}</span>
            {item.is_prime_exclusive ? <span className="prime-badge">PRIME</span> : null}
          </div>
          <p style={{color:'#8197A4',lineHeight:1.6,fontSize:'0.9rem'}}>{item.description}</p>
        </div>
      </div>
    </div>
  );
}

function ContentCard({ item, onClick }: { item: ContentItem; onClick: () => void }) {
  return (
    <div className="prime-card" onClick={onClick}>
      <img src={`https://img.youtube.com/vi/${item.youtube_id}/mqdefault.jpg`} alt={item.title} loading="lazy" />
      <div className="prime-card-info">
        <div className="prime-card-title">{item.title}</div>
        <div className="prime-card-meta">
          <span>{item.release_year}</span>
          {item.is_prime_exclusive ? <span className="prime-badge">PRIME</span> : null}
        </div>
      </div>
    </div>
  );
}

function LoginPage({ onLogin }: { onLogin: (token: string, user: any) => void }) {
  const [email, setEmail] = useState('user1@prime.com');
  const [password, setPassword] = useState('sentinels123');
  const [error, setError] = useState('');
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); setError('');
    try { const { data } = await api.post('/api/auth/login', { email, password }); onLogin(data.access_token, data.user); }
    catch (err: any) { setError(err.response?.data?.error || 'Login failed'); }
  };
  return (
    <div className="prime-login">
      <form className="prime-login-form" onSubmit={handleSubmit}>
        <img src="https://upload.wikimedia.org/wikipedia/commons/1/11/Amazon_Prime_Video_logo.svg" alt="Prime Video" style={{ height: 35, marginBottom: 15 }} />
        <h1>Sign In</h1>
        {error && <div style={{color:'#ff4444',marginBottom:12,fontSize:'0.85rem'}}>{error}</div>}
        <input placeholder="Email" value={email} onChange={e=>setEmail(e.target.value)} />
        <input type="password" placeholder="Password" value={password} onChange={e=>setPassword(e.target.value)} />
        <button type="submit" className="btn-prime">Sign In</button>
        <p style={{color:'#8197A4',marginTop:14,fontSize:'0.85rem'}}>Demo credentials pre-filled.</p>
      </form>
    </div>
  );
}

function BrowsePage({ user, onLogout }: { user: any; onLogout: () => void }) {
  const [categories, setCategories] = useState<CategoryGroup[]>([]);
  const [featured, setFeatured] = useState<ContentItem|null>(null);
  const [selected, setSelected] = useState<ContentItem|null>(null);
  const [scrolled, setScrolled] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const h = () => setScrolled(window.scrollY > 40);
    window.addEventListener('scroll', h); return () => window.removeEventListener('scroll', h);
  }, []);

  useEffect(() => {
    const load = async () => {
      try {
        const [bRes, fRes] = await Promise.all([api.get('/api/content/browse'), api.get('/api/content/featured')]);
        setCategories(bRes.data);
        if (fRes.data.length) setFeatured(fRes.data[0]);
      } catch(e) { console.error(e); }
      setLoading(false);
    };
    load();
  }, []);

  if (loading) return <div className="prime-loading"><div className="prime-spinner"/></div>;

  return (
    <>
      <nav className={`prime-nav ${scrolled?'scrolled':''}`}>
        <div style={{display:'flex',alignItems:'center',gap:32}}>
          <span className="prime-logo">PrimeOS</span>
          <ul className="prime-nav-links">
            <li><a href="/">Home</a></li><li><a href="/">Store</a></li><li><a href="/">Categories</a></li>
          </ul>
        </div>
        <div style={{display:'flex',alignItems:'center',gap:12}}>
          <span style={{fontSize:'0.85rem',color:'#8197A4'}}>{user.display_name}</span>
          <button onClick={onLogout} style={{color:'#8197A4',fontSize:'0.8rem'}}>Sign Out</button>
        </div>
      </nav>

      {featured && (
        <div className="prime-hero">
          <div className="prime-hero-bg" style={{backgroundImage:`url(https://img.youtube.com/vi/${featured.youtube_id}/maxresdefault.jpg)`}}/>
          <div className="prime-hero-content">
            {featured.is_prime_exclusive ? <span className="prime-hero-badge">PRIME EXCLUSIVE</span> : null}
            <h1 className="prime-hero-title">{featured.title}</h1>
            <p className="prime-hero-desc">{featured.description}</p>
            <button className="btn-prime" onClick={()=>setSelected(featured)}><svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style={{marginRight:6}}><polygon points="5 3 19 12 5 21 5 3"/></svg>Play</button>
          </div>
        </div>
      )}

      <div className="prime-section">
        {categories.map(cat => (
          <div key={cat.category} className="prime-row">
            <h2 className="prime-row-title">{cat.category}</h2>
            <div className="prime-row-items">
              {cat.items.map(item => <ContentCard key={item.id} item={item} onClick={()=>setSelected(item)} />)}
            </div>
          </div>
        ))}
      </div>

      {selected && <VideoModal item={selected} onClose={()=>setSelected(null)} />}
    </>
  );
}

export default function App() {
  const [user, setUser] = useState<any>(null);
  const [token, setToken] = useState(localStorage.getItem('prime_token'));

  useEffect(() => {
    const s = localStorage.getItem('prime_user');
    if (s && token) try { setUser(JSON.parse(s)) } catch {}
  }, [token]);

  const handleLogin = (t: string, u: any) => {
    localStorage.setItem('prime_token', t); localStorage.setItem('prime_user', JSON.stringify(u));
    setToken(t); setUser(u);
  };
  const handleLogout = () => {
    localStorage.removeItem('prime_token'); localStorage.removeItem('prime_user');
    setToken(null); setUser(null);
  };

  if (!user || !token) return <LoginPage onLogin={handleLogin} />;
  return <BrowsePage user={user} onLogout={handleLogout} />;
}
