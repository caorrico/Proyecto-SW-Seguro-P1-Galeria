# SecureFrame Gallery

SecureFrame Gallery es una aplicacion web segura para gestionar una galeria publica de imagenes con registro, autenticacion, solicitudes de albumes, subida controlada de imagenes, analisis de esteganografia, cuarentena y revision manual por supervisor.

Proyecto academico de Desarrollo de Software Seguro de la Universidad de las Fuerzas Armadas ESPE.

## Objetivo

Construir una galeria multimedia resiliente donde solo se publica contenido aprobado y saneado. El sistema aplica controles de autenticacion, RBAC, validacion server-side, almacenamiento separado por buckets, cabeceras de seguridad y trazabilidad de decisiones de revision.

## Arquitectura

- Backend: FastAPI, SQLAlchemy, Pydantic, JWT, Argon2, SlowAPI.
- Frontend: React, TypeScript, Vite, React Router, Axios.
- Base de datos: SQLite para desarrollo rapido o PostgreSQL via Docker Compose.
- Archivos: MinIO con buckets separados para cuarentena, galeria publica y evidencia rechazada.
- Seguridad: validacion de entrada, re-encoding de imagenes con Pillow, analisis LSB/entropia/EOF, RBAC y cabeceras HTTP.

## Estructura

- `backend/app/main.py`: aplicacion FastAPI, CORS, rate limiting y routers.
- `backend/app/routers`: autenticacion, albumes, imagenes y cuarentena.
- `backend/app/services`: hashing/JWT, procesamiento de imagenes, esteganografia y MinIO.
- `backend/app/models`: modelos SQLAlchemy.
- `backend/app/schemas`: contratos Pydantic.
- `frontend/src/pages`: galeria publica, login, registro, dashboard y panel supervisor.
- `frontend/src/services/api.ts`: cliente API usado por el frontend.
- `database/init`: esquema SQL inicial para PostgreSQL.
- `docs/latex`: informe tecnico modular en LaTeX.

## Modulos Funcionales

- Registro e inicio de sesion con contrasenas robustas, Argon2 y bloqueo temporal por intentos fallidos.
- Solicitud de albumes por usuarios autenticados.
- Aprobacion o rechazo de albumes por supervisor o administrador.
- Subida de imagenes solo en albumes aprobados y propios.
- Validacion por magic bytes, tamano maximo, re-encoding y eliminacion de metadatos.
- Analisis de esteganografia por LSB, histograma, entropia y datos posteriores al EOF.
- Cuarentena para imagenes sospechosas y aprobacion/rechazo manual.
- Galeria publica que lista solo albumes publicos aprobados e imagenes limpias o aprobadas manualmente.

## Roles

- Visitante: consulta la galeria publica.
- Usuario: solicita albumes y sube imagenes a albumes aprobados propios.
- Supervisor: revisa solicitudes de albumes e imagenes en cuarentena.
- Administrador: rol soportado por RBAC para privilegios equivalentes a supervisor.

## Seguridad Implementada

- SQL Injection: uso de SQLAlchemy ORM y filtros parametrizados.
- XSS: validacion de titulo, descripcion y razones de rechazo; React escapa texto por defecto.
- Path Traversal: nombres almacenados generados con UUID y extension detectada.
- Subida segura: limite de 10 MB, magic bytes, formatos permitidos, Pillow verify y re-encoding.
- Metadatos: re-encoding para no preservar EXIF.
- RBAC: dependencias `get_current_user`, `get_optional_current_user` y `require_supervisor`.
- Rate limiting: login, registro y subida de imagenes.
- Sesiones: JWT de acceso con expiracion, refresh token HttpOnly con JTI y rotacion.
- Cabeceras: CSP, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy` y HSTS solo bajo HTTPS.
- CORS: restringido por `FRONTEND_ORIGIN`.

## Variables de Entorno

Copia `.env.example` a `.env` o `backend/.env` y ajusta valores:

```env
DATABASE_URL=sqlite:///./secureframe.db
SECRET_KEY=change-this-development-secret-before-production
FRONTEND_ORIGIN=http://localhost:5173
MINIO_URL=localhost:9393
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=change-this-minio-secret
VITE_API_URL=http://localhost:8000/api
```

No uses los valores de ejemplo en produccion.

## Instalacion Backend

Instala Python 3.11+ y luego:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Con WSL/Linux:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Instalacion Frontend

Instala Node.js LTS 20+ y luego:

```powershell
cd frontend
npm install
```

## Base de Datos e Infraestructura

Para PostgreSQL + MinIO:

```powershell
docker compose up -d
```

El backend tambien puede iniciar con SQLite usando `DATABASE_URL=sqlite:///./secureframe.db`.

## Ejecucion en Desarrollo

Backend:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```powershell
cd frontend
npm run dev
```

Script integrado:

```powershell
.\start_all.ps1
```

## Produccion

- Usar HTTPS y un `SECRET_KEY` aleatorio fuerte.
- Configurar `secure=True` en cookies si se despliega solo bajo HTTPS.
- Restringir CORS al dominio final.
- Usar PostgreSQL gestionado y MinIO/S3 con politicas privadas.
- Ejecutar `npm run build` y servir `frontend/dist` desde un servidor estatico.

## Credenciales Demo

El proyecto puede crear un usuario supervisor demo:

- Usuario: `admin`
- Contrasena: `admin123`

Estas credenciales son solo para laboratorio academico. Cambialas o deshabilita el seed antes de produccion.

## Endpoints Principales

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `POST /api/albums/request`
- `GET /api/albums/my`
- `GET /api/albums/public`
- `GET /api/albums/pending`
- `PATCH /api/albums/{album_id}/review`
- `POST /api/albums/{album_id}/images`
- `GET /api/albums/{album_id}/images`
- `GET /api/images/{stored_filename}`
- `GET /api/images/url/{image_id}`
- `GET /api/quarantine`
- `PATCH /api/quarantine/{image_id}/approve`
- `PATCH /api/quarantine/{image_id}/reject`

## Flujo General

1. El usuario se registra e inicia sesion.
2. Solicita un album con titulo, descripcion y privacidad.
3. Supervisor aprueba o rechaza la solicitud.
4. El usuario sube imagenes solo si el album esta aprobado.
5. El backend valida, sanea y analiza la imagen.
6. Imagen limpia: se promueve al bucket publico y queda visible.
7. Imagen sospechosa: queda en cuarentena.
8. Supervisor aprueba manualmente o rechaza y mueve a evidencia.
9. Visitantes ven solo albumes publicos aprobados e imagenes limpias.

## Limitaciones Conocidas

- El access token se guarda en `localStorage`; el refresh token HttpOnly reduce riesgo, pero una mejora futura seria mover el acceso a cookies HttpOnly o memoria.
- La deteccion de esteganografia es heuristica y no sustituye un motor forense especializado.
- La blocklist de logout para access tokens es en memoria; en produccion debe migrarse a Redis o base de datos con TTL.
- La maquina local analizada no tenia `python`, `py`, `node` ni `npm` en PATH, por lo que la instalacion no pudo ejecutarse desde esta terminal.

## Trabajo Futuro

- Pruebas automatizadas de API y E2E.
- Migraciones Alembic versionadas.
- Panel administrativo completo para gestion de usuarios.
- Politicas CSP por entorno y despliegue HTTPS.
- Integracion con SCA/SAST en CI.

## Autores

- Cesar Loor
- Gabriel Murillo
- Camilo Orrico

Docente: Ing. Geovanny Cudco.
