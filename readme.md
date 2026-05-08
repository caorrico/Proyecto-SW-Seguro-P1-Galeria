# SecureFrame Gallery - Seguridad Grado Militar 🛡️

SecureFrame Gallery es una plataforma de gestión de álbumes e imágenes diseñada bajo los principios de **Seguridad por Diseño** y alineada con los estándares **OWASP ASVS (Nivel 2)**.

## 🚀 Arquitectura de Seguridad Implementada

### 1. Gestión de Almacenamiento (Estrategia Multi-Bucket MinIO)
Siguiendo la arquitectura de aislamiento físico, el sistema utiliza tres buckets independientes para gestionar el ciclo de vida de los archivos:

| Bucket | Propósito | Nivel de Acceso |
| --- | --- | --- |
| `uploads-quarantine` | Punto de entrada para todas las subidas. Zona de análisis. | **Restringido**: Solo Backend. |
| `gallery-public` | Almacenamiento de imágenes aprobadas por supervisión. | **Público**: Vía Proxy/Presigned URL. |
| `rejected-evidence` | Depósito forense para archivos sospechosos o rechazados. | **Crítico**: Solo Supervisor/Admin. |

**Proxy de Streaming**: El acceso a los archivos se realiza a través de un proxy en el backend que valida permisos y genera **Presigned URLs de corta duración (5 min)**, evitando la exposición directa del almacenamiento S3.

### 2. Pipeline de Procesamiento Seguro (Anti-Malware & Privacidad)
Cada archivo subido es sometido a un proceso de limpieza y validación antes de ser persistido:

*   **Validación de Magic Bytes**: Se inspecciona el encabezado binario del archivo para confirmar su tipo real, neutralizando ataques de extensión falsa.
*   **Sanitización por Re-encoding**: Las imágenes se abren y se vuelven a procesar mediante `Pillow`. Este proceso destruye exploits embebidos en segmentos de datos no estándar y ataques "polyglot".
*   **Strip de EXIF**: Eliminación automática de metadatos sensibles (GPS, modelo de cámara, fechas originales) para proteger la privacidad del usuario.
*   **Prevención de DoS**: Límite estricto de **10MB** por archivo y validación de dimensiones para evitar "bombas de descompresión".

### 3. Motor de Detección de Esteganografía
El sistema integra un analizador forense que etiqueta los archivos como `CLEAN` o `SUSPICIOUS`:

*   **Análisis LSB (Least Significant Bit)**: Detecta anomalías estadísticas que sugieren mensajes ocultos en los píxeles.
*   **Análisis de Entropía**: Mide la aleatoriedad de los datos por zonas para identificar payloads cifrados.
*   **Detección EOF (End of File)**: Escaneo de datos extra pegados tras el marcador de fin de archivo estándar (técnica clásica de ocultación).

### 4. Autenticación y Sesiones Blindadas
*   **Hasing Argon2**: Almacenamiento de contraseñas con el estándar más robusto de la industria.
*   **Detección de Reutilización de Tokens (JTI)**: Cada sesión tiene un identificador único. Si se detecta el uso de un token de refresco ya invalidado (ataque de replay), el sistema revoca automáticamente **toda la familia de sesiones** del usuario.
*   **Cookies HttpOnly & Secure**: Prevención de robo de tokens vía ataques XSS.
*   **Anti-Enumeración**: Implementación de *timing equivalence* para evitar el descubrimiento de cuentas mediante tiempos de respuesta.

## 🔍 Auditoría y Cumplimiento

El proyecto incluye herramientas para verificar la integridad del sistema en tiempo real:

### Script de Auditoría Automatizada
Ejecuta el siguiente comando para generar un reporte de cumplimiento:

```bash
wsl chmod +x security_audit.sh
wsl ./security_audit.sh
```

Este script realiza:
*   **SCA (pip-audit)**: Escaneo de vulnerabilidades conocidas (CVEs) en dependencias.
*   **SAST (Bandit & Semgrep)**: Análisis estático del código fuente buscando fallos de lógica de seguridad.

Los resultados se guardan en el archivo `SECURITY_REPORT.md`.

## 🛠️ Ejecución del Proyecto

### Backend (WSL / Linux)
1. Levantar infraestructura (PostgreSQL + MinIO): `docker compose up -d`
2. Configurar entorno: `cp .env.example .env` (y ajustar variables).
3. Instalar y correr:
   ```bash
   cd backend
   python -m venv .venv_wsl
   source .venv_wsl/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

---
*Este proyecto es parte del curso de Desarrollo Seguro - ESPE 2026.*
