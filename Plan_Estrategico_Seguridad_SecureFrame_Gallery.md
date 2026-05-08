# Documento de Plan Estratégico de Seguridad  
**Sistema:** SecureFrame Gallery (FastAPI + Frontend Web + PostgreSQL + almacenamiento tipo S3/MinIO)  
**Curso:** Desarrollo Seguro — ESPE (VII)  
**Autor:** _[Nombre del estudiante]_  
**Fecha:** 2026-05-08  
**Versión:** 1.0  

---

## 0. Resumen ejecutivo

SecureFrame Gallery es un sistema que permite a usuarios autenticados solicitar álbumes, que luego son aprobados por un rol supervisor/admin, y subir imágenes únicamente a álbumes aprobados. La galería pública expone álbumes aprobados y públicos. El backend está implementado en **FastAPI** con **JWT** (access token) y **refresh token en cookie HttpOnly**, y el almacenamiento de imágenes se realiza mediante un servicio compatible con S3 (MinIO) y URLs pre-firmadas.

Este Plan Estratégico de Seguridad identifica los riesgos más críticos del sistema (especialmente alrededor de **subida y procesamiento de archivos**, **control de acceso por roles**, y **gestión de sesiones/tokens**), propone un conjunto de **controles técnicos y organizativos** priorizados por coste/impacto, define actividades de seguridad por fase del **SDLC**, y alinea la solución con principios de **OWASP ASVS (Nivel 2)** y **NIST SP 800-218 (SSDF)**.

---

## 1. Introducción, alcance y supuestos

### 1.1 Alcance del sistema

Funciones consideradas en este plan (según el repositorio):

- Registro y autenticación (`/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/me`).
- RBAC (roles `user`, `supervisor`, `admin`) y protección de endpoints.
- Gestión de solicitudes de álbum (estado `pending/approved/rejected`).
- Subida de imágenes a álbum aprobado (`POST /images/upload`), persistencia de metadatos en DB y almacenamiento en S3/MinIO.
- Acceso a imagen mediante URL pre-firmada (`GET /images/{image_id}/url`).

### 1.2 Actores y roles

- **Visitante (público):** consulta álbumes públicos aprobados.
- **Usuario:** se registra, inicia sesión, solicita álbumes y sube imágenes a álbum aprobado propio.
- **Supervisor:** revisa y aprueba/rechaza solicitudes.
- **Admin:** capacidades equivalentes o superiores al supervisor, además de administración.

### 1.3 Activos a proteger

| Activo | Por qué importa |
|---|---|
| Credenciales (hash de contraseña, cookies refresh, JWT) | Compromiso implica toma de cuentas y acceso a recursos privados. |
| Álbumes e imágenes (privadas/públicas) | Exposición de contenido privado, daño reputacional, problemas legales. |
| Infra (API, DB, MinIO/S3, logs) | Caídas (DoS), corrupción, pérdida de datos, costos operativos. |
| Reputación del sistema/curso/equipo | Un incidente público (imagen maliciosa viral) daña credibilidad. |

### 1.4 Límites de confianza (trust boundaries)

1. **Navegador/Cliente** (no confiable): entradas del usuario, archivos subidos, headers.
2. **Backend FastAPI** (zona confiable controlada): validación, auth, autorización, lógica.
3. **Base de datos PostgreSQL** (confianza alta, acceso restringido): persistencia de usuarios/álbumes/imágenes.
4. **Almacenamiento tipo S3/MinIO** (zona semi-confiable): objetos; requiere políticas estrictas (IAM/bucket policy).
5. **Servicios externos** (SMTP/Email si aplica): verificación de cuenta, reset password.

---

## 2. Introducción y costes: impacto de Path Traversal y File Upload Bypass

### 2.1 ¿Cuál es el coste de un Path Traversal en este sistema?

**Path Traversal** ocurre cuando una funcionalidad que construye rutas de archivos permite que un atacante manipule el path (p. ej. `../../etc/passwd`) y acceda a archivos fuera del directorio previsto.

En SecureFrame Gallery, aunque el almacenamiento final está en MinIO (objeto, no filesystem), pueden existir escenarios de Path Traversal en:

- Carpeta `backend/uploads/` (si se usa en futuros RF para staging/scan).
- Cualquier futura “descarga/preview” de archivos desde el servidor.
- Procesamiento local temporal de imágenes (transcodificación, extracción de metadatos).

**Costes e impactos**:

- **Confidencialidad:** lectura de `.env`, claves (`SECRET_KEY`, credenciales MinIO/DB), archivos de configuración, backups, llaves privadas.
- **Integridad:** si además existe escritura, se podría sobreescribir archivos (p. ej. código o configuración), escalando a RCE.
- **Disponibilidad:** lectura masiva o de dispositivos especiales puede degradar el servicio.
- **Coste económico directo:** horas de respuesta a incidentes, rotación de secretos, downtime.
- **Coste académico y reputacional:** demuestra falta de controles básicos; afecta entregables y confianza.

**Escenario crítico**: si se filtra `SECRET_KEY`, un atacante podría **firmar JWT** válidos y suplantar roles (`admin`), comprometiendo completamente el sistema.

### 2.2 ¿Cuál es el coste de un File Upload Bypass?

Un **File Upload Bypass** ocurre cuando la validación del archivo subido es insuficiente y permite:

- Subir un archivo que no es realmente imagen (p. ej. ejecutable, script, HTML) pero “parece” imagen por extensión/Content-Type.
- Subir un archivo “polyglot” (válido como imagen y como otro formato interpretado en otro contexto).
- Subir imágenes con cargas ocultas (metadatos/esteganografía) o “decompression bombs”.

**Costes e impactos**:

- **RCE indirecto**: si alguna parte del pipeline ejecuta herramientas externas (ImageMagick/ffmpeg/exiftool) sin sandbox, un archivo malicioso puede explotar CVEs.
- **XSS/Contenido activo**: si se permite SVG o HTML disfrazado, y se sirve con `Content-Type` incorrecto, podría ejecutar JS.
- **DoS**: imágenes muy grandes o comprimidas agresivamente consumen CPU/RAM (PIL/libjpeg) al procesarlas.
- **Abuso del storage**: subida masiva => costo por almacenamiento/egreso.
- **Riesgo legal**: distribución de malware o contenido ilegal.

### 2.3 ¿Qué pasaría si una imagen con payload oculto se vuelve viral en la galería pública?

Este es un “escenario de pesadilla” realista para una galería:

1. Un atacante sube una imagen aparentemente normal (o logra que un usuario legítimo lo haga).
2. La imagen se vuelve viral (muchas visitas y descargas).
3. El payload oculto puede ser:
   - **Esteganografía** (oculta datos en LSB/píxeles) para exfiltración o C2.
   - **Metadatos maliciosos** (EXIF/XMP) para explotar parsers en clientes o en el servidor.
   - **Archivo polyglot** que activa comportamiento en ciertos viewers.
4. Consecuencias:
   - **Exposición masiva**: impacto reputacional fuerte.
   - **DoS por popularidad + procesamiento**: si se generan thumbnails on-demand sin caché, se multiplican costos CPU/RAM.
   - **Compromiso de clientes**: aunque el servidor esté bien, la plataforma se asocia con malware.
   - **Responsabilidad**: puede implicar reporte y remediación, retiro de contenido, bloqueo de cuentas, y medidas de moderación.

Por ello, el plan debe incluir **controles preventivos**, **detección** y un proceso de **respuesta** (quarantine/takedown).

### 2.4 Modelo de costes (estimación práctica para justificar prioridades)

> Los valores son estimaciones para argumentar impacto (no cifras oficiales). El objetivo es justificar por qué “upload hardening” y “storage/IAM” son prioridades.

**Coste directo (operativo)**:

- **Respuesta a incidente (IR):** 1–3 personas × 8–24 horas (triage, contención, rotación de secretos, despliegue hotfix, análisis).
- **Downtime / degradación:** pérdida de disponibilidad y tiempo invertido en recuperación (restaurar DB, limpiar bucket, reindexar).
- **Coste de infraestructura:** subida/descarga masiva de objetos (egress), almacenamiento de archivos maliciosos, CPU para reintentos.

**Coste indirecto (reputacional/academia/legal)**:

- Pérdida de confianza (usuarios evitan la plataforma).
- Deterioro de credibilidad del equipo (especialmente si el incidente es “viral”).
- Riesgos legales si se distribuye malware o contenido sensible.

**Traducción a decisiones técnicas**:

- Un control “barato” como **límite de tamaño/dimensiones** reduce drásticamente DoS por imágenes grandes.
- **Bucket privado + presigned URL** previene exposición masiva por error de configuración.
- **Re-encoding** reduce impacto de payloads ocultos (metadatos/polyglots) con un coste de CPU controlable si se hace asíncrono.

---

## 3. Análisis de amenazas: matriz categorizada

> Convención usada:  
> **Impacto (CIA)**: C (confidencialidad), I (integridad), A (disponibilidad).  
> **Probabilidad:** Baja/Media/Alta en función de exposición + facilidad + controles actuales.  
> **Prioridad:** combina impacto + probabilidad + dificultad de mitigación.

### 3.1 Hardware (CPU/RAM/IO): amenazas de procesamiento de imágenes

| Amenaza | Escenario | CIA | Prob. | Controles propuestos | Evidencia/artefacto |
|---|---|---:|---:|---|---|
| Decompression bomb / imagen gigante | Suben PNG/JPEG que al decodificar consume RAM/CPU; PIL intenta procesar | A↑ | Alta | Límite de tamaño (bytes) y dimensiones; rechazar >X MP; `PIL.Image.MAX_IMAGE_PIXELS`; timeouts; colas asíncronas | Política de límites + tests de carga |
| DoS por ráfaga de uploads | Subida masiva de archivos (aunque sean “válidos”) | A↑ | Alta | Rate limiting por IP/usuario; cuotas; WAF/proxy; backpressure; almacenamiento con límites | Config SlowAPI + métricas |
| DoS por análisis costoso | Un atacante fuerza análisis repetido (p.ej. steganálisis/entropy) con imágenes grandes | A↑ | Media | Hacer análisis asíncrono; cachear resultados; límites por usuario; timeouts por job | Cola + métricas de jobs |
| Exhaustión de disco temporal | Si se usa staging local para escaneo/transcodificación | A↑ | Media | Evitar persistencia local; usar tmp con quotas; limpiar; monitor de espacio | Checklist DevOps |
| Ataques side-channel (micro) | Tiempos distintos en login/validación permiten inferir existencia de usuario | C↑ | Media | Ya existe timing equivalence (dummy hash). Mantenerlo y auditar errores | Pruebas de enumeración |

### 3.2 Código (dependencias y errores de implementación)

| Amenaza | Escenario | CIA | Prob. | Controles propuestos | Evidencia/artefacto |
|---|---|---:|---:|---|---|
| CVEs en librerías de imagen | PIL/Pillow, libjpeg, png parser con vulnerabilidades | C/I/A | Media | SCA (dependabot/pip-audit); pin de versiones; actualización programada | Reporte SCA por release |
| Command Injection en herramientas externas | Si se llama `exiftool`, `ffmpeg`, etc. con `shell=True` o argumentos no sanitizados | C/I/A | Media | Evitar shell; usar listas de args; sandbox; principio de mínimo privilegio | Revisión de código + lint |
| Validación insuficiente de tipo de archivo | Solo se valida `content_type.startswith("image/")` (bypass fácil) | C/I/A | Alta | Validación por **magic bytes**; decodificar y re-encode (transcodificación); lista blanca (JPEG/PNG/WebP) | Tests de bypass (polyglot) |
| Path Traversal en staging/futuros endpoints | Si se implementa lectura/escritura local con nombre controlado por usuario | C/I | Media | No construir rutas con input sin normalizar; usar IDs internos; `pathlib` + allowlist; nunca servir rutas del FS | Revisión de endpoints de archivos |
| SSRF vía “fetch de URL” (futuro) | Si se agrega función de “importar imagen por URL” | C/I/A | Media | Bloquear IPs internas, DNS rebinding; allowlist de dominios; proxy controlado | Checklist de features |
| SQLi/ORM misuse (futuro) | Consultas raw o concatenación de strings | C/I | Baja/Media | ORM parametrizado; revisión; tests; SAST | Reglas semgrep |
| Inyección en logs / datos sensibles | Loguear tokens, passwords o PII en eventos de auth | C↑ | Media | Redacción/mascarado en logs; formato estructurado; políticas de retención | Guía de logging seguro |
| Revocación de tokens incompleta | Blocklist in-memory no escala; refresh rotación sin detección de reuse | C/I | Media | Blocklist en Redis/DB con TTL; refresh rotation con “family” o `jti` persistente; invalidación al cambiar contraseña | Diseño de sesiones v2 |

### 3.3 Diseño (lógica de negocio, roles, flujos)

| Amenaza | Escenario | CIA | Prob. | Controles propuestos | Evidencia/artefacto |
|---|---|---:|---:|---|---|
| Falta de segregación real de roles | Usuario puede acceder a endpoints supervisor/admin por fallos de dependencia | C/I | Media | Centralizar autorización; tests de autorización por rol; policy-as-code | Suite de tests RBAC |
| IDOR en recursos (álbum/imagen) | Acceso a `image_id` ajeno; URLs pre-firmadas permiten bypass | C↑ | Media | Verificar permisos antes de firmar URL; expirar rápido; no exponer paths | Tests IDOR + reglas |
| Enumeración de usuarios en registro/login | Mensajes diferentes permiten saber si existe usuario/email | C↑ | Media | Uniformar mensajes; mantener timing equivalence; rate limit por IP | Caso de prueba ASVS |
| Falta de flujo de verificación de email (si aplica) | Cuentas fake para spam/abuso | A/Reputación | Media | Email verify + límites; bloqueo/ban; reputación de IP | Registro de verificación |
| Moderación ausente | Contenido ilegal/malicioso se publica | Reputación/Legal | Media | Quarantine/approval de imágenes públicas; reporte; takedown; hash de contenidos | Procedimiento operativo |
| CSRF si se usa cookie de sesión/refresh | Un sitio externo induce requests con cookies | I | Media | CSRF token (double-submit) en endpoints mutadores; SameSite; CORS mínimo | Pruebas CSRF |
| XSS en frontend (impacto sobre tokens) | Si se guardan tokens en storage web o hay render inseguro | C/I | Media | No guardar JWT en localStorage; CSP; sanitización; evitar HTML rich | Checklist frontend |

### 3.4 Arquitectura (despliegue, storage, secretos, comunicación)

| Amenaza | Escenario | CIA | Prob. | Controles propuestos | Evidencia/artefacto |
|---|---|---:|---:|---|---|
| Bucket público o IAM permisivo | El bucket MinIO/S3 permite listar/leer objetos | C↑ | Media/Alta | Bucket privado; política “deny by default”; solo presigned GET; separar buckets (public/quarantine) | Política IAM/bucket versionada |
| MinIO sin TLS (`secure=False`) | Tráfico API↔MinIO sin cifrar expone credenciales/objetos | C/I | Media | TLS end-to-end; `secure=True`; certificados; red privada | Config de despliegue |
| CORS permisivo | Orígenes no confiables pueden abusar de cookies/requests | C/I | Media | CORS mínimo; `allow_credentials` solo si necesario; origin exacto | Config CORS revisada |
| Secretos en repositorio o `.env` mal manejado | Filtración de `SECRET_KEY`, DB, MinIO keys | C/I | Media | Secret management; escaneo de secretos (gitleaks); rotación | Política de secretos |
| Exposición de DB | DB accesible desde internet | C/I/A | Baja/Media | Segmentación de red; firewall; credenciales mínimas; backups cifrados | Diagrama de red |
| URLs pre-firmadas demasiado largas | Links compartidos permanecen válidos y se filtran | C↑ | Media | TTL corto por sensibilidad; renovación; watermark (opcional) | Política de expiración |

---

## 4. Estrategia de controles (qué haremos y por qué)

### 4.1 Controles para subida y publicación de imágenes (núcleo del riesgo)

**Objetivo:** evitar file upload bypass, reducir superficie de CVEs y prevenir viralización de payloads.

Controles priorizados:

1. **Lista blanca de formatos:** aceptar solo `image/jpeg`, `image/png`, `image/webp` (evitar SVG en primera etapa).
2. **Validación por contenido (magic bytes):** no confiar solo en `Content-Type`.
3. **Transcodificación obligatoria (“sanitize by re-encoding”):**
   - Decodificar con librería confiable.
   - Re-encode a formato estándar (p.ej., JPEG/PNG) eliminando perfiles extraños.
   - Esto reduce metadatos, polyglots y payloads en segmentos no usados.
4. **Strip de metadatos (EXIF/XMP):** remover por defecto para imágenes públicas.
5. **Límites:** tamaño máximo (MB), dimensiones máximas (MP), y número de imágenes por día/usuario.
6. **Quarantine:** mantener un estado “en revisión” para imágenes:
   - `uploaded -> quarantined -> approved/rejected`.
   - Integrar analítica básica (p.ej., el `steg_analyzer` existente) como señal, no como veredicto absoluto.
7. **Moderación y takedown:** capacidad de despublicar rápido, y trazabilidad (quién subió, cuándo, IP).

### 4.2 Controles para almacenamiento tipo S3/MinIO

- **Bucket privado**: sin acceso público directo.
- **Acceso por URL pre-firmada**: emitir solo tras autorización (ya se hace, pero se debe reforzar).
- **Expiración corta**: para imágenes privadas, expiración menor (p.ej. 5–15 min) y renovar según necesidad.
- **Separación de buckets/prefijos**:
  - `quarantine/` (no público, no presigned a visitantes)
  - `public/` (solo presigned para visitantes o CDN controlado)
  - `private/` (solo presigned para propietarios/supervisor/admin)
- **TLS y red privada**: MinIO debe usar HTTPS (`secure=True`) y credenciales no deben viajar en claro.
- **Rotación de claves MinIO/S3**: programada y tras incidentes.

### 4.3 Controles de autenticación y sesiones/tokens

En el repositorio se observa:

- Access token JWT (Bearer) con `token_version`.
- Refresh token JWT en cookie `secureframe_refresh`, con rotación al refrescar.
- Blocklist in-memory para logout (demo).

Recomendaciones estratégicas:

1. **Cookies seguras en producción**:
   - `HttpOnly=True` (ya)
   - `Secure=True` (en producción)
   - `SameSite=Lax` (o `None` solo si es cross-site y siempre con HTTPS).
2. **Rotación robusta de refresh tokens**:
   - Persistir `jti` de refresh en DB/Redis con TTL.
   - En refresh: invalidar el refresh anterior, emitir uno nuevo.
   - Si se detecta reuse (mismo `jti` usado dos veces) => revocar “familia” y forzar re-login.
3. **Invalidación global**:
   - Al cambio de contraseña, bloqueo, o sospecha: incrementar `token_version` (ya existe campo) y revocar refresh activos.
4. **Mensajes de error consistentes**:
   - En login, preferir respuestas que no permitan enumeración (ya hay parte).
5. **Auditoría de eventos**:
   - login fail, lock, unlock, refresh, logout, cambio de contraseña.

### 4.4 Controles de API: validación, errores, cabeceras

Ya existen headers básicos (CSP, HSTS, nosniff). Ajustes propuestos:

- CSP actual incluye `'unsafe-inline'`; en un plan estratégico, se propone:
  - reducir inline scripts (en frontend) y endurecer CSP con hashes/nonces si es posible.
- Para endpoints de auth:
  - `Cache-Control: no-store` (ya).
- Estándar de errores:
  - Mensajes consistentes, sin stack traces, con `request_id` para correlación en logs.

### 4.5 Controles en frontend (para reducir XSS y robo de sesión)

Aunque el backend sea robusto, un XSS en el frontend puede:

- Robar el **access token** si se guarda en `localStorage/sessionStorage`.
- Abusar de cookies de refresh si CORS/CSRF están mal configurados.

Directrices:

- Mantener el access token **en memoria** (contexto React) y refrescar cuando sea necesario.
- Evitar `dangerouslySetInnerHTML` (ya se menciona como decisión en el README).
- Endurecer CSP gradualmente (idealmente eliminar `'unsafe-inline'` en producción).
- Validar y escapar siempre los textos mostrados (títulos/descripciones ya se tratan como texto plano).

---

## 5. Seguridad en el SDLC (actividades por fase)

La seguridad no es una “tarea al final”, sino un conjunto de actividades repetibles en cada fase.

### 5.1 Requisitos

Actividades:

- Definir requisitos **CIA** por tipo de dato:
  - Imágenes privadas: C alta.
  - Álbum público: C media (contenido público), I alta (evitar manipulación), A media/alta.
  - Credenciales/tokens: C e I muy altas.
- Definir requisitos de **privacidad**:
  - Minimización de metadatos de imágenes (remover EXIF).
- Definir requisitos anti-abuso:
  - límites de uploads, rate limiting, bloqueo por intentos.
- Definir requisitos de logging:
  - qué se registra y qué se prohíbe registrar (tokens, contraseñas).

Entregables:

- Documento de requisitos de seguridad (lista priorizada).
- Criterios de aceptación (p.ej. “no se aceptan archivos no-imagen por magic bytes”).

### 5.2 Diseño

Actividades:

- **Threat Modeling** (este documento) y revisión por el equipo.
- Definir arquitectura de almacenamiento:
  - buckets/prefijos, permisos, flujo quarantine.
- Diseñar el flujo de imágenes:
  - upload -> validación -> transcodificación -> análisis -> quarantine/approve.
- Definir modelo de sesiones/tokens:
  - refresh persistente con `jti` y detección de reuse.
- Definir controles de acceso (RBAC + pruebas).

Entregables:

- Diagrama de flujo (DFD) y límites de confianza.
- Matriz de amenazas actualizada y backlog de mitigaciones.

### 5.3 Desarrollo

Actividades:

- **SAST**:
  - Semgrep (reglas FastAPI/Python)
  - Bandit (Python security linter)
- **SCA**:
  - `pip-audit` / Dependabot (CVEs en dependencias)
- Revisiones de código:
  - checklist para uploads, auth, storage, logging.
- Gestión de secretos:
  - escaneo con gitleaks, no commitear `.env`.
- IaC/Config scanning (si hay Docker/K8s):
  - revisar `docker-compose.yml` y configuraciones para evitar credenciales por defecto y puertos expuestos.

Entregables:

- Pipeline CI con SAST/SCA.
- Checklist de PR (pull request) con puntos ASVS.

### 5.4 Pruebas

Actividades:

- **DAST**:
  - OWASP ZAP contra el backend (auth, endpoints, CORS, headers).
- Pruebas específicas:
  - IDOR en `image_id`.
  - File upload bypass (polyglot, Content-Type falso, magic bytes).
  - DoS básico (tamaño/dimensiones).
- **Fuzzing** (especialmente para parsers de imagen):
  - Fuzzing de endpoint upload con corpus de imágenes corruptas.
  - En Python, se puede usar Atheris (fuzzing) sobre funciones de parseo/transcodificación si se implementan.

Entregables:

- Reporte de pruebas con evidencias (capturas/logs).
- Casos de prueba automatizados.

### 5.5 Despliegue y Operación

Actividades:

- Hardening de configuración:
  - `Secure=True` en cookies, HSTS, TLS.
  - DB no expuesta públicamente.
  - MinIO/S3 en red interna y con TLS.
- Observabilidad:
  - métricas de uploads, errores, rate limiting, locks.
- Gestión de incidentes:
  - playbook de “takedown de imagen viral”.
  - rotación de secretos y revocación de tokens.

Entregables:

- Runbook de incident response.
- Dashboards/alertas básicos.

---

## 6. Directrices adicionales y alineación con frameworks

### 6.1 Alineación con OWASP ASVS (Nivel 2)

> Nota: ASVS L2 es adecuado para aplicaciones que manejan autenticación y datos de usuarios con exposición en internet. No se implementa “un framework”, se alinea la solución con sus requisitos.

| ASVS (familia) | Cómo lo cubrimos en SecureFrame Gallery | Evidencia esperada |
|---|---|---|
| V1: Arquitectura, diseño y threat modeling | Matriz de amenazas + límites de confianza + decisiones IAM/storage | Este documento + diagramas |
| V2: Autenticación | Rate limit, anti-enumeración, bloqueo temporal, hash Argon2 | Código auth + pruebas |
| V3: Gestión de sesión | Refresh en cookie HttpOnly + rotación + revocación por `token_version` | Diseño de refresh con `jti` |
| V4: Control de acceso | Dependencias RBAC y pruebas por rol; evitar IDOR | Tests RBAC/IDOR |
| V5: Validación, sanitización y encoding | Anti Stored XSS en textos; validación estricta de uploads | Tests de bypass/XSS |
| V7: Manejo de errores y logging | Mensajes consistentes, logs sin datos sensibles, request_id | Política de logs |
| V9: Comunicaciones | TLS extremo a extremo (cliente↔API y API↔MinIO) | Config TLS |
| V12: Archivos y recursos | Lista blanca, magic bytes, transcodificación, límites, quarantine | Evidencia de pipeline de imágenes |
| V13: API y servicios web | CORS mínimo, headers seguridad, DAST | Reporte OWASP ZAP |
| V14: Configuración | secretos fuera del repo, hardening, rotación | gitleaks + runbooks |

### 6.2 Alineación con NIST SP 800-218 (SSDF)

SSDF propone prácticas organizadas en 4 áreas. Alineación propuesta:

1. **PO (Prepare the Organization)**  
   - Definir roles y responsabilidad (quién aprueba releases, quién revisa seguridad).  
   - Política mínima de secretos y rotación.  
   - Capacitación: checklist de uploads, JWT, CORS.

2. **PS (Protect the Software)**  
   - Control de acceso a repositorio; branch protection.  
   - SCA/SAST en CI; escaneo de secretos (gitleaks).  
   - Firmas/versionado de artefactos de release.

3. **PW (Produce Well-Secured Software)**  
   - Threat modeling en diseño.  
   - Validación fuerte de uploads y reducción de superficie (re-encoding).  
   - Pruebas DAST y fuzzing donde aplique.

4. **RV (Respond to Vulnerabilities)**  
   - Proceso de manejo de CVEs (dependencias).  
   - Playbook de incidentes (imagen viral, credencial filtrada).  
   - Ciclo de mejora continua (post-mortem + acciones).

---

## 7. Roadmap (prioridades y costos de implementación)

### 7.1 Quick wins (1–3 días)

- Hacer `Secure=True` en cookies en configuración de producción.
- Limitar tamaño de upload (MB) y dimensiones máximas (MP).
- Validación por magic bytes + lista blanca de formatos.
- Reducir expiración de presigned URLs para privados.
- Política de logging seguro (sin tokens/PII).

### 7.2 Mediano plazo (1–2 semanas)

- Pipeline de imágenes: transcodificación + stripping EXIF.
- Quarantine real + panel supervisor para aprobar/rechazar imágenes (si aplica).
- Persistir refresh `jti` en Redis/DB para revocación y detección de reuse.
- SAST/SCA/secret scanning en CI.

### 7.3 Largo plazo (2–4 semanas)

- Fuzzing sistemático de pipeline de imágenes.
- WAF/Rate limiting avanzado y cuotas por usuario.
- CDN controlado para contenido público, con cache y protecciones.
- Métricas y alertas (DoS, subida masiva, fallos auth).

---

## 8. Métricas y criterios de aceptación

Ejemplos de criterios verificables:

- **Uploads**:
  - 100% de archivos aceptados deben decodificar y re-encodificar correctamente.
  - Rechazo de polyglots y Content-Type falso (casos de prueba).
  - Límite de tamaño/dimensiones aplicado (tests).
- **Auth/Sesión**:
  - Rate limiting en login/registro funcionando.
  - Bloqueo temporal tras N intentos fallidos.
  - Revocación por `token_version` tras cambio de contraseña/bloqueo.
- **Storage**:
  - Bucket no permite listado público.
  - Presigned URLs expiran y no se emiten sin autorización previa.
- **SDLC**:
  - Pipeline CI falla si hay secretos o CVEs críticas sin excepción aprobada.
  - Reporte DAST sin hallazgos de severidad alta.

---

## 9. Anexo: checklist breve de riesgos “top”

1. Upload bypass (no confiar en Content-Type)  
2. DoS por imágenes grandes/decompression bombs  
3. IAM/bucket policy permisiva (storage público)  
4. Tokens/sesiones sin revocación robusta  
5. IDOR en acceso a imágenes  
6. Logging con datos sensibles  
7. Falta de proceso de takedown/quarantine ante contenido viral  
