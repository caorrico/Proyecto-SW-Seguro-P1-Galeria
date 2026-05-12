import { ExternalLink, Eye, Globe2, ImageIcon, LayoutDashboard, Lock, Search, Trash2, Upload, User } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import ThemeToggle from '../components/ThemeToggle';
import { useAuth } from '../context/AuthContext';
import { albumsApi, getApiErrorMessage, imagesApi } from '../services/api';
import type { Album, GalleryImage } from '../types';

const albumStatusLabels: Record<string, string> = {
  pending: 'Pendiente',
  approved: 'Aprobado',
  rejected: 'Rechazado',
};

const imageStatusLabels: Record<string, string> = {
  CLEAN: 'Limpia',
  SUSPICIOUS: 'Sospechosa',
  APPROVED_MANUAL: 'Aprobada manualmente',
  REJECTED: 'Rechazada',
};

const privacyLabels: Record<string, string> = {
  public: 'Público',
  private: 'Privado',
};

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [albums, setAlbums] = useState<Album[]>([]);
  const [selectedAlbum, setSelectedAlbum] = useState<Album | null>(null);
  const [images, setImages] = useState<GalleryImage[]>([]);
  const [previewUrls, setPreviewUrls] = useState<Record<number, string>>({});
  const [newTitle, setNewTitle] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newPrivacy, setNewPrivacy] = useState<'public' | 'private'>('public');
  const [uploading, setUploading] = useState(false);
  const [msg, setMsg] = useState('');

  const loadAlbums = () => albumsApi.myAlbums().then(r => setAlbums(r.data));
  const loadImages = (album: Album) =>
    imagesApi.albumImages(album.id).then(async r => {
      setImages(r.data);
      const entries = await Promise.all(
        r.data.map(async img => {
          try {
            const res = await imagesApi.presignedUrl(img.id);
            return [img.id, res.data.url] as const;
          } catch {
            return [img.id, imagesApi.imageUrl(img.stored_filename)] as const;
          }
        }),
      );
      setPreviewUrls(Object.fromEntries(entries));
    }).catch(() => {
      setImages([]);
      setPreviewUrls({});
    });

  useEffect(() => { loadAlbums(); }, []);

  const requestAlbum = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await albumsApi.requestAlbum({ title: newTitle, description: newDesc, privacy: newPrivacy });
      setNewTitle('');
      setNewDesc('');
      setNewPrivacy('public');
      setMsg('Solicitud de álbum enviada. Espera la revisión del supervisor.');
      loadAlbums();
    } catch (err: unknown) {
      setMsg(getApiErrorMessage(err, 'No se pudo crear la solicitud de álbum.'));
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
      setMsg(
        steg?.is_suspicious
          ? 'La imagen fue marcada como sospechosa y enviada a cuarentena.'
          : 'Imagen cargada, analizada y aprobada correctamente.',
      );
      loadImages(selectedAlbum);
    } catch (err: unknown) {
      setMsg(getApiErrorMessage(err, 'No se pudo subir la imagen.'));
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleDelete = async (albumId: number, imageId: number) => {
    if (!window.confirm('¿Seguro que deseas eliminar este archivo?')) return;
    try {
      await imagesApi.deleteImage(albumId, imageId);
      if (selectedAlbum) loadImages(selectedAlbum);
    } catch (err: unknown) {
      setMsg(getApiErrorMessage(err, 'No se pudo eliminar la imagen.'));
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  const statusBadge = (s: string) => {
    const status = s.toLowerCase();
    const cls = status === 'approved' ? 'badge-green' : status === 'rejected' ? 'badge-red' : 'badge-yellow';
    return <span className={`badge ${cls}`}>{albumStatusLabels[status] ?? s}</span>;
  };

  const privacyBadge = (privacy: string) => {
    const normalized = privacy.toLowerCase();
    const icon = normalized === 'public' ? <Globe2 size={13} /> : <Lock size={13} />;
    return <span className="badge badge-muted">{icon}{privacyLabels[normalized] ?? privacy}</span>;
  };

  return (
    <div className="dashboard">
      <header className="dash-header">
        <h1><LayoutDashboard size={22} /> Mi galería</h1>
        <div className="dash-user">
          <ThemeToggle />
          <Link to="/" className="btn btn-outline btn-sm">
            <Globe2 size={15} /> Galería pública
          </Link>
          {(user?.role === 'supervisor' || user?.role === 'admin') && (
            <Link to="/supervisor" className="btn btn-outline btn-sm">
              <Search size={15} /> Panel de revisión
            </Link>
          )}
          <span><User size={15} /> {user?.username}</span>
          <button className="btn btn-sm" onClick={handleLogout}>Cerrar sesión</button>
        </div>
      </header>

      <div className="dash-grid">
        <section className="panel">
          <h2>Mis álbumes</h2>
          <form onSubmit={requestAlbum} className="form-inline">
            <input placeholder="Título del álbum" value={newTitle}
              onChange={e => setNewTitle(e.target.value)} required />
            <input placeholder="Descripción (opcional)" value={newDesc}
              onChange={e => setNewDesc(e.target.value)} />
            <select value={newPrivacy} onChange={e => setNewPrivacy(e.target.value as 'public' | 'private')}>
              <option value="public">Público</option>
              <option value="private">Privado</option>
            </select>
            <button type="submit" className="btn btn-primary btn-sm">Solicitar álbum</button>
          </form>
          {msg && <p className="form-msg">{msg}</p>}
          <ul className="album-list">
            {albums.map(a => (
              <li key={a.id}
                className={`album-item ${selectedAlbum?.id === a.id ? 'active' : ''}`}
                onClick={() => selectAlbum(a)}>
                <span>{a.title}</span>
                <span className="album-badges">{privacyBadge(a.privacy)}{statusBadge(a.status)}</span>
              </li>
            ))}
          </ul>
        </section>

        <section className="panel">
          {selectedAlbum ? (
            <>
              <h2>{selectedAlbum.title}</h2>
              {selectedAlbum.status.toUpperCase() === 'APPROVED' && (
                <div className="upload-area">
                  <label htmlFor="file-upload" className="btn btn-primary">
                    {uploading ? 'Subiendo...' : <><Upload size={16} /> Subir imagen</>}
                  </label>
                  <input id="file-upload" type="file"
                    accept="image/jpeg,image/png,image/gif,image/webp"
                    onChange={handleUpload} disabled={uploading} style={{ display: 'none' }} />
                </div>
              )}
              {selectedAlbum.status.toUpperCase() === 'PENDING' && (
                <p className="notice">Álbum pendiente de aprobación por el supervisor.</p>
              )}
              <div className="image-grid">
                {images.map(img => (
                  <div key={img.id} className="image-card">
                    <a
                      className="image-preview-link"
                      href={previewUrls[img.id] ?? imagesApi.imageUrl(img.stored_filename)}
                      target="_blank"
                      rel="noopener noreferrer"
                      title={`Abrir ${img.original_filename}`}
                    >
                      <img src={previewUrls[img.id] ?? imagesApi.imageUrl(img.stored_filename)} alt={img.original_filename}
                        loading="lazy" />
                    </a>
                    <div className="image-info">
                      <span className="image-name" title={img.original_filename}>{img.original_filename}</span>
                      <div className="image-actions">
                        <span className={`badge ${img.status === 'CLEAN' || img.status === 'APPROVED_MANUAL' ? 'badge-green' : 'badge-yellow'}`}>
                          {imageStatusLabels[img.status] ?? img.status}
                        </span>
                        <span className="image-buttons">
                          <a
                            className="btn btn-outline btn-icon"
                            href={previewUrls[img.id] ?? imagesApi.imageUrl(img.stored_filename)}
                            target="_blank"
                            rel="noopener noreferrer"
                            title="Abrir imagen"
                            aria-label="Abrir imagen"
                          >
                            <ExternalLink size={15} />
                          </a>
                          <button
                            className="btn btn-red btn-icon"
                            onClick={() => handleDelete(img.album_id, img.id)}
                            title="Eliminar archivo"
                            aria-label="Eliminar archivo"
                          >
                            <Trash2 size={15} />
                          </button>
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
                {images.length === 0 && <p className="empty"><ImageIcon size={28} /> No hay imágenes todavía.</p>}
              </div>
            </>
          ) : (
            <p className="empty"><Eye size={28} /> Selecciona un álbum para ver o subir imágenes.</p>
          )}
        </section>
      </div>
    </div>
  );
}
