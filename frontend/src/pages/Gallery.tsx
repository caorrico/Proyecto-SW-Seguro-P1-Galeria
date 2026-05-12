import { ExternalLink, Folder, ImageIcon, ShieldCheck } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import ThemeToggle from '../components/ThemeToggle';
import { useAuth } from '../context/AuthContext';
import { albumsApi, imagesApi } from '../services/api';
import type { Album, GalleryImage } from '../types';

const isPublicApprovedAlbum = (album: Album) =>
  album.privacy.toLowerCase() === 'public' && album.status.toLowerCase() === 'approved';

export default function Gallery() {
  const { isAuthenticated, user, logout } = useAuth();
  const navigate = useNavigate();
  const [albums, setAlbums] = useState<Album[]>([]);
  const [selected, setSelected] = useState<Album | null>(null);
  const [images, setImages] = useState<GalleryImage[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    albumsApi.publicAlbums()
      .then(r => setAlbums(r.data.filter(isPublicApprovedAlbum)))
      .finally(() => setLoading(false));
  }, []);

  const selectAlbum = (album: Album) => {
    if (!isPublicApprovedAlbum(album)) {
      setSelected(null);
      setImages([]);
      return;
    }
    setSelected(album);
    imagesApi.publicAlbumImages(album.id).then(r => setImages(r.data)).catch(() => setImages([]));
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  return (
    <div className="gallery-page">
      <header className="gallery-header">
        <div className="gallery-brand">
          <span className="gallery-icon"><ShieldCheck size={24} /></span>
          <h1>SecureFrame Gallery</h1>
        </div>
        <nav className="gallery-nav">
          <ThemeToggle />
          {isAuthenticated ? (
            <>
              <Link to="/dashboard" className="btn btn-outline">Mi galería</Link>
              <span className="nav-user">{user?.username}</span>
              <button className="btn btn-sm" onClick={handleLogout}>Cerrar sesión</button>
            </>
          ) : (
            <>
              <Link to="/login" className="btn btn-outline">Iniciar sesión</Link>
              <Link to="/register" className="btn btn-primary">Registrarse</Link>
            </>
          )}
        </nav>
      </header>

      <main className="gallery-main">
        {loading ? (
          <p className="loading">Cargando galerías...</p>
        ) : albums.length === 0 ? (
          <div className="empty-state">
            <ImageIcon size={40} />
            <p>No hay galerías públicas disponibles.</p>
            <Link to="/register" className="btn btn-primary">Crear una cuenta</Link>
          </div>
        ) : (
          <div className="gallery-layout">
            <aside className="album-sidebar">
              <h2>Álbumes</h2>
              {albums.map(a => (
                <button key={a.id}
                  className={`album-tab ${selected?.id === a.id ? 'active' : ''}`}
                  onClick={() => selectAlbum(a)}>
                  <Folder size={15} /> {a.title}
                </button>
              ))}
            </aside>

            <section className="image-section">
              {selected ? (
                <>
                  <h2>{selected.title}</h2>
                  {selected.description && <p className="album-desc">{selected.description}</p>}
                  <div className="image-grid">
                    {images.map(img => (
                      <div key={img.id} className="image-card">
                        <a
                          className="image-preview-link"
                          href={imagesApi.imageUrl(img.stored_filename)}
                          target="_blank"
                          rel="noopener noreferrer"
                          title={`Abrir ${img.original_filename}`}
                        >
                          <img
                            src={imagesApi.imageUrl(img.stored_filename)}
                            alt={img.original_filename}
                            loading="lazy"
                          />
                        </a>
                        <div className="image-info">
                          <span className="image-name" title={img.original_filename}>{img.original_filename}</span>
                          <a
                            className="btn btn-outline btn-icon"
                            href={imagesApi.imageUrl(img.stored_filename)}
                            target="_blank"
                            rel="noopener noreferrer"
                            title="Abrir imagen"
                            aria-label="Abrir imagen"
                          >
                            <ExternalLink size={15} />
                          </a>
                        </div>
                      </div>
                    ))}
                    {images.length === 0 && <p className="empty">Este álbum no tiene imágenes publicadas.</p>}
                  </div>
                </>
              ) : (
                <p className="empty">Selecciona un álbum para ver sus imágenes.</p>
              )}
            </section>
          </div>
        )}
      </main>
    </div>
  );
}
