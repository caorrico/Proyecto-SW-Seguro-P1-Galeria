import { useEffect, useState } from "react";
import { Check, X } from "lucide-react";
import { approveAlbum, fetchSupervisorAlbums, rejectAlbum } from "../services/api";
import type { Album, AlbumStatus } from "../types";

const statuses: AlbumStatus[] = ["pending", "approved", "rejected"];

export default function Supervisor() {
  const [status, setStatus] = useState<AlbumStatus>("pending");
  const [albums, setAlbums] = useState<Album[]>([]);
  const [reason, setReason] = useState<Record<number, string>>({});
  const [message, setMessage] = useState("");

  async function loadAlbums(selected = status) {
    setAlbums(await fetchSupervisorAlbums(selected));
  }

  useEffect(() => {
    loadAlbums(status).catch(() => setMessage("No se pudieron cargar solicitudes."));
  }, [status]);

  async function review(albumId: number, action: "approve" | "reject") {
    setMessage("");
    try {
      if (action === "approve") {
        await approveAlbum(albumId);
      } else {
        await rejectAlbum(albumId, reason[albumId]);
      }
      await loadAlbums();
    } catch {
      setMessage("No se pudo revisar la solicitud.");
    }
  }

  return (
    <section className="panel">
      <div className="panel-title">
        <h2>Revision de albumes</h2>
        <div className="segmented">
          {statuses.map((item) => (
            <button type="button" className={status === item ? "active" : ""} onClick={() => setStatus(item)} key={item}>
              {item}
            </button>
          ))}
        </div>
      </div>
      {message && <p className="error">{message}</p>}
      <div className="album-grid">
        {albums.map((album) => (
          <article className="album-card" key={album.id}>
            <h3>{album.title}</h3>
            <p>{album.description}</p>
            <span className={`badge ${album.status}`}>{album.status}</span>
            {album.status === "pending" && (
              <div className="review-actions">
                <input
                  placeholder="Motivo de rechazo opcional"
                  value={reason[album.id] ?? ""}
                  onChange={(event) => setReason((current) => ({ ...current, [album.id]: event.target.value }))}
                />
                <button type="button" onClick={() => review(album.id, "approve")}><Check size={16} /> Aprobar</button>
                <button type="button" className="danger" onClick={() => review(album.id, "reject")}><X size={16} /> Rechazar</button>
              </div>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}
