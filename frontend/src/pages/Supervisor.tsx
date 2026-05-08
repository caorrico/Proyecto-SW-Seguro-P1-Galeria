import { useEffect, useState } from 'react';
import { albumsApi, imagesApi } from '../services/api';
import type { Album, GalleryImage } from '../types';
import { useAuth } from '../context/AuthContext';

export default function Supervisor() {
  const { user, logout } = useAuth();
  const [tab, setTab] = useState<'myalbums' | 'albums' | 'quarantine'>('myalbums');
  const [msg, setMsg] = useState('');

  // ── Pestaña: Mis álbumes (supervisor como usuario) ──────────────────────
  const [myAlbums, setMyAlbums] = useState<Album[]>([]);
  const [selectedAlbum, setSelectedAlbum] = useState<Album | null>(null);
  const [albumImages, setAlbumImages] = useState<GalleryImage[]>([]);
  const [newTitle, setNewTitle] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [uploading, setUploading] = useState(false);

  const loadMyAlbums = () => albumsApi.myAlbums().then(r => setMyAlbums(r.data)).catch(() => {});
  const loadAlbumImages = (album: Album) =>
    imagesApi.albumImages(album.id).then(r => setAlbumImages(r.data)).catch(() => setAlbumImages([]));

  const selectAlbum = (album: Album) => {
    setSelectedAlbum(album);
    loadAlbumImages(album);
  };

  const createAlbum = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await albumsApi.requestAlbum({ title: newTitle, description: newDesc });
      setNewTitle(''); setNewDesc('');
      setMsg('✅ Album created and auto-approved.');
      loadMyAlbums();
    } catch (err: any) {
      setMsg(err.response?.data?.detail ?? 'Error creating album');
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!selectedAlbum || !e.target.files?.[0]) return;
    setUploading(true);
    setMsg('');
    try {
      const result = await imagesApi.upload(selectedAlbum.id, e.target.files[0]);
      const steg = result.data.steg_result;
      setMsg(steg?.is_suspicious
        ? '⚠️ Image flagged for steganography — sent to quarantine.'
        : '✅ Image uploaded successfully.');
      loadAlbumImages(selectedAlbum);
    } catch (err: any) {
      setMsg(err.response?.data?.detail ?? 'Upload failed');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  // ── Pestaña: Álbumes pendientes ─────────────────────────────────────────
  const [pendingAlbums, setPendingAlbums] = useState<Album[]>([]);
  const loadPending = () => albumsApi.pendingAlbums().then(r => setPendingAlbums(r.data)).catch(() => {});

  const reviewAlbum = async (id: number, action: 'approve' | 'reject') => {
    try {
      await albumsApi.reviewAlbum(id, action);
      setMsg(`Album ${action}d successfully.`);
      loadPending();
    } catch { setMsg('Action failed.'); }
  };

  // ── Pestaña: Cuarentena ─────────────────────────────────────────────────
  const [quarantine, setQuarantine] = useState<GalleryImage[]>([]);
  const loadQuarantine = () => imagesApi.quarantine().then(r => setQuarantine(r.data)).catch(() => {});

  const reviewImage = async (id: number, action: 'approve' | 'reject') => {
    try {
      if (action === 'approve') await imagesApi.approveQuarantine(id);
      else await imagesApi.rejectQuarantine(id);
      setMsg(`Image ${action}d.`);
      loadQuarantine();
    } catch { setMsg('Action failed.'); }
  };

  const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api';

  useEffect(() => { loadMyAlbums(); loadPending(); loadQuarantine(); }, []);

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
        <button className={`tab ${tab === 'myalbums' ? 'active' : ''}`} onClick={() => setTab('myalbums')}>
          🖼️ My Gallery
        </button>
        <button className={`tab ${tab === 'albums' ? 'active' : ''}`} onClick={() => setTab('albums')}>
          📋 Pending Albums ({pendingAlbums.length})
        </button>
        <button className={`tab ${tab === 'quarantine' ? 'active' : ''}`} onClick={() => setTab('quarantine')}>
          🚨 Quarantine ({quarantine.length})
        </button>
      </div>

      {/* ── Mi Galería ──────────────────────────────────────────────────── */}
      {tab === 'myalbums' && (
        <div className="dash-grid">
          <section className="panel">
            <h2>My Albums</h2>
            <form onSubmit={createAlbum} className="form-inline">
              <input placeholder="Album title" value={newTitle}
                onChange={e => setNewTitle(e.target.value)} required />
              <input placeholder="Description (optional)" value={newDesc}
                onChange={e => setNewDesc(e.target.value)} />
              <button type="submit" className="btn btn-primary btn-sm">Create Album</button>
            </form>
            <ul className="album-list">
              {myAlbums.map(a => (
                <li key={a.id}
                  className={`album-item ${selectedAlbum?.id === a.id ? 'active' : ''}`}
                  onClick={() => selectAlbum(a)}>
                  <span>{a.title}</span>
                  <span className={`badge ${a.status === 'APPROVED' ? 'badge-green' : a.status === 'REJECTED' ? 'badge-red' : 'badge-yellow'}`}>
                    {a.status}
                  </span>
                </li>
              ))}
              {myAlbums.length === 0 && <p className="empty">No albums yet. Create one above.</p>}
            </ul>
          </section>

          <section className="panel">
            {selectedAlbum ? (
              <>
                <h2>{selectedAlbum.title}</h2>
                {selectedAlbum.status === 'APPROVED' && (
                  <div className="upload-area">
                    <label htmlFor="sup-file-upload" className="btn btn-primary">
                      {uploading ? 'Uploading…' : '📤 Upload Image'}
                    </label>
                    <input id="sup-file-upload" type="file"
                      accept="image/jpeg,image/png,image/gif,image/webp"
                      onChange={handleUpload} disabled={uploading} style={{ display: 'none' }} />
                  </div>
                )}
                <div className="image-grid">
                  {albumImages.map(img => (
                    <div key={img.id} className="image-card">
                      <img src={imagesApi.imageUrl(img.stored_filename)} alt={img.original_filename} loading="lazy" />
                      <div className="image-info">
                        <span className={`badge ${img.status === 'CLEAN' || img.status === 'APPROVED_MANUAL' ? 'badge-green' : 'badge-yellow'}`}>
                          {img.status}
                        </span>
                        <span className="image-name">{img.original_filename}</span>
                      </div>
                    </div>
                  ))}
                  {albumImages.length === 0 && <p className="empty">No images yet.</p>}
                </div>
              </>
            ) : (
              <p className="empty">Select an album to view or upload images.</p>
            )}
          </section>
        </div>
      )}

      {/* ── Álbumes pendientes ──────────────────────────────────────────── */}
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

      {/* ── Cuarentena ─────────────────────────────────────────────────── */}
      {tab === 'quarantine' && (
        <section className="panel">
          <h2>Quarantined Images</h2>
          {quarantine.length === 0 ? <p className="empty">Quarantine is empty.</p> : (
            <div className="quarantine-grid">
              {quarantine.map(img => (
                <div key={img.id} className="quarantine-card">
                  <img src={`${API}/images/${img.stored_filename}`} alt={img.original_filename} />
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
