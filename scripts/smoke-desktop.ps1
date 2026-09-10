# Launch the built application with isolated settings, without capturing audio.
$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $PSScriptRoot
$SmokeDir = Join-Path $ProjectDir ("build\smoke-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $SmokeDir | Out-Null
$ConfigPath = Join-Path $SmokeDir "config.json"
'{"host":"127.0.0.1","port":18765}' | Set-Content -LiteralPath $ConfigPath -Encoding ASCII
$PreviousLocalAppData = $env:LOCALAPPDATA
$AppProcess = $null
Add-Type @'
using System;
using System.Runtime.InteropServices;
using System.Text;
public static class DesktopSmokeWindow {
    private delegate bool Callback(IntPtr window, IntPtr parameter);
    [DllImport("user32.dll")]
    private static extern bool EnumWindows(Callback callback, IntPtr parameter);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    private static extern int GetWindowText(IntPtr window, StringBuilder title, int size);
    public static IntPtr FindProcessWindow(uint processId) {
        IntPtr found = IntPtr.Zero;
        EnumWindows((window, parameter) => {
            uint owner;
            GetWindowThreadProcessId(window, out owner);
            var title = new StringBuilder(256);
            GetWindowText(window, title, title.Capacity);
            if (owner == processId && title.ToString() == "Live Twitch Translator") { found = window; return false; }
            return true;
        }, IntPtr.Zero);
        return found;
    }
    [DllImport("user32.dll")]
    public static extern uint GetWindowThreadProcessId(IntPtr window, out uint processId);
    [DllImport("user32.dll")]
    public static extern bool PostMessage(IntPtr window, uint message, IntPtr wParam, IntPtr lParam);
}
'@
try {
    $env:LOCALAPPDATA = $SmokeDir
    $AppProcess = Start-Process -FilePath (Join-Path $ProjectDir "dist\LiveTwitchTranslator\LiveTwitchTranslator.exe") `
        -ArgumentList @("--config", ('"' + $ConfigPath + '"')) -WindowStyle Hidden -PassThru
    $Ready = $false
    for ($Attempt = 0; $Attempt -lt 60; $Attempt++) {
        if ($AppProcess.HasExited) { throw "Executable exited before startup" }
        try {
            $Response = Invoke-RestMethod "http://127.0.0.1:18765/api/status" -TimeoutSec 1
            $WindowHandle = [DesktopSmokeWindow]::FindProcessWindow($AppProcess.Id)
            [uint32]$WindowProcessId = 0
            $null = [DesktopSmokeWindow]::GetWindowThreadProcessId($WindowHandle, [ref]$WindowProcessId)
            if ($Response.message -and $WindowProcessId -eq $AppProcess.Id) { $Ready = $true; break }
        } catch { }
        Start-Sleep -Milliseconds 500
    }
    if (-not $Ready) { throw "Desktop did not become ready; inspect $SmokeDir" }
    $Page = Invoke-WebRequest "http://127.0.0.1:18765/settings" -UseBasicParsing
    if ($Page.Content -notmatch 'Live translator settings') { throw "Settings page missing" }
    $Overlay = Invoke-WebRequest "http://127.0.0.1:18765/" -UseBasicParsing
    if ($Overlay.Content -notmatch 'Live English captions') { throw "Overlay missing" }
    $null = Invoke-RestMethod "http://127.0.0.1:18765/api/audio-sources"
    $TermsPath = Join-Path $SmokeDir "LiveTwitchTranslator\highlight_terms.txt"
    if (-not (Test-Path -LiteralPath $TermsPath) -or (Get-Item -LiteralPath $TermsPath).Length -ne 0) {
        throw "First-run terms file is missing or not empty"
    }
    if (-not [DesktopSmokeWindow]::PostMessage($WindowHandle, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero)) { throw "Desktop window did not accept close" }
    if (-not $AppProcess.WaitForExit(15000)) { throw "Application did not shut down" }
    if ($AppProcess.ExitCode -ne 0) { throw "Application exited with an error" }
    Write-Host "DESKTOP_SMOKE_PASSED: window, server, overlay, audio enumeration, first-run files and shutdown"
} finally {
    $env:LOCALAPPDATA = $PreviousLocalAppData
    if ($AppProcess -and -not $AppProcess.HasExited) { Stop-Process -Id $AppProcess.Id }
}
