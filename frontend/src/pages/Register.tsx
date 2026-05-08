import { FormEvent, useState } from "react";
import { UserPlus } from "lucide-react";
import { register } from "../services/api";

const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&._\-+])[A-Za-z\d@$!%*?&._\-+]{8,}$/;

export default function Register() {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");

  const isPasswordValid = passwordRegex.test(password);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setMessage("");

    if (!isPasswordValid) {
      setMessage("La contraseña no cumple con las políticas de seguridad.");
      return;
    }

    try {
      await register(username, email, password);
      setMessage("Usuario registrado. Ya puedes iniciar sesion.");
      setUsername("");
      setEmail("");
      setPassword("");
    } catch {
      setMessage("No se pudo registrar el usuario. Comprueba tus datos.");
    }
  }

  return (
    <section className="panel">
      <h2>Registro</h2>
      <form onSubmit={handleSubmit} className="stack">
        <label>Usuario<input value={username} onChange={(event) => setUsername(event.target.value)} required minLength={3} /></label>
        <label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label>
        <label>
          Contraseña
          <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required />
        </label>
        <div style={{ fontSize: "0.85rem", color: isPasswordValid ? "green" : "gray" }}>
          Requisitos de contraseña: al menos 8 caracteres, 1 mayúscula, 1 minúscula, 1 número y 1 carácter especial.
        </div>
        <button type="submit" disabled={!isPasswordValid || !username || !email}>
          <UserPlus size={16} /> Crear cuenta
        </button>
        {message && <p>{message}</p>}
      </form>
    </section>
  );
}
