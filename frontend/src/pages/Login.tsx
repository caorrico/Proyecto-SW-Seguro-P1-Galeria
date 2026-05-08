import { FormEvent, useState } from "react";
import { LogIn } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setMessage("");
    try {
      await login(username, password);
    } catch {
      setMessage("Credenciales invalidas o servidor no disponible.");
    }
  }

  return (
    <section className="panel">
      <h2>Ingreso</h2>
      <form onSubmit={handleSubmit} className="stack">
        <label>Usuario<input value={username} onChange={(event) => setUsername(event.target.value)} /></label>
        <label>Contrasena<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} /></label>
        <button type="submit"><LogIn size={16} /> Iniciar sesion</button>
        {message && <p className="error">{message}</p>}
      </form>
    </section>
  );
}
