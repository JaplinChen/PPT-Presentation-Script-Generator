param(
    [string]$LogPath,
    [string]$Title
)

try {
    # Set Window Title
    $Host.UI.RawUI.WindowTitle = $Title

    # Wait briefly for title to propagate
    Start-Sleep -Milliseconds 500

    # Check for duplicates (We expect at least 1: ourselves)
    # If more than 1 window has this title, it means a previous instance exists.
    # We should exit to avoid clutter.
    $procs = Get-Process | Where-Object { $_.MainWindowTitle -eq $Title }

    if ($procs.count -gt 1) {
        Write-Host "⚠️  Monitor window for '$Title' is already open."
        Write-Host "   Closing this duplicate instance..."
        Start-Sleep -Seconds 2
        exit
    }

    # Set Output Encoding to UTF-8
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8

    Write-Host "=================================================="
    Write-Host "   MONITORING: $Title"
    Write-Host "   FILE: $LogPath"
    Write-Host "=================================================="

    if (-not (Test-Path $LogPath)) {
        throw "Log file not found: $LogPath"
    }

    # Tail the log file with UTF8 encoding
    Get-Content $LogPath -Wait -Tail 20 -Encoding UTF8
}
catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    Write-Host "Script Args: LogPath='$LogPath', Title='$Title'"
    Read-Host "Press Enter to exit..."
}
