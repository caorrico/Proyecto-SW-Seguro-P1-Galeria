# Arquitectura recomendada con MinIO

## Buckets separados

MUY importante.

No uses un solo bucket para todo.

---

# Propuesta ideal

## 1. Bucket: `uploads-quarantine`

Archivos recién subidos.

Privado.

NADIE público puede acceder.

---

## 2. Bucket: `gallery-public`

Solo imágenes aprobadas.

Lectura pública.

---

## 3. Bucket: `rejected-evidence`

Opcional.

Guardar archivos sospechosos:

* auditoría
* investigación
* evidencias

Privado total.

---

# Flujo seguro

<pre class="overflow-visible! px-0!" data-start="1126" data-end="1277"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute end-1.5 top-1 z-2 md:end-2 md:top-1"></div><div class="relative"><div class="pe-11 pt-3"><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼd ͼr"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span>usuario</span><br/><span>   ↓</span><br/><span>backend</span><br/><span>   ↓</span><br/><span>uploads-quarantine</span><br/><span>   ↓</span><br/><span>worker análisis</span><br/><span>   ↓</span><br/><span>limpio -> gallery-public</span><br/><span>sospechoso -> rejected-evidence</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

---

# Cómo aplicar IAM realmente

En MinIO creas:

* usuarios
* policies
* access keys
* secret keys

---

# Ejemplo de roles reales

## Backend API

Debe poder:

* subir archivos
* mover objetos
* leer metadata

Pero NO:

* borrar todo el storage
* acceder a admin

---

## Worker de análisis

Debe:

* leer cuarentena
* escribir resultados

NO necesita:

* acceso público
* admin global

---

## Frontend público

Idealmente:

* NO accede directo a MinIO privado
* solo recibe URLs seguras

---

# Policies estilo IAM

MinIO usa policies JSON parecidas a AWS.

---

# Ejemplo:

Backend solo puede escribir cuarentena

<pre class="overflow-visible! px-0!" data-start="1894" data-end="2128"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="relative"><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼd ͼr"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span>{</span><br/><span>  "Version": </span><span class="ͼk">"2012-10-17"</span><span>,</span><br/><span>  "Statement": [</span><br/><span>    {</span><br/><span>      "Effect": </span><span class="ͼk">"Allow"</span><span>,</span><br/><span>      "Action": [</span><br/><span></span><span class="ͼk">"s3:PutObject"</span><br/><span>      ],</span><br/><span>      "Resource": [</span><br/><span></span><span class="ͼk">"arn:aws:s3:::uploads-quarantine/*"</span><br/><span>      ]</span><br/><span>    }</span><br/><span>  ]</span><br/><span>}</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

---

# Worker puede leer cuarentena

<pre class="overflow-visible! px-0!" data-start="2167" data-end="2401"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="relative"><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼd ͼr"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span>{</span><br/><span>  "Version": </span><span class="ͼk">"2012-10-17"</span><span>,</span><br/><span>  "Statement": [</span><br/><span>    {</span><br/><span>      "Effect": </span><span class="ͼk">"Allow"</span><span>,</span><br/><span>      "Action": [</span><br/><span></span><span class="ͼk">"s3:GetObject"</span><br/><span>      ],</span><br/><span>      "Resource": [</span><br/><span></span><span class="ͼk">"arn:aws:s3:::uploads-quarantine/*"</span><br/><span>      ]</span><br/><span>    }</span><br/><span>  ]</span><br/><span>}</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

---

# Público solo lectura gallery-public

<pre class="overflow-visible! px-0!" data-start="2447" data-end="2701"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="relative"><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼd ͼr"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span>{</span><br/><span>  "Version": </span><span class="ͼk">"2012-10-17"</span><span>,</span><br/><span>  "Statement": [</span><br/><span>    {</span><br/><span>      "Effect": </span><span class="ͼk">"Allow"</span><span>,</span><br/><span>      "Principal": </span><span class="ͼk">"*"</span><span>,</span><br/><span>      "Action": [</span><br/><span></span><span class="ͼk">"s3:GetObject"</span><br/><span>      ],</span><br/><span>      "Resource": [</span><br/><span></span><span class="ͼk">"arn:aws:s3:::gallery-public/*"</span><br/><span>      ]</span><br/><span>    }</span><br/><span>  ]</span><br/><span>}</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

---

# Lo MÁS importante para tu defensa

Debes explicar:

## “por qué separar buckets”

Porque:

* reduce impacto
* evita exposición accidental
* permite cuarentena
* facilita auditoría
* limita movimiento lateral

Eso suena MUY profesional.

---

# Riesgos si NO usas IAM

Muy importante decir esto.

Si usas una sola credencial admin para todo:

* cualquier vulnerabilidad backend compromete TODOS los archivos
* el atacante puede:
* borrar buckets
* publicar malware
* exfiltrar imágenes
* modificar evidencia

---

# Diseño ideal para tu proyecto

## Backend

Credencial:

<pre class="overflow-visible! px-0!" data-start="3285" data-end="3328"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute end-1.5 top-1 z-2 md:end-2 md:top-1"></div><div class="relative"><div class="pe-11 pt-3"><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼd ͼr"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span>backend-upload-user</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

Permisos:

* PutObject cuarentena
* GetObject metadata

---

## Worker

Credencial:

<pre class="overflow-visible! px-0!" data-start="3412" data-end="3456"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute end-1.5 top-1 z-2 md:end-2 md:top-1"></div><div class="relative"><div class="pe-11 pt-3"><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼd ͼr"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span>steg-analysis-worker</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

Permisos:

* leer cuarentena
* mover a public/rejected

---

## Supervisor

NO acceso directo a MinIO.

Todo pasa por backend.

Eso es MUY importante arquitectónicamente.

---

# Buenas prácticas clave

## Nunca:

* poner credenciales MinIO en frontend
* usar root credentials en backend
* hacer buckets privados públicos accidentalmente

---

# URLs temporales

MUY buena práctica.

En vez de:

<pre class="overflow-visible! px-0!" data-start="3850" data-end="3890"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute end-1.5 top-1 z-2 md:end-2 md:top-1"></div><div class="relative"><div class="pe-11 pt-3"><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼd ͼr"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span>/public/file.jpg</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

usas:

# presigned URLs

Expiran en:

* 1 min
* 5 min
* etc.

Eso evita:

* scraping masivo
* acceso indefinido

---

# Cómo quedaría en Docker Compose

Muy elegante para defensa:

<pre class="overflow-visible! px-0!" data-start="4070" data-end="4154"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="relative"><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼd ͼr"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span>services:</span><br/><span>  backend:</span><br/><span>  postgres:</span><br/><span>  redis:</span><br/><span>  minio:</span><br/><span>  worker:</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

Eso visualmente da impresión de:

* microservicios
* separación
* arquitectura moderna

---

# Lo más importante conceptualmente

Tu proyecto NO trata solo de:

> “guardar imágenes”.

Trata de:

> controlar el ciclo de vida seguro de archivos potencialmente maliciosos.

Y MinIO + IAM ayuda EXACTAMENTE a eso.
