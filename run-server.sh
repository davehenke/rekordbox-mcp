#!/bin/bash
cd "$(dirname "$0")"

LOG_FILE="rekordbox_startup.log"

# Function to log with timestamp
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

log "🎵 Starting Rekordbox MCP Server..."

# Check if pyrekordbox key is available
log "🔑 Checking rekordbox database key..."

# Test if database connection works
if ! uv run python -c "
import pyrekordbox
db = pyrekordbox.Rekordbox6Database()
content = list(db.get_content())
print(f'✅ Database key working! Found {len(content)} tracks.')
" >> "$LOG_FILE" 2>&1; then
    log "❌ Database key not found or not working."
    log "🔧 Attempting to download key..."
    
    # Try to download the key
    if uv run python -m pyrekordbox download-key >> "$LOG_FILE" 2>&1; then
        log "✅ Key downloaded successfully!"
        
        # Test again
        if uv run python -c "
import pyrekordbox
db = pyrekordbox.Rekordbox6Database()
content = list(db.get_content())
print(f'✅ Database connection verified! Found {len(content)} tracks.')
" >> "$LOG_FILE" 2>&1; then
            log "✅ Database setup complete!"
        else
            log "❌ Database still not accessible after key download."
            log "   Please check that rekordbox is not running and try again."
            exit 1
        fi
    else
        log "❌ Failed to download key."
        log "   Please run: uv run python -m pyrekordbox download-key"
        log "   Or check the setup guide for manual key extraction."
        exit 1
    fi
fi

log "🚀 Starting rekordbox MCP server..."
log "   This will connect to the database on startup."
log "   If connection fails, the server will exit automatically."
exec uv run rekordbox-mcp --log-level DEBUG "$@"