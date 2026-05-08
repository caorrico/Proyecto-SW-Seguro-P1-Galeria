Bienvenido al respositorio

# SecureFrame Gallery

## RF02 - Gestion de Albumes

### Objetivo funcional

RF02 implementa la gestion de solicitudes de albumes para usuarios autenticados. Un usuario puede solicitar un album indicando titulo, descripcion y privacidad inicial. La solicitud queda en estado `pending` y solo un usuario con rol `supervisor` o `admin` puede aprobarla o rechazarla.

El alcance de este trabajo se limito a albumes y a la validacion minima de RF03 que impide subir imagenes a albumes no aprobados. No se implemento el flujo completo de RF03 ni RF04.

### Modelo de datos de Album

| Campo | Tipo | Descripcion |
| --- | --- | --- |
| `id` | entero | Identificador del album. |
| `title` | string, maximo 100 | Titulo validado como texto plano. |
| `description` | texto, maximo 1000 | Descripcion validada como texto plano. |
| `privacy` | `public` o `private` | Visibilidad inicial solicitada por el usuario. |
| `status` | `pending`, `approved`, `rejected` | Estado de revision del album. |
| `user_id` | FK `users.id` | Propietario obtenido desde el JWT, no desde el request. |
| `created_at` | fecha | Fecha de creacion. |
| `updated_at` | fecha | Fecha de actualizacion. |
| `reviewed_by` | FK opcional `users.id` | Supervisor o administrador que reviso la solicitud. |
| `reviewed_at` | fecha opcional | Fecha de revision. |
| `rejection_reason` | texto opcional | Motivo de rechazo validado como texto plano. |

### Estados del album

| Estado | Uso |
| --- | --- |
| `pending` | Estado inicial de toda solicitud creada por un usuario autenticado. |
| `approved` | Estado asignado por supervisor/admin para permitir publicacion y subida de imagenes. |
| `rejected` | Estado asignado por supervisor/admin cuando la solicitud no procede. |

### Flujo de aprobacion

1. El usuario inicia sesion y envia `POST /albums/request`.
2. El backend obtiene el usuario desde el JWT y crea el album con `status = pending`.
3. El usuario consulta sus solicitudes con `GET /albums/my`.
4. El supervisor o administrador consulta solicitudes con `GET /albums/supervisor?status=pending`.
5. El supervisor aprueba con `PATCH /albums/{album_id}/approve` o rechaza con `PATCH /albums/{album_id}/reject`.
6. Si el album ya no esta en `pending`, el backend responde `409 Conflict`.

### Reglas de seguridad contra Stored XSS

La estrategia aplicada es tratar `title`, `description` y `rejection_reason` como texto plano. El backend normaliza espacios, valida longitud y rechaza patrones peligrosos como `<script>`, `javascript:`, eventos HTML (`onerror=`, `onclick=`, `onload=`), `<iframe>`, `<object>`, `<embed>`, `<svg>`, `<img` y `data:text/html`.

No se acepta HTML enriquecido. El frontend renderiza con interpolacion normal de React y no usa `dangerouslySetInnerHTML`, por lo que los textos no se interpretan como HTML.

### Control de acceso RBAC

El usuario autenticado se obtiene mediante JWT en `get_current_user`. La dependencia `require_supervisor_or_admin` restringe rutas administrativas a roles `supervisor` y `admin`.

Los usuarios normales pueden crear solicitudes y listar solo sus propios albumes. No se confia en roles enviados desde el frontend. Para crear un supervisor de demostracion en la base local, registrar un usuario y actualizar su rol directamente en base de datos:

```sql
UPDATE users SET role = 'supervisor' WHERE username = 'supervisor_demo';
```

### Endpoints implementados

| Metodo | Ruta | Rol | Descripcion |
| --- | --- | --- | --- |
| `POST` | `/auth/register` | publico | Registro minimo de usuarios normales. |
| `POST` | `/auth/login` | publico | Emite JWT con datos de usuario. |
| `GET` | `/auth/me` | autenticado | Devuelve usuario actual. |
| `POST` | `/albums/request` | autenticado | Crea solicitud de album en `pending`. |
| `GET` | `/albums/my` | autenticado | Lista albumes propios, con filtro opcional `status`. |
| `GET` | `/albums/public` | publico | Lista albumes `approved` y `public`. |
| `GET` | `/albums/supervisor` | supervisor/admin | Lista albumes, con filtro opcional `status`. |
| `PATCH` | `/albums/{album_id}/approve` | supervisor/admin | Aprueba album pendiente. |
| `PATCH` | `/albums/{album_id}/reject` | supervisor/admin | Rechaza album pendiente con motivo opcional. |
| `POST` | `/images/upload` | autenticado | Subida minima de imagen solo si el album propio esta aprobado. |

### Pruebas con Postman

La coleccion se genero fuera del repositorio en:

`../RF02_albumes_pruebas/postman/RF02_albumes_collection.json`

Variables esperadas:

| Variable | Descripcion |
| --- | --- |
| `base_url` | URL del backend, por defecto `http://localhost:8000`. |
| `user_token` | JWT de usuario normal. |
| `supervisor_token` | JWT de supervisor/admin. |
| `album_id` | Identificador de album creado para pruebas. |

### Pruebas desde el frontend

1. Ejecutar backend y frontend.
2. Registrar un usuario normal.
3. Iniciar sesion y crear una solicitud de album desde el dashboard.
4. Verificar que aparece en `Mis solicitudes` con estado `pending`.
5. Cambiar un usuario demo a rol `supervisor` o `admin` en base de datos.
6. Iniciar sesion como supervisor y abrir el panel de revision.
7. Filtrar por `pending`, aprobar o rechazar y confirmar que el usuario ve el estado actualizado.

### Prueba de Stored XSS

Intentar crear albumes con estos valores:

```text
<script>alert(1)</script>
<img src=x onerror=alert(1)>
javascript:alert(1)
<svg onload=alert(1)>
data:text/html,<script>alert(1)</script>
```

El backend debe responder `422 Unprocessable Entity` con mensaje de contenido no permitido o impedir la persistencia del texto peligroso. En frontend no debe ejecutarse ningun script.

### Ejecucion del backend

Antes de ejecutar el backend, levantar PostgreSQL:

```bash
docker compose up -d db
```

El Compose crea un contenedor PostgreSQL 16 y la base `secureframe_gallery` usando las variables de `.env`. En una base nueva ejecuta `database/init/01_secureframe_schema.sql`, creando las tablas principales del sistema y un admin de prueba. La aplicacion no ejecuta `Base.metadata.create_all` al arrancar.

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Variables principales de `backend/.env`:

```env
DATABASE_URL=postgresql+psycopg2://secureframe_user:secureframe_password@localhost:5432/secureframe_gallery
SECRET_KEY=change-this-secret-key-in-production
FRONTEND_ORIGIN=http://localhost:5173
```

Credencial de prueba generada por el init SQL:

```text
username: admin_demo
password: Admin12345
role: admin
```

Si el volumen ya existia, recrear la base para que el init se ejecute:

```bash
docker compose down -v
docker compose up -d db
```

### Ejecucion del frontend

```bash
cd frontend
npm install
npm run dev
```

El frontend espera `VITE_API_BASE_URL=http://localhost:8000` si se desea configurar explicitamente.

### Notas de integracion con RF03

El endpoint minimo `POST /images/upload` verifica que el album exista, pertenezca al usuario autenticado y tenga `status = approved`. Si el album esta `pending` o `rejected`, responde `403` con el mensaje solicitado: `Solo se pueden subir imagenes a albumes aprobados.`

### Limitaciones y decisiones tecnicas

No habia implementacion previa en los archivos de backend ni frontend, por lo que se creo una base minima funcional. No habia configuracion Alembic existente; por compatibilidad academica local se uso `Base.metadata.create_all` en el arranque. Si el equipo incorpora Alembic, estos campos deben convertirse en una migracion formal antes de produccion.

### Archivos modificados o creados

| Archivo | Cambio |
| --- | --- |
| `backend/app/config.py` | Configuracion de entorno. |
| `backend/app/database.py` | Engine, sesion y base declarativa SQLAlchemy. |
| `backend/app/models/user.py` | Modelo User con rol y relaciones. |
| `backend/app/models/album.py` | Modelo Album RF02 con auditoria de revision. |
| `backend/app/models/image.py` | Modelo Image minimo para dependencia con album aprobado. |
| `backend/app/schemas/auth.py` | Schemas de autenticacion. |
| `backend/app/schemas/album.py` | Schemas RF02 y validacion anti Stored XSS. |
| `backend/app/schemas/image.py` | Respuesta de imagen. |
| `backend/app/services/auth_service.py` | Hash de contrasena, JWT y RBAC. |
| `backend/app/routers/auth.py` | Registro, login y usuario actual. |
| `backend/app/routers/albums.py` | Endpoints RF02. |
| `backend/app/routers/images.py` | Guardia minima de subida a album aprobado. |
| `backend/app/main.py` | Registro de app, CORS y routers. |
| `backend/requirements.txt` | Dependencias backend. |
| `frontend/package.json` | Scripts y dependencias frontend. |
| `frontend/index.html` | Entrada Vite. |
| `frontend/tsconfig.json` | Configuracion TypeScript. |
| `frontend/src/main.tsx` | Bootstrap React. |
| `frontend/src/App.tsx` | Layout y composicion de paginas. |
| `frontend/src/context/AuthContext.tsx` | JWT y rol global tipado. |
| `frontend/src/services/api.ts` | Axios tipado y endpoints RF02. |
| `frontend/src/types/index.ts` | Tipos User, Role, Album. |
| `frontend/src/pages/Dashboard.tsx` | Solicitud de album y listado propio. |
| `frontend/src/pages/Supervisor.tsx` | Revision y filtros por estado. |
| `frontend/src/pages/Gallery.tsx` | Galeria publica de albumes aprobados. |
| `frontend/src/pages/Login.tsx` | Login minimo. |
| `frontend/src/pages/Register.tsx` | Registro minimo. |
| `frontend/src/styles.css` | Estilos de interfaz. |
