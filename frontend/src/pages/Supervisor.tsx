import { CheckCircle, ClipboardList, Search, ShieldAlert, Trash2, User, XCircle } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ThemeToggle from '../components/ThemeToggle';
import { useAuth } from '../context/AuthContext';
import { albumsApi, imagesApi } from '../services/api';
import type { Album, GalleryImage } from '../types';

export default function Supervisor() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [tab, setTab] = useState<'albums' | 'quarantine'>('albums');
  const [pendingAlbums, setPendingAlbums] = useState<Album[]>([]);
  const [quarantine, setQuarantine] = useState<GalleryImage[]>([]);
  const [previewUrls, setPreviewUrls] = useState<Record<number, string>>({});
  const [msg, setMsg] = useState('');

  const loadPending = () => albumsApi.pendingAlbums().then(r => setPendingAlbums(r.data)).catch(() => {});
  const loadQuarantine = () => imagesApi.quarantine().then(async r => {
    setQuarantine(r.data);
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
  }).catch(() => {});

  useEffect(() => { loadPending(); loadQuarantine(); }, []);

  const reviewAlbum = async (id: number, action: 'approve' | 'reject') => {
    try {
      await albumsApi.reviewAlbum(id, action);
      setMsg(action === 'approve' ? 'Álbum aprobado correctamente.' : 'Álbum rechazado correctamente.');
      loadPending();
    } catch { setMsg('No se pudo completar la acción.'); }
  };

  const reviewImage = async (id: number, action: 'approve' | 'reject') => {
    try {
      if (action === 'approve') await imagesApi.approveQuarantine(id);
      else await imagesApi.rejectQuarantine(id);
      setMsg(action === 'approve' ? 'Imagen aprobada manualmente.' : 'Imagen rechazada.');
      loadQuarantine();
    } catch { setMsg('No se pudo completar la acción.'); }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  return (
    <div className="dashboard">
      <header className="dash-header">
        <h1><Search size={22} /> Panel de revisión</h1>
        <div className="dash-user">
          <ThemeToggle />
          <span><User size={15} /> {user?.username}</span>
          <button className="btn btn-sm" onClick={handleLogout}>Cerrar sesión</button>
        </div>
      </header>

      {msg && <p className="form-msg">{msg}</p>}

      <div className="tab-bar">
        <button className={`tab ${tab === 'albums' ? 'active' : ''}`} onClick={() => setTab('albums')}>
          <ClipboardList size={16} /> Álbumes pendientes ({pendingAlbums.length})
        </button>
        <button className={`tab ${tab === 'quarantine' ? 'active' : ''}`} onClick={() => setTab('quarantine')}>
          <ShieldAlert size={16} /> Cuarentena ({quarantine.length})
        </button>
      </div>

      {tab === 'albums' && (
        <section className="panel">
          <h2>Álbumes en espera de aprobación</h2>
          {pendingAlbums.length === 0 ? <p className="empty">No hay álbumes pendientes.</p> : (
            <table className="data-table">
              <thead><tr><th>Título</th><th>Descripción</th><th>Solicitado</th><th>Acciones</th></tr></thead>
              <tbody>
                {pendingAlbums.map(a => (
                  <tr key={a.id}>
                    <td>{a.title}</td>
                    <td>{a.description ?? 'Sin descripción'}</td>
                    <td>{new Date(a.created_at).toLocaleDateString('es-EC')}</td>
                    <td className="action-cell">
                      <button className="btn btn-green btn-sm" onClick={() => reviewAlbum(a.id, 'approve')}><CheckCircle size={15} /> Aprobar</button>
                      <button className="btn btn-red btn-sm" onClick={() => reviewAlbum(a.id, 'reject')}><XCircle size={15} /> Rechazar</button>
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
          <h2>Imágenes en cuarentena</h2>
          {quarantine.length === 0 ? <p className="empty">La cuarentena está vacía.</p> : (
            <div className="quarantine-grid">
              {quarantine.map(img => (
                <div key={img.id} className="quarantine-card">
                  <div className="preview-container">
                    <img
                      src={previewUrls[img.id] ?? imagesApi.imageUrl(img.stored_filename)}
                      alt="Vista previa en cuarentena"
                      onError={(e) => (e.currentTarget.src = 'https://placehold.co/400x300/1e293b/64748b?text=Sin+vista+previa')}
                    />
                    <div className="quarantine-label">ARCHIVO SOSPECHOSO</div>
                  </div>
                  <div className="q-info">
                    <p className="q-filename">{img.original_filename}</p>
                    {img.steg_result && (
                      <div className="steg-details">
                        <p>{img.steg_result.diagnosis ?? 'Análisis automático disponible'}</p>
                        {img.steg_result.lsb_ratio !== undefined && (
                          <p>Relación LSB: <code>{img.steg_result.lsb_ratio}</code></p>
                        )}
                        <div className="steg-flags">
                          {img.steg_result.lsb_suspicious && <span className="flag">LSB</span>}
                          {img.steg_result.histogram_suspicious && <span className="flag">Histograma</span>}
                          {img.steg_result.entropy_suspicious && <span className="flag">Entropía</span>}
                        </div>
                      </div>
                    )}
                    <div className="action-cell">
                      <button className="btn btn-green btn-sm" onClick={() => reviewImage(img.id, 'approve')}>
                        <CheckCircle size={15} /> Aprobar manualmente
                      </button>
                      <button className="btn btn-red btn-sm" onClick={() => reviewImage(img.id, 'reject')}>
                        <Trash2 size={15} /> Rechazar
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
