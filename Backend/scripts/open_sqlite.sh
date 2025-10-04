#!/usr/bin/env bash
# Cross-platform helper that opens Backend/code/db.sqlite3 using the default DB browser on the host
# On Windows this will attempt to open with 'start', on macOS 'open', on Linux 'xdg-open'.
DB_PATH="$(pwd)/code/db.sqlite3"
if [ ! -f "$DB_PATH" ]; then
  echo "SQLite DB not found at $DB_PATH"
  exit 1
fi
case "$(uname -s)" in
  Darwin)
    open "$DB_PATH" ;;
  Linux)
    xdg-open "$DB_PATH" || echo "Install a DB browser or xdg-open is missing" ;;
  MINGW*|MSYS*|CYGWIN*|Windows_NT)
    cmd.exe /C start "" "$(wslpath -w "$DB_PATH" 2>/dev/null || echo $DB_PATH)" || powershell.exe -Command "Start-Process -FilePath '$DB_PATH'" ;;
  *)
    echo "Platform not recognized. Open $DB_PATH with your favorite SQLite browser." ;;
esac
