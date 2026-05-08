# 🛡️ SecureFrame Gallery

> **Proyecto Integrador P1 — Desarrollo Seguro 2026-50**
> Galería web segura con detección de esteganografía en imágenes.

## 🚀 Stack Tecnológico

| Capa | Tecnología |
|---|---|
| **Backend** | Python 3.12 + FastAPI + SQLAlchemy |
| **Base de datos** | PostgreSQL 16 (Docker) |
| **Auth** | Argon2id + JWT |
| **Esteganografía** | NumPy + Pillow (análisis LSB + histograma + entropía) |
| **Frontend** | React 18 + TypeScript + Vite |

---

## 🔑 Credenciales de Prueba

Estas cuentas se crean automáticamente al arrancar el backend por primera vez.

| Rol | Username | Password | Acceso |
|---|---|---|---|
| **Supervisor** | `supervisor` | `Sup3rv!s0r#2026` | Panel cuarentena + aprobar/rechazar álbumes |
| **Usuario** | `demo_user` | `DemoUs3r!2026` | Solicitar álbumes + subir imágenes |

> **Nota:** Para la defensa, el supervisor puede aprobar el álbum del usuario demo y luego subir imágenes para mostrar el flujo completo de esteganografía.

---

## ⚡ Levantar el Proyecto Localmente

### 1. Requisitos previos
- Python 3.12+
- Node.js 18+
- Docker Desktop

### 2. Base de datos (PostgreSQL en Docker)

```bash
docker compose up -d
```

### 3. Backend (FastAPI)

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- API docs: **http://localhost:8000/api/docs**
- Health check: **http://localhost:8000/api/health**

### 4. Frontend (React + Vite)

```bash
cd frontend
npm install
node_modules\.bin\vite.cmd      # Windows PowerShell
# ó: npx --yes vite             # alternativa
```

- App: **http://localhost:5173**

---

## 🔒 Controles de Seguridad Implementados

| Control | Implementación |
|---|---|
| **Hashing de contraseñas** | Argon2id (time_cost=2, memory=64MB) |
| **Autenticación** | JWT con expiración (60 min) |
| **Anti-enumeración** | Respuesta genérica en login + dummy hash timing |
| **Rate Limiting** | slowapi — 5 intentos/min por IP en `/auth/login` |
| **Validación MIME** | Magic bytes (no extensión) vía Pillow |
| **Strip EXIF** | Re-encoding Pillow — elimina metadatos de geolocalización |
| **Prevención Path Traversal** | Validación de filename + nombres UUID |
| **Security Headers** | CSP, nosniff, HSTS, X-Frame-Options, Permissions-Policy |
| **RBAC** | 3 roles: visitor / user / supervisor |
| **Sanitización XSS** | bleach en inputs de texto (título y descripción) |
| **SQL Injection** | SQLAlchemy ORM con prepared statements |

---

## 🔬 Módulo de Esteganografía

El análisis se ejecuta automáticamente en cada imagen subida. Combina tres métodos:

1. **LSB Ratio (NumPy):** Si `|ratio - 0.5| < 0.015`, la distribución es sospechosamente uniforme
2. **Histograma (par diff):** Si la diferencia entre pares de valores adyacentes `(2k, 2k+1)` es < 5%
3. **Entropía por zonas:** Analiza inicio, mitad y fin de la imagen — entropía > 7.9 bits = sospechoso

**Limitaciones documentadas:** No detecta esteganografía de dominio de frecuencia (DCT, wavelet). Pueden ocurrir falsos positivos en imágenes con alto ruido natural.

---

## 📁 Estructura del Proyecto

```
Proyecto-SW-Seguro-P1-Galeria/
├── backend/
│   ├── app/
│   │   ├── main.py               # Entry point + seeder
│   │   ├── config.py             # pydantic-settings
│   │   ├── database.py           # SQLAlchemy + init_db
│   │   ├── models/               # User, Album, Image
│   │   ├── routers/              # auth, albums, images (+ quarantine)
│   │   ├── services/             # auth_service, steg_analyzer, image_processor
│   │   ├── schemas/              # Pydantic validators
│   │   └── middleware/           # SecurityHeaders, RateLimiter
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   └── src/
│       ├── pages/                # Gallery, Login, Register, Dashboard, Supervisor
│       ├── context/              # AuthContext (useReducer + JWT)
│       ├── services/             # api.ts (Axios + interceptors)
│       └── types/                # Interfaces TypeScript
├── docker-compose.yml            # PostgreSQL 16
└── readme.md
```

---

## 🌐 Variables de Entorno

Copiar `backend/.env.example` → `backend/.env` y ajustar:

```env
DATABASE_URL=postgresql://secureframe:secureframe_dev_2026@localhost:5432/secureframe_db
SECRET_KEY=<generar con: python -c "import secrets; print(secrets.token_hex(32))">
```

---

## 📚 Referencias

- [OWASP ASVS v4.0](https://owasp.org/www-project-application-security-verification-standard/)
- [NIST SP 800-218 (SSDF)](https://csrc.nist.gov/publications/detail/sp/800-218/final)
- [OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
- [argon2-cffi](https://argon2-cffi.readthedocs.io/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)