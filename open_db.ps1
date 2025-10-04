# PowerShell helper to open the sqlite DB with the default application (DB Browser for SQLite, etc.)
$path = Join-Path -Path (Get-Location) -ChildPath "Backend\code\db.sqlite3"
if (-Not (Test-Path $path)) {
    Write-Error "DB file not found at $path"
    exit 1
}
Start-Process -FilePath $path
