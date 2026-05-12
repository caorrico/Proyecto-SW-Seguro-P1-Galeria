import { CheckCircle, ClipboardList, Search, ShieldAlert, Trash2, User, XCircle } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ThemeToggle from '../components/ThemeToggle';
import { useAuth } from '../context/AuthContext';
import { albumsApi, imagesApi } from '../services/api';
import type { Album, GalleryImage, StegAnalysis } from '../types';

const zoneLabels: Record<'start' | 'middle' | 'end', string> = {
  start: 'Inicio',
  middle: 'Medio',
  end: 'Final',
};

function metric(value: number | undefined, digits = 4) {
  return typeof value === 'number' ? value.toFixed(digits) : 'N/D';
}

function entropyRows(steg: StegAnalysis) {
  if (!steg.zone_analysis) return [];
  return (Object.keys(zoneLabels) as Array<keyof typeof zoneLabels>)
    .map(zone => ({ zone, data: steg.zone_analysis?.[zone] }))
    .filter((item): item is { zone: keyof typeof zoneLabels; data: NonNullable<StegAnalysis['zone_analysis']>[keyof typeof zoneLabels] } => Boolean(item.data));
}

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
      setMsg(action === 'approve' ? 'Album aprobado correctamente.' : 'Album rechazado correctamente.');
      loadPending();
    } catch { setMsg('No se pudo completar la accion.'); }
  };

  const reviewImage = async (id: number, action: 'approve' | 'reject') => {
    try {
      if (action === 'approve') await imagesApi.approveQuarantine(id);
      else await imagesApi.rejectQuarantine(id);
      setMsg(action === 'approve' ? 'Imagen aprobada manualmente.' : 'Imagen rechazada.');
      loadQuarantine();
    } catch { setMsg('No se pudo completar la accion.'); }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  return (
    <div className="dashboard">
      <header className="dash-header">
        <h1><Search size={22} /> Panel de revision</h1>
        <div className="dash-user">
          <ThemeToggle />
          <span><User size={15} /> {user?.username}</span>
          <button className="btn btn-sm" onClick={handleLogout}>Cerrar sesion</button>
        </div>
      </header>

      {msg && <p className="form-msg">{msg}</p>}

      <div className="tab-bar">
        <button className={`tab ${tab === 'albums' ? 'active' : ''}`} onClick={() => setTab('albums')}>
          <ClipboardList size={16} /> Albumes pendientes ({pendingAlbums.length})
        </button>
        <button className={`tab ${tab === 'quarantine' ? 'active' : ''}`} onClick={() => setTab('quarantine')}>
          <ShieldAlert size={16} /> Cuarentena ({quarantine.length})
        </button>
      </div>

      {tab === 'albums' && (
        <section className="panel">
          <h2>Albumes en espera de aprobacion</h2>
          {pendingAlbums.length === 0 ? <p className="empty">No hay albumes pendientes.</p> : (
            <table className="data-table">
              <thead><tr><th>Titulo</th><th>Descripcion</th><th>Solicitado</th><th>Acciones</th></tr></thead>
              <tbody>
                {pendingAlbums.map(a => (
                  <tr key={a.id}>
                    <td>{a.title}</td>
                    <td>{a.description ?? 'Sin descripcion'}</td>
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
          <h2>Imagenes en cuarentena</h2>
          {quarantine.length === 0 ? <p className="empty">La cuarentena esta vacia.</p> : (
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
                    <p className="q-filename" title={img.original_filename}>{img.original_filename}</p>
                    {img.steg_result && (
                      <div className="steg-details">
                        <p>{img.steg_result.diagnosis ?? 'Analisis automatico disponible'}</p>
                        <div className="metric-grid">
                          <span>Dimensiones</span>
                          <code>{img.steg_result.dimensions ?? 'N/D'}</code>
                          <span>Ratio LSB</span>
                          <code>{metric(img.steg_result.lsb_ratio, 6)}</code>
                          <span>Dif. histograma</span>
                          <code>{metric(img.steg_result.histogram_pair_diff)}</code>
                        </div>
                        {entropyRows(img.steg_result).length > 0 && (
                          <div className="entropy-table" aria-label="Metricas de entropia">
                            <div className="entropy-row entropy-head">
                              <span>Zona</span><span>E1</span><span>E2</span><span>R1</span><span>R2</span>
                            </div>
                            {entropyRows(img.steg_result).map(({ zone, data }) => (
                              <div className="entropy-row" key={zone}>
                                <span>{zoneLabels[zone]}</span>
                                <code>{metric(data.e1)}</code>
                                <code>{metric(data.e2)}</code>
                                <code>{metric(data.r1)}</code>
                                <code>{metric(data.r2)}</code>
                              </div>
                            ))}
                          </div>
                        )}
                        <div className="steg-flags">
                          {img.steg_result.lsb_suspicious && <span className="flag">LSB</span>}
                          {img.steg_result.histogram_suspicious && <span className="flag">Histograma</span>}
                          {img.steg_result.entropy_suspicious && <span className="flag">Entropia</span>}
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
