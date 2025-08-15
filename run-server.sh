#!/bin/bash
cd "$(dirname "$0")"

echo "🎵 Starting Rekordbox MCP Server..." >&2

# Check if pyrekordbox key is available
echo "🔑 Checking rekordbox database key..." >&2

# Test if database connection works
if ! uv run python -c "
import pyrekordbox
db = pyrekordbox.Rekordbox6Database()
content = list(db.get_content())
print(f'✅ Database key working! Found {len(content)} tracks.')
" 2>&1; then
    echo "❌ Database key not found or not working." >&2
    echo "🔧 Attempting to download key..." >&2
    
    # Try to download the key
    if uv run python -m pyrekordbox download-key; then
        echo "✅ Key downloaded successfully!" >&2
        
        # Test again
        if uv run python -c "
import pyrekordbox
db = pyrekordbox.Rekordbox6Database()
content = list(db.get_content())
print(f'✅ Database connection verified! Found {len(content)} tracks.')
" 2>&1; then
            echo "✅ Database setup complete!" >&2
        else
            echo "❌ Database still not accessible after key download." >&2
            echo "   Please check that rekordbox is not running and try again." >&2
            exit 1
        fi
    else
        echo "❌ Failed to download key." >&2
        echo "   Please run: uv run python -m pyrekordbox download-key" >&2
        echo "   Or check the setup guide for manual key extraction." >&2
        exit 1
    fi
fi

echo "🚀 Starting rekordbox MCP server..." >&2
echo "   This will connect to the database on startup." >&2
echo "   If connection fails, the server will exit automatically." >&2
exec uv run rekordbox-mcp "$@"