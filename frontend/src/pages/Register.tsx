import { CheckCircle2, Circle, ShieldCheck } from 'lucide-react';
import { useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import ThemeToggle from '../components/ThemeToggle';
import { authApi, getApiErrorMessage } from '../services/api';

const passwordChecks = [
  { id: 'length', label: 'Mínimo 8 caracteres', test: (value: string) => value.length >= 8 },
  { id: 'lower', label: 'Una letra minúscula', test: (value: string) => /[a-z]/.test(value) },
  { id: 'upper', label: 'Una letra mayúscula', test: (value: string) => /[A-Z]/.test(value) },
  { id: 'number', label: 'Un número', test: (value: string) => /\d/.test(value) },
  { id: 'symbol', label: 'Un símbolo permitido', test: (value: string) => /[@$!%*?&._\-+]/.test(value) },
];

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: '', email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const passwordStatus = useMemo(
    () => passwordChecks.map(check => ({ ...check, valid: check.test(form.password) })),
    [form.password],
  );
  const passwordIsValid = passwordStatus.every(check => check.valid);
  const showPasswordHelp = form.password.length > 0;

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setError('');
    setForm(f => ({ ...f, [k]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!passwordIsValid) {
      setError('La contraseña todavía no cumple todos los requisitos.');
      return;
    }

    setLoading(true);
    try {
      await authApi.register(form);
      navigate('/login?registered=1');
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, 'No se pudo completar el registro. Inténtalo nuevamente.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-theme"><ThemeToggle /></div>
      <div className="auth-card">
        <div className="auth-logo"><ShieldCheck size={42} /></div>
        <h1>Crear cuenta</h1>
        <p className="auth-subtitle">Únete a SecureFrame Gallery</p>
        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="reg-username">Usuario</label>
            <input id="reg-username" type="text" value={form.username}
              onChange={set('username')} required minLength={3} maxLength={50} />
          </div>
          <div className="form-group">
            <label htmlFor="reg-email">Correo electrónico</label>
            <input id="reg-email" type="email" value={form.email}
              onChange={set('email')} required />
          </div>
          <div className="form-group">
            <label htmlFor="reg-password">Contraseña</label>
            <input id="reg-password" type="password" value={form.password}
              onChange={set('password')} required minLength={8}
              aria-describedby="password-help"
              placeholder="Ejemplo: Segura123!" />
            {showPasswordHelp && (
              <div id="password-help" className="password-rules" aria-live="polite">
                {passwordStatus.map(check => (
                  <div key={check.id} className={`password-rule ${check.valid ? 'valid' : ''}`}>
                    {check.valid ? <CheckCircle2 size={15} /> : <Circle size={15} />}
                    <span>{check.label}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
          {error && <p className="form-error">{error}</p>}
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Creando cuenta...' : 'Crear cuenta'}
          </button>
        </form>
        <p className="auth-link">¿Ya tienes una cuenta? <Link to="/login">Inicia sesión</Link></p>
      </div>
    </div>
  );
}
