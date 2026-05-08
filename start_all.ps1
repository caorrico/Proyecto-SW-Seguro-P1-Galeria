$ErrorActionPreference = "Stop"

Write-Host "Iniciando SecureFrame Gallery..." -ForegroundColor Cyan

# 1. Iniciar Base de Datos (Docker en WSL)
Write-Host "Levantando Base de Datos (PostgreSQL en WSL)..." -ForegroundColor Yellow
wsl docker compose up -d

# 2. Esperar a que la BD esté lista (dentro de WSL)
Write-Host "Esperando a que la BD responda..."
$maxWait = 30
$waited = 0
while ($waited -lt $maxWait) {
    wsl docker exec secureframe_db pg_isready -U secureframe_user -d secureframe_gallery
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Base de datos lista" -ForegroundColor Green
        break
    }
    Start-Sleep -Seconds 2
    $waited += 2
    Write-Host "  Esperando... ($waited s)" -ForegroundColor DarkGray
}

# 3. Actualizar .env para uso interno de WSL
# En WSL, conectamos a localhost:5434
$envContent = @"
DATABASE_URL=postgresql+psycopg2://secureframe_user:SUPER_PASSWORD@localhost:5434/secureframe_gallery
SECRET_KEY=una_clave_larga_y_random
MINIO_URL=localhost:9393
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=SUPER_SECRET
"@
Set-Content -Path "backend\.env" -Value $envContent -NoNewline

# 4. Iniciar Backend DENTRO de WSL
Write-Host "Iniciando Backend (FastAPI en WSL)..." -ForegroundColor Yellow
# Nos aseguramos de que el venv sea válido, instalamos dependencias, semilla de BD y corremos el servidor
$backendCmd = "wsl bash -c 'cd backend && ( [ ! -f .venv_wsl/bin/python3 ] && rm -rf .venv_wsl ); [ ! -d .venv_wsl ] && python3 -m venv .venv_wsl; ./.venv_wsl/bin/python3 -m pip install --upgrade pip && ./.venv_wsl/bin/python3 -m pip install -r requirements.txt && ./.venv_wsl/bin/python3 ../seed_admin.py && ./.venv_wsl/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload'"
Start-Process powershell -ArgumentList "-NoExit -Command `"$backendCmd`""

# 5. Iniciar Frontend (Windows)
Write-Host "Iniciando Frontend (Vite en Windows)..." -ForegroundColor Yellow
$frontendCmd = "cd frontend; npm install; npm run dev"
Start-Process powershell -ArgumentList "-NoExit -Command `"$frontendCmd`""

Write-Host ""
Write-Host "=== Sistema levantado ===" -ForegroundColor Green
Write-Host "- Backend:  http://localhost:8000 (vía WSL)"
Write-Host "- Frontend: http://localhost:5173"
Write-Host "- Admin:    admin / admin123" -ForegroundColor Cyan
