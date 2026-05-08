import { useEffect, useState } from "react";
import { fetchPublicAlbums } from "../services/api";
import type { Album } from "../types";

export default function Gallery() {
  const [albums, setAlbums] = useState<Album[]>([]);

  useEffect(() => {
    fetchPublicAlbums().then(setAlbums).catch(() => setAlbums([]));
  }, []);

  return (
    <section className="public-band">
      <div>
        <h1>Galeria publica</h1>
        <p>Albumes aprobados con privacidad publica.</p>
      </div>
      <div className="album-grid">
        {albums.length === 0 && <p className="muted">Aun no existen albumes publicos aprobados.</p>}
        {albums.map((album) => (
          <article key={album.id} className="album-card">
            <h3>{album.title}</h3>
            <p>{album.description}</p>
            <span className="badge approved">approved</span>
          </article>
        ))}
      </div>
    </section>
  );
}
