import { FormEvent, useEffect, useState } from "react";
import { PlusCircle, RefreshCw } from "lucide-react";
import { fetchMyAlbums, requestAlbum } from "../services/api";
import type { Album, AlbumPrivacy } from "../types";

export default function Dashboard() {
  const [albums, setAlbums] = useState<Album[]>([]);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [privacy, setPrivacy] = useState<AlbumPrivacy>("private");
  const [message, setMessage] = useState("");

  async function loadAlbums() {
    const data = await fetchMyAlbums();
    setAlbums(data);
  }

  useEffect(() => {
    loadAlbums().catch(() => setMessage("No se pudieron cargar tus solicitudes."));
  }, []);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setMessage("");
    if (title.trim().length < 3 || description.trim().length === 0) {
      setMessage("Completa titulo y descripcion con valores validos.");
      return;
    }
    try {
      await requestAlbum({ title, description, privacy });
      setTitle("");
      setDescription("");
      setPrivacy("private");
      setMessage("Solicitud enviada con estado pending.");
      await loadAlbums();
    } catch (error) {
      setMessage("La solicitud fue rechazada por validacion o permisos.");
    }
  }

  return (
    <section className="work-area">
      <div className="panel">
        <h2>Solicitud de album</h2>
        <form onSubmit={handleSubmit} className="stack">
          <label>Titulo<input maxLength={100} value={title} onChange={(event) => setTitle(event.target.value)} /></label>
          <label>Descripcion<textarea maxLength={1000} value={description} onChange={(event) => setDescription(event.target.value)} /></label>
          <label>Privacidad
            <select value={privacy} onChange={(event) => setPrivacy(event.target.value as AlbumPrivacy)}>
              <option value="private">private</option>
              <option value="public">public</option>
            </select>
          </label>
          <button type="submit"><PlusCircle size={16} /> Solicitar album</button>
          {message && <p>{message}</p>}
        </form>
      </div>

      <div className="panel wide">
        <div className="panel-title">
          <h2>Mis solicitudes</h2>
          <button type="button" onClick={() => loadAlbums()}><RefreshCw size={16} /> Actualizar</button>
        </div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Titulo</th><th>Privacidad</th><th>Estado</th><th>Motivo</th></tr></thead>
            <tbody>
              {albums.map((album) => (
                <tr key={album.id}>
                  <td>{album.title}</td>
                  <td>{album.privacy}</td>
                  <td><span className={`badge ${album.status}`}>{album.status}</span></td>
                  <td>{album.rejection_reason ?? ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
