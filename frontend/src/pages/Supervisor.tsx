import { useEffect, useState } from 'react';
import { albumsApi, imagesApi } from '../services/api';
import type { Album, GalleryImage } from '../types';
import { useAuth } from '../context/AuthContext';

export default function Supervisor() {
  const { user, logout } = useAuth();
  const [tab, setTab] = useState<'albums' | 'quarantine'>('albums');
  const [pendingAlbums, setPendingAlbums] = useState<Album[]>([]);
  const [quarantine, setQuarantine] = useState<GalleryImage[]>([]);
  const [msg, setMsg] = useState('');

  const loadPending = () => albumsApi.pendingAlbums().then(r => setPendingAlbums(r.data)).catch(() => {});
  const loadQuarantine = () => imagesApi.quarantine().then(r => setQuarantine(r.data)).catch(() => {});

  useEffect(() => { loadPending(); loadQuarantine(); }, []);

  const reviewAlbum = async (id: number, action: 'approve' | 'reject') => {
    try {
      await albumsApi.reviewAlbum(id, action);
      setMsg(`Album ${action}d successfully.`);
      loadPending();
    } catch { setMsg('Action failed.'); }
  };

  const reviewImage = async (id: number, action: 'approve' | 'reject') => {
    try {
      if (action === 'approve') await imagesApi.approveQuarantine(id);
      else await imagesApi.rejectQuarantine(id);
      setMsg(`Image ${action}d.`);
      loadQuarantine();
    } catch { setMsg('Action failed.'); }
  };

  const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api';

  return (
    <div className="dashboard">
      <header className="dash-header">
        <h1>🔍 Supervisor Panel</h1>
        <div className="dash-user">
          <span>👤 {user?.username}</span>
          <button className="btn btn-sm" onClick={logout}>Sign Out</button>
        </div>
      </header>

      {msg && <p className="form-msg">{msg}</p>}

      <div className="tab-bar">
        <button className={`tab ${tab === 'albums' ? 'active' : ''}`} onClick={() => setTab('albums')}>
          📋 Pending Albums ({pendingAlbums.length})
        </button>
        <button className={`tab ${tab === 'quarantine' ? 'active' : ''}`} onClick={() => setTab('quarantine')}>
          🚨 Quarantine ({quarantine.length})
        </button>
      </div>

      {tab === 'albums' && (
        <section className="panel">
          <h2>Albums Awaiting Approval</h2>
          {pendingAlbums.length === 0 ? <p className="empty">No pending albums.</p> : (
            <table className="data-table">
              <thead><tr><th>Title</th><th>Description</th><th>Requested</th><th>Actions</th></tr></thead>
              <tbody>
                {pendingAlbums.map(a => (
                  <tr key={a.id}>
                    <td>{a.title}</td>
                    <td>{a.description ?? '—'}</td>
                    <td>{new Date(a.created_at).toLocaleDateString()}</td>
                    <td className="action-cell">
                      <button className="btn btn-green btn-sm" onClick={() => reviewAlbum(a.id, 'approve')}>✅ Approve</button>
                      <button className="btn btn-red btn-sm" onClick={() => reviewAlbum(a.id, 'reject')}>❌ Reject</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}

      {tab === 'quarantine' && (
        <section className="panel">
          <h2>Quarantined Images</h2>
          {quarantine.length === 0 ? <p className="empty">Quarantine is empty.</p> : (
            <div className="quarantine-grid">
              {quarantine.map(img => (
                <div key={img.id} className="quarantine-card">
                  <div className="preview-container mb-4" style={{ position: 'relative', height: '200px', backgroundColor: '#0f172a', borderRadius: '8px', overflow: 'hidden' }}>
                    <img 
                      src={`${API}/images/${img.stored_filename}`} 
                      alt="Quarantine Preview"
                      style={{ width: '100%', height: '100%', objectFit: 'contain', filter: 'sepia(0.5) saturate(1.5)' }} 
                      onError={(e) => (e.currentTarget.src = 'https://placehold.co/400x300/1e293b/64748b?text=No+Preview+Available')}
                    />
                    <div style={{ position: 'absolute', top: 0, left: 0, padding: '4px 8px', background: 'red', color: 'white', fontSize: '10px', fontWeight: 'bold' }}>
                      SUSPICIOUS FILE
                    </div>
                  </div>
                  <div className="q-info">
                    <p className="q-filename">{img.original_filename}</p>
                    {img.steg_result && (
                      <div className="steg-details">
                        <p>🔬 {img.steg_result.diagnosis}</p>
                        {img.steg_result.lsb_ratio !== undefined && (
                          <p>LSB ratio: <code>{img.steg_result.lsb_ratio}</code></p>
                        )}
                        <div className="steg-flags">
                          {img.steg_result.lsb_suspicious && <span className="flag">LSB ⚠️</span>}
                          {img.steg_result.histogram_suspicious && <span className="flag">Histogram ⚠️</span>}
                          {img.steg_result.entropy_suspicious && <span className="flag">Entropy ⚠️</span>}
                        </div>
                      </div>
                    )}
                    <div className="action-cell">
                      <button className="btn btn-green btn-sm" onClick={() => reviewImage(img.id, 'approve')}>
                        ✅ Approve (Ignore Alert)
                      </button>
                      <button className="btn btn-red btn-sm" onClick={() => reviewImage(img.id, 'reject')}>
                        🗑️ Delete Permanently
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
