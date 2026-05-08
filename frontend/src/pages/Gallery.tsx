import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { albumsApi, imagesApi } from '../services/api';
import type { Album, GalleryImage } from '../types';

export default function Gallery() {
  const [albums, setAlbums] = useState<Album[]>([]);
  const [selected, setSelected] = useState<Album | null>(null);
  const [images, setImages] = useState<GalleryImage[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    albumsApi.publicAlbums()
      .then(r => setAlbums(r.data))
      .finally(() => setLoading(false));
  }, []);

  const selectAlbum = (album: Album) => {
    setSelected(album);
    imagesApi.albumImages(album.id).then(r => setImages(r.data)).catch(() => setImages([]));
  };

  return (
    <div className="gallery-page">
      <header className="gallery-header">
        <div className="gallery-brand">
          <span className="gallery-icon">🛡️</span>
          <h1>SecureFrame Gallery</h1>
        </div>
        <nav className="gallery-nav">
          <Link to="/login" className="btn btn-outline">Sign In</Link>
          <Link to="/register" className="btn btn-primary">Join</Link>
        </nav>
      </header>

      <main className="gallery-main">
        {loading ? (
          <p className="loading">Loading galleries…</p>
        ) : albums.length === 0 ? (
          <div className="empty-state">
            <p>🖼️ No public galleries yet.</p>
            <Link to="/register" className="btn btn-primary">Create an account to start</Link>
          </div>
        ) : (
          <div className="gallery-layout">
            {/* Album sidebar */}
            <aside className="album-sidebar">
              <h2>Albums</h2>
              {albums.map(a => (
                <button key={a.id}
                  className={`album-tab ${selected?.id === a.id ? 'active' : ''}`}
                  onClick={() => selectAlbum(a)}>
                  📁 {a.title}
                </button>
              ))}
            </aside>

            {/* Image grid */}
            <section className="image-section">
              {selected ? (
                <>
                  <h2>{selected.title}</h2>
                  {selected.description && <p className="album-desc">{selected.description}</p>}
                  <div className="image-grid">
                    {images.map(img => (
                      <div key={img.id} className="image-card">
                        <img
                          src={`${import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api'}/images/${img.stored_filename}`}
                          alt={img.original_filename}
                          loading="lazy"
                        />
                        <p className="image-caption">{img.original_filename}</p>
                      </div>
                    ))}
                    {images.length === 0 && <p className="empty">No images in this album.</p>}
                  </div>
                </>
              ) : (
                <p className="empty">Select an album to browse images.</p>
              )}
            </section>
          </div>
        )}
      </main>
    </div>
  );
}
