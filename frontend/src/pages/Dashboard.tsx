import { useEffect, useState } from 'react';
import { albumsApi, imagesApi } from '../services/api';
import { imagesApi as imgApi } from '../services/api';
import type { Album, GalleryImage } from '../types';
import { useAuth } from '../context/AuthContext';

export default function Dashboard() {
  const { user, logout } = useAuth();
  const [albums, setAlbums] = useState<Album[]>([]);
  const [selectedAlbum, setSelectedAlbum] = useState<Album | null>(null);
  const [images, setImages] = useState<GalleryImage[]>([]);
  const [newTitle, setNewTitle] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [uploading, setUploading] = useState(false);
  const [msg, setMsg] = useState('');

  const loadAlbums = () => albumsApi.myAlbums().then(r => setAlbums(r.data));
  const loadImages = (album: Album) =>
    imagesApi.albumImages(album.id).then(r => setImages(r.data)).catch(() => setImages([]));

  useEffect(() => { loadAlbums(); }, []);

  const requestAlbum = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await albumsApi.requestAlbum({ title: newTitle, description: newDesc });
      setNewTitle(''); setNewDesc('');
      setMsg('Album request submitted — waiting for supervisor approval.');
      loadAlbums();
    } catch (err: any) {
      setMsg(err.response?.data?.detail ?? 'Error creating album');
    }
  };

  const selectAlbum = (album: Album) => {
    setSelectedAlbum(album);
    loadImages(album);
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!selectedAlbum || !e.target.files?.[0]) return;
    setUploading(true);
    setMsg('');
    try {
      const result = await imagesApi.upload(selectedAlbum.id, e.target.files[0]);
      const steg = result.data.steg_result;
      if (steg?.is_suspicious) {
        setMsg('⚠️ Image flagged for steganography and sent to quarantine.');
      } else {
        setMsg('✅ Image uploaded and approved successfully.');
      }
      loadImages(selectedAlbum);
    } catch (err: any) {
      setMsg(err.response?.data?.detail ?? 'Upload failed');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const statusBadge = (s: string) => {
    const cls = s === 'APPROVED' ? 'badge-green' : s === 'REJECTED' ? 'badge-red' : 'badge-yellow';
    return <span className={`badge ${cls}`}>{s}</span>;
  };

  return (
    <div className="dashboard">
      <header className="dash-header">
        <h1>🖼️ My Gallery</h1>
        <div className="dash-user">
          <span>👤 {user?.username}</span>
          <button className="btn btn-sm" onClick={logout}>Sign Out</button>
        </div>
      </header>

      <div className="dash-grid">
        {/* Left: Albums */}
        <section className="panel">
          <h2>My Albums</h2>
          <form onSubmit={requestAlbum} className="form-inline">
            <input placeholder="Album title" value={newTitle}
              onChange={e => setNewTitle(e.target.value)} required />
            <input placeholder="Description (optional)" value={newDesc}
              onChange={e => setNewDesc(e.target.value)} />
            <button type="submit" className="btn btn-primary btn-sm">Request Album</button>
          </form>
          {msg && <p className="form-msg">{msg}</p>}
          <ul className="album-list">
            {albums.map(a => (
              <li key={a.id}
                className={`album-item ${selectedAlbum?.id === a.id ? 'active' : ''}`}
                onClick={() => selectAlbum(a)}>
                <span>{a.title}</span>{statusBadge(a.status)}
              </li>
            ))}
          </ul>
        </section>

        {/* Right: Images */}
        <section className="panel">
          {selectedAlbum ? (
            <>
              <h2>{selectedAlbum.title}</h2>
              {selectedAlbum.status === 'APPROVED' && (
                <div className="upload-area">
                  <label htmlFor="file-upload" className="btn btn-primary">
                    {uploading ? 'Uploading…' : '📤 Upload Image'}
                  </label>
                  <input id="file-upload" type="file"
                    accept="image/jpeg,image/png,image/gif,image/webp"
                    onChange={handleUpload} disabled={uploading} style={{ display: 'none' }} />
                </div>
              )}
              {selectedAlbum.status === 'PENDING' && (
                <p className="notice">⏳ Album pending supervisor approval.</p>
              )}
              <div className="image-grid">
                {images.map(img => (
                  <div key={img.id} className="image-card">
                    <img src={imagesApi.imageUrl(img.stored_filename)} alt={img.original_filename}
                      loading="lazy" />
                    <div className="image-info">
                      <span className={`badge ${img.status === 'CLEAN' || img.status === 'APPROVED_MANUAL' ? 'badge-green' : 'badge-yellow'}`}>
                        {img.status}
                      </span>
                      <span className="image-name">{img.original_filename}</span>
                    </div>
                  </div>
                ))}
                {images.length === 0 && <p className="empty">No images yet.</p>}
              </div>
            </>
          ) : (
            <p className="empty">Select an album to view or upload images.</p>
          )}
        </section>
      </div>
    </div>
  );
}
