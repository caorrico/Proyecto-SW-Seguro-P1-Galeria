$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $Root "backend"
$FrontendDir = Join-Path $Root "frontend"
$Python = Join-Path $BackendDir ".venv\Scripts\python.exe"
$NodeDir = "C:\Program Files\nodejs"
$Npm = Join-Path $NodeDir "npm.cmd"

Write-Host "Iniciando SecureFrame Gallery en terminales visibles..." -ForegroundColor Cyan

if (-not (Test-Path $Python)) {
    $SystemPython = Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"
    if (-not (Test-Path $SystemPython)) {
        throw "No se encontro Python. Instala Python 3.12 o ajusta la ruta en start_all.ps1."
    }

    Write-Host "Creando entorno virtual backend\\.venv..." -ForegroundColor Yellow
    & $SystemPython -m venv (Join-Path $BackendDir ".venv")
}

if (-not (Test-Path $Npm)) {
    throw "No se encontro npm en $Npm. Instala Node.js LTS o ajusta la ruta en start_all.ps1."
}

Write-Host "Levantando infraestructura local (PostgreSQL + MinIO)..." -ForegroundColor Yellow
docker compose up -d

Write-Host "Esperando PostgreSQL..." -ForegroundColor Yellow
$maxWait = 40
$waited = 0
while ($waited -lt $maxWait) {
    docker exec secureframe_db pg_isready -U secureframe_user -d secureframe_gallery | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] PostgreSQL listo" -ForegroundColor Green
        break
    }
    Start-Sleep -Seconds 2
    $waited += 2
}

if ($waited -ge $maxWait) {
    throw "PostgreSQL no respondio a tiempo."
}

$envContent = @"
DATABASE_URL=postgresql+psycopg2://secureframe_user:change-this-postgres-password@localhost:5434/secureframe_gallery
SECRET_KEY=change-this-development-secret-before-production
MINIO_URL=localhost:9393
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=change-this-minio-secret
FRONTEND_ORIGIN=http://localhost:5173
"@
Set-Content -Path (Join-Path $BackendDir ".env") -Value $envContent -NoNewline

Write-Host "Instalando/verificando dependencias del backend..." -ForegroundColor Yellow
& $Python -m pip install -r (Join-Path $BackendDir "requirements.txt")

Write-Host "Creando/actualizando usuario admin..." -ForegroundColor Yellow
& $Python (Join-Path $Root "seed_admin.py")

Write-Host "Instalando/verificando dependencias del frontend..." -ForegroundColor Yellow
$env:Path = "$NodeDir;$env:Path"
Push-Location $FrontendDir
try {
    & $Npm install
}
finally {
    Pop-Location
}

$BackendCommand = @"
`$env:DATABASE_URL='postgresql+psycopg2://secureframe_user:change-this-postgres-password@localhost:5434/secureframe_gallery'
`$env:SECRET_KEY='change-this-development-secret-before-production'
`$env:MINIO_URL='localhost:9393'
`$env:MINIO_ACCESS_KEY='minioadmin'
`$env:MINIO_SECRET_KEY='change-this-minio-secret'
`$env:FRONTEND_ORIGIN='http://localhost:5173'
cd '$BackendDir'
& '$Python' -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
"@

$FrontendCommand = @"
`$env:Path='$NodeDir;' + `$env:Path
cd '$FrontendDir'
& '$Npm' run dev -- --host 0.0.0.0 --port 5173
"@

Write-Host "Abriendo terminal visible del backend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $BackendCommand

Write-Host "Abriendo terminal visible del frontend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $FrontendCommand

Write-Host ""
Write-Host "=== Sistema levantandose en terminales visibles ===" -ForegroundColor Green
Write-Host "- Backend:  http://localhost:8000"
Write-Host "- Frontend: http://localhost:5173"
Write-Host "- MinIO:    http://localhost:9001"
Write-Host "- Admin:    admin / admin123" -ForegroundColor Cyan
