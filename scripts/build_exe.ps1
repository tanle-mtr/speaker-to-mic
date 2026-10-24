# 打包 SpeakerToMic 为单个无窗口 exe。
# 在仓库根目录运行： powershell -ExecutionPolicy Bypass -File scripts/build_exe.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

# 优先使用仓库内虚拟环境，否则回退到系统 python
$py = "python"
if (Test-Path (Join-Path $root ".venv\Scripts\python.exe")) {
    $py = Join-Path $root ".venv\Scripts\python.exe"
}

Push-Location $root
try {
    & $py -m PyInstaller --noconfirm --onefile --noconsole --name SpeakerToMic `
        --collect-all pyaudiowpatch `
        --collect-all sounddevice `
        (Join-Path "src" "speaker_to_mic.py")
    Write-Host "Done -> dist\SpeakerToMic.exe"
}
finally {
    Pop-Location
}
