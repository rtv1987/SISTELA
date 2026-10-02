param([string]$Python = '', [string]$Makensis = '')
$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
Set-Location -LiteralPath $repoRoot
if (-not $Python) { $Python = Join-Path $repoRoot '.venv\Scripts\python.exe' }
if (-not (Test-Path -LiteralPath $Python)) { throw 'Run developer setup first or specify -Python.' }
$version = (& $Python -c "from sistela.version import VERSION; print(VERSION)").Trim()
if ($version -notmatch '^\d+\.\d+\.\d+$') { throw 'Invalid application version.' }
$releaseInstaller = Join-Path $repoRoot "dist\windows\SISTELA-Assistant-Setup-$version.exe"
$releasePortable = Join-Path $repoRoot "dist\windows\SISTELA-Assistant-Portable-$version.zip"
if ((Test-Path -LiteralPath $releaseInstaller) -or (Test-Path -LiteralPath $releasePortable)) {
    throw 'This release already exists. Preserve it and make an explicit version decision before building.'
}
# A release cannot silently omit either private production regression fixture.
& $Python -m pytest tests/test_pdf.py tests/test_pdf_structure.py --require-fixtures -q
if ($LASTEXITCODE -ne 0) { throw 'PDF release regressions failed or a required real fixture is missing.' }
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
& $Python -c "import hashlib,json,pathlib,sys; p=pathlib.Path(sys.argv[1]); files={str(f.relative_to(p)).replace(chr(92),'/'):hashlib.sha256(f.read_bytes()).hexdigest() for f in p.rglob('*') if f.is_file() and f.name!='INSTALL-MANIFEST.json'}; (p/'INSTALL-MANIFEST.json').write_text(json.dumps(files,sort_keys=True),encoding='utf-8')" $bundlePath
if ($LASTEXITCODE -ne 0) { throw 'Bundle integrity manifest failed.' }
& "$bundlePath\SISTELA-Assistant.exe" --verify-install
if ($LASTEXITCODE -ne 0) { throw 'Frozen dependency/integrity verification failed.' }
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
& $Python scripts/verify_windows_release.py $installerPath $portablePath
if ($LASTEXITCODE -ne 0) { throw 'Installer, portable and packaged runtime version verification failed.' }
$checksums = Get-ChildItem -LiteralPath $outputPath -File | Where-Object { $_.Name -match '^SISTELA-Assistant-(Setup-.*\.exe|Portable-.*\.zip)$' } | ForEach-Object {
    $hash = Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256
    $hash.Hash.ToLower() + '  ' + $_.Name
}
$checksums | Set-Content -LiteralPath (Join-Path $outputPath 'SHA256SUMS.txt') -Encoding ASCII
$checksums | Set-Content -LiteralPath (Join-Path $outputPath "SHA256SUMS-$version.txt") -Encoding ASCII
Write-Output "Installer: $installerPath"
Write-Output $checksums
