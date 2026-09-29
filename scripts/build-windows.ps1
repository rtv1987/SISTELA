param([string]$Python = '', [string]$Makensis = '')
$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
Set-Location -LiteralPath $repoRoot
if (-not $Python) { $Python = Join-Path $repoRoot '.venv\Scripts\python.exe' }
if (-not (Test-Path -LiteralPath $Python)) { throw 'Run developer setup first or specify -Python.' }
$outputPath = [IO.Path]::GetFullPath((Join-Path $repoRoot 'dist\windows'))
$buildPath = [IO.Path]::GetFullPath((Join-Path $repoRoot 'tmp\windows-build'))
foreach ($targetPath in @($outputPath, $buildPath)) {
    if (-not $targetPath.StartsWith($repoRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Build path escaped repository.' }
    New-Item -ItemType Directory -Force -Path $targetPath | Out-Null
}
$env:PYTHONUTF8 = '1'
& $Python -m pip install -r requirements-lock.txt
if ($LASTEXITCODE -ne 0) { throw 'Runtime dependencies failed.' }
& $Python -m pip install --no-deps -e .
if ($LASTEXITCODE -ne 0) { throw 'Application metadata failed.' }
& $Python -m pip install -r packaging/requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw 'Build dependencies failed.' }
Push-Location frontend
try {
    & pnpm install --frozen-lockfile
    if ($LASTEXITCODE -ne 0) { throw 'Frontend dependencies failed.' }
    & pnpm build
    if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
} finally { Pop-Location }
$version = (& $Python -c "from sistela.version import VERSION; print(VERSION)").Trim()
if ($version -notmatch '^\d+\.\d+\.\d+$') { throw 'Invalid application version.' }
if (-not $Makensis) {
    $toolsPath = Join-Path $repoRoot 'tmp\build-tools'
    New-Item -ItemType Directory -Force -Path $toolsPath | Out-Null
    $archivePath = Join-Path $toolsPath 'nsis-3.12.zip'
    if (-not (Test-Path -LiteralPath $archivePath)) {
        & $Python -c "import urllib.request,sys; urllib.request.urlretrieve('https://downloads.sourceforge.net/project/nsis/NSIS%203/3.12/nsis-3.12.zip',sys.argv[1])" $archivePath
        if ($LASTEXITCODE -ne 0) { throw 'NSIS download failed.' }
    }
    $digest = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash
    if ($digest -ne '56581F90DB321581C5381193D796FFFCF2D24B2F8FED2160A6C6A3BAA67F2C4F') { throw 'NSIS checksum mismatch.' }
    Expand-Archive -LiteralPath $archivePath -DestinationPath $toolsPath -Force
    $Makensis = Join-Path $toolsPath 'nsis-3.12\makensis.exe'
}
& $Python -m PyInstaller --clean --noconfirm --distpath $outputPath --workpath $buildPath packaging/windows.spec
if ($LASTEXITCODE -ne 0) { throw 'Backend packaging failed.' }
$bundlePath = Join-Path $outputPath 'SISTELA-Assistant'
$manifest = Join-Path $buildPath 'uninstall-files.nsh'
# Delete only shipped files, never recursively delete a user-selected installation directory.
$entries = @()
Get-ChildItem -LiteralPath $bundlePath -File -Recurse | ForEach-Object {
    $relative = $_.FullName.Substring($bundlePath.Length + 1)
    $entries += 'Delete "$INSTDIR\' + $relative + '"'
}
Get-ChildItem -LiteralPath $bundlePath -Directory -Recurse | Sort-Object { $_.FullName.Length } -Descending | ForEach-Object {
    $relative = $_.FullName.Substring($bundlePath.Length + 1)
    $entries += 'RMDir "$INSTDIR\' + $relative + '"'
}
$entries | Set-Content -LiteralPath $manifest -Encoding UTF8
& $Makensis /INPUTCHARSET UTF8 "/DVersion=$version" "/DOutput=$outputPath" "/DBundle=$bundlePath" "/DDeleteManifest=$manifest" packaging/installer.nsi
if ($LASTEXITCODE -ne 0) { throw 'Installer compilation failed.' }
$portablePath = Join-Path $outputPath "SISTELA-Assistant-Portable-$version.zip"
Compress-Archive -LiteralPath $bundlePath -DestinationPath $portablePath -Force
$installerPath = Join-Path $outputPath "SISTELA-Assistant-Setup-$version.exe"
$checksums = @($installerPath, $portablePath) | ForEach-Object {
    $hash = Get-FileHash -LiteralPath $_ -Algorithm SHA256
    $hash.Hash.ToLower() + '  ' + [IO.Path]::GetFileName($_)
}
$checksums | Set-Content -LiteralPath (Join-Path $outputPath 'SHA256SUMS.txt') -Encoding ASCII
Write-Output "Installer: $installerPath"
Write-Output $checksums
