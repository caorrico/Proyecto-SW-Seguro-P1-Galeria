import { FormEvent, useState } from "react";
import { UserPlus } from "lucide-react";
import { register } from "../services/api";

export default function Register() {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setMessage("");
    try {
      await register(username, email, password);
      setMessage("Usuario registrado. Ya puedes iniciar sesion.");
      setUsername("");
      setEmail("");
      setPassword("");
    } catch {
      setMessage("No se pudo registrar el usuario.");
    }
  }

  return (
    <section className="panel">
      <h2>Registro</h2>
      <form onSubmit={handleSubmit} className="stack">
        <label>Usuario<input value={username} onChange={(event) => setUsername(event.target.value)} /></label>
        <label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} /></label>
        <label>Contrasena<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} /></label>
        <button type="submit"><UserPlus size={16} /> Crear cuenta</button>
        {message && <p>{message}</p>}
      </form>
    </section>
  );
}
