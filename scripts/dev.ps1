param([switch]$SkipBuild)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
if (-not $SkipBuild) {
    Push-Location frontend
    try {
        & pnpm build
        if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed. Run setup.ps1 first.' }
    } finally { Pop-Location }
}
& .\.venv\Scripts\python.exe -m alembic upgrade head
if ($LASTEXITCODE -ne 0) { throw 'Migration failed.' }
& .\.venv\Scripts\python.exe -m uvicorn sistela.api:create_app --factory --host 127.0.0.1 --port 8000
