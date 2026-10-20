# ===========================================================================
#  One-time setup: make the camera stream start automatically at every logon,
#  and start it right now.
#  Run it by double-clicking install_autostart.bat (no admin needed).
# ===========================================================================

$ErrorActionPreference = 'Stop'

$dir     = $PSScriptRoot
$vbs     = Join-Path $dir 'start_background.vbs'
$startup = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Startup'
$lnkPath = Join-Path $startup 'CameraStreamer.lnk'

Write-Host ''
Write-Host '  CAMERA STREAM - AUTO-START SETUP' -ForegroundColor Cyan
Write-Host '  ---------------------------------' -ForegroundColor DarkGray
Write-Host "  Folder : $dir"
Write-Host ''

# ---- sanity checks -------------------------------------------------------
if (-not (Test-Path $vbs)) {
    Write-Host "  [X] start_background.vbs is missing from this folder." -ForegroundColor Red
    Write-Host '      Keep all files together and try again.'
    exit 1
}
if (-not (Test-Path (Join-Path $dir 'streamer.py'))) {
    Write-Host '  [X] streamer.py is missing from this folder.' -ForegroundColor Red
    exit 1
}

$pythonw = 'C:\Users\user\AppData\Local\Programs\Python\Python314\pythonw.exe'
if (-not (Test-Path $pythonw)) {
    $found = Get-Command pythonw.exe -ErrorAction SilentlyContinue
    if ($found) { $pythonw = $found.Source }
    else {
        Write-Host '  [X] pythonw.exe was not found. Install Python or fix its path.' -ForegroundColor Red
        exit 1
    }
}
Write-Host "  Python : $pythonw"

# ---- 1. install the autostart shortcut ----------------------------------
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut($lnkPath)
$sc.TargetPath       = 'wscript.exe'
$sc.Arguments        = '"' + $vbs + '"'
$sc.WorkingDirectory = $dir
$sc.Description      = 'Auto-start live camera streamer to cloud VPS'
$sc.Save()

if (Test-Path $lnkPath) {
    Write-Host '  [OK] Auto-start installed (runs at every logon).' -ForegroundColor Green
} else {
    Write-Host '  [X] Could not create the startup shortcut.' -ForegroundColor Red
    exit 1
}

# ---- 2. start streaming right now ---------------------------------------
# The streamer holds port 47991 while it runs. If we can bind that port, no
# streamer is running; if the bind fails, one already owns it.
function Test-StreamerRunning {
    $listener = $null
    try {
        $listener = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Loopback, 47991)
        $listener.Start()
        $listener.Stop()
        return $false
    } catch {
        return $true
    } finally {
        if ($listener) { try { $listener.Stop() } catch { } }
    }
}

if (Test-StreamerRunning) {
    Write-Host '  [OK] Streamer already running - not starting a second copy.' -ForegroundColor Green
} else {
    Start-Process -FilePath 'wscript.exe' -ArgumentList ('"' + $vbs + '"') -WorkingDirectory $dir
    Write-Host '  [OK] Streamer started in the background.' -ForegroundColor Green
}

# ---- 3. show the watch links --------------------------------------------
$url = 'http://87.232.72.64:8088'
Write-Host ''
Write-Host '  WATCH YOUR CAMERA (from anywhere):' -ForegroundColor Cyan
Write-Host "    $url" -ForegroundColor Yellow
Write-Host ''
Write-Host '  Give it ~15 seconds to appear, then open the link above.'
Write-Host '  Log file: ' -NoNewline
Write-Host (Join-Path $dir 'streamer.log') -ForegroundColor DarkGray
Write-Host ''
