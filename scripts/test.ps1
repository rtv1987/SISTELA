param([switch]$RequireFixtures, [switch]$E2E)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
& .\.venv\Scripts\ruff.exe check .
if ($LASTEXITCODE -ne 0) { throw 'Lint failed.' }
$testArgs = @('-m', 'pytest', '-q')
if ($RequireFixtures) { $testArgs += '--require-fixtures' }
& .\.venv\Scripts\python.exe @testArgs
if ($LASTEXITCODE -ne 0) { throw 'Tests failed.' }
& .\.venv\Scripts\python.exe -m alembic check
if ($LASTEXITCODE -ne 0) { throw 'Migration check failed. Run alembic upgrade head first.' }
Push-Location frontend
try {
    & pnpm test
    if ($LASTEXITCODE -ne 0) { throw 'Frontend tests failed.' }
    & pnpm lint
    if ($LASTEXITCODE -ne 0) { throw 'Frontend lint failed.' }
    & pnpm build
    if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
    if ($E2E) {
        & pnpm test:e2e
        if ($LASTEXITCODE -ne 0) { throw 'Browser tests failed.' }
    }
} finally { Pop-Location }
