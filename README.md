# Rekordbox MCP Server

A comprehensive Model Context Protocol (MCP) server for rekordbox database management with real-time database access.

**Built using [pyrekordbox](https://github.com/dylanljones/pyrekordbox)** - This project is not affiliated with the pyrekordbox project or its maintainers.

## Features

### 🗄️ Database Access
- **Direct SQLite Database Connection**: Access the encrypted rekordbox database directly using pyrekordbox
- **Real-time Queries**: Search and filter tracks with comprehensive criteria
- **Safe Mutation Operations**: Playlist management with automatic backups and safety annotations

### 🔍 Search & Discovery
- **Advanced Search**: Multi-field search across artist, title, genre, key, BPM, and more
- **Musical Key Filtering**: Find tracks in compatible keys for harmonic mixing
- **BPM Range Queries**: Search by tempo ranges for beatmatching
- **Rating and Play Count Filters**: Discover your most loved and most played tracks

### 📊 Analytics & Insights
- **Library Statistics**: Comprehensive stats including genre distribution, average BPM, total playtime
- **Play Count Analytics**: Track listening patterns and habits
- **Collection Insights**: Understand your music library composition
- **DJ History Access**: Full access to your DJ session history and performance data

### ⚙️ Database Operations
- **Playlist Management**: Create, modify, and delete playlists with safety protections
- **Batch Operations**: Add multiple tracks to playlists efficiently
- **History Analysis**: Access complete DJ session history and performance data
- **Library Statistics**: Comprehensive analytics and insights

## Architecture

This project consists of two complementary approaches:

### Python Server (Current)
- **FastMCP Framework**: Modern Python MCP server using FastMCP 2.0
- **pyrekordbox Integration**: Mature library for encrypted database access
- **Real-time Database Queries**: Direct SQLite operations with SQLCipher support
- **Production Ready**: Built-in logging, error handling, and safety features

### TypeScript Server (Legacy)
- **XML-based Access**: Uses rekordbox XML exports for read-only operations
- **MCP SDK**: Built with the official TypeScript MCP SDK
- **Static Analysis**: Perfect for analysis without database modification risk

## ⚠️ Important Safety Notice

**BACKUP YOUR REKORDBOX LIBRARY BEFORE USE**

This software directly accesses your rekordbox database for analysis and querying. While currently read-only, **always create a backup** of your entire rekordbox library before using this tool as a precautionary measure.

### Backup Requirements

**You should create a complete backup of your rekordbox library before using this software.** Consult rekordbox documentation or support resources for proper backup procedures for your specific setup and rekordbox version.

### Risk Acknowledgment

- ⚠️ **This project accesses your rekordbox database directly**
- ⚠️ **Use at your own risk - no warranty provided**  
- ⚠️ **Test thoroughly with backups before using on your main library**
- ⚠️ **The developers are not responsible for any data loss or damage**

**If you are not comfortable with these risks, use the read-only XML export functionality instead.**

## Quick Start

### Prerequisites
- Python 3.12+
- rekordbox 6 or 7 installed with an existing library
- **COMPLETE BACKUP** of your rekordbox library (see safety notice above)
- **rekordbox must be completely closed** when using this tool
- Access to your rekordbox database (automatic detection supported)

### Installation

```bash
# Install dependencies with uv
uv sync

# Run the server
uv run rekordbox-mcp
```

### Configuration

The server supports both automatic database detection and manual configuration:

```bash
# Auto-detect rekordbox database (recommended)
uv run rekordbox-mcp

# Specify custom database path
uv run rekordbox-mcp --database-path /path/to/rekordbox/Pioneer
```

### MCP Client Setup

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "rekordbox-database": {
      "command": "uv",
      "args": ["run", "rekordbox-mcp"],
      "cwd": "/path/to/rekordbox-mcp"
    }
  }
}
```

## Available Tools

### Search & Query
- `search_tracks` - Advanced track search with multiple filters
- `get_track_details` - Detailed track information including metadata
- `get_library_stats` - Comprehensive library statistics
- `get_playlists` - List all playlists (including smart playlists)
- `get_playlist_tracks` - Get tracks in a specific playlist

### DJ History
- `get_history_sessions` - Browse all DJ session history
- `get_session_tracks` - Get full tracklist for any DJ session
- `get_recent_sessions` - Filter recent DJ sessions
- `get_history_stats` - Comprehensive DJ performance statistics
- `search_history_sessions` - Search sessions by date, tracks, etc.

### Database Operations
- `connect_database` - Establish database connection

### Resources
- `database-status` - Current connection status and basic stats

## Available MCP Tools

### Search & Discovery
- **`search_tracks`** - Advanced multi-field track search with filtering
- **`get_library_stats`** - Comprehensive library statistics and analytics

### Playlist Operations
- **`get_playlists`** - List all playlists including smart playlists
- **`create_playlist`** - Create new playlists ⚠️ (Mutation)
- **`add_track_to_playlist`** - Add single track to playlist ⚠️ (Mutation)
- **`add_tracks_to_playlist`** - Add multiple tracks to playlist in one operation ⚠️ (Mutation)
- **`remove_track_from_playlist`** - Remove track from playlist ⚠️ (Mutation)
- **`delete_playlist`** - Delete playlist permanently ⚠️ (Destructive)

### DJ History & Analytics
- **`get_recent_sessions`** - Access recent DJ session history
- **`get_session_tracks`** - Get tracks played in specific session
- **`get_history_stats`** - DJ performance statistics and insights

⚠️ **Mutation operations** modify your rekordbox database and create automatic backups  
⚠️ **Destructive operations** permanently delete data and require extra confirmation

## Examples

### Search for tracks by key and BPM
```python
# Find tracks in 5A key with BPM between 120-130
search_tracks(key="5A", bpm_min=120, bpm_max=130, limit=20)
```

### Access DJ History
```python
# Get recent DJ sessions
get_recent_sessions(days=30)

# Get tracks from a specific session
get_session_tracks(session_id="12345")
```


### Get library insights
```python
# Comprehensive library statistics
get_library_stats()

# DJ performance statistics
get_history_stats()
```

### Playlist Management
```python
# Create a new playlist
create_playlist(name="Hidden Bangers", parent_id="root")

# Add single track to playlist
add_track_to_playlist(playlist_id="136766232", track_id="218048716")

# Add multiple tracks efficiently (recommended for batch operations)
add_tracks_to_playlist(
    playlist_id="136766232", 
    track_ids=["218048716", "253968855", "148359536", "76341043"]
)

# Remove track from playlist
remove_track_from_playlist(playlist_id="136766232", track_id="218048716")

# Delete playlist (with safety confirmation)
delete_playlist(playlist_id="136766232")
```

## Safety Features

- **Automatic Backups**: All mutation operations create automatic database backups before changes
- **FastMCP Safety Annotations**: Proper safety hints for mutation and destructive operations
- **Smart Playlist Protection**: Prevents deletion of intelligent playlists
- **Connection Validation**: Validates database connections and access
- **Error Handling**: Comprehensive error handling with detailed logging and rollback
- **Input Validation**: Input validation for all database operations
- **Batch Operation Safety**: Detailed reporting on success/failure of batch operations

**⚠️ Important**: These safety features are supplementary protections. Always maintain your own backups and use this software at your own risk.

## Development

### Project Structure
```
rekordbox_mcp/
   __init__.py          # Package initialization
   server.py            # FastMCP server and tool definitions
   database.py          # Database connection and operations
   models.py            # Pydantic data models
```

### Running Tests
```bash
uv run pytest
```

### Code Quality
```bash
# Format code
uv run black rekordbox_mcp/

# Lint code
uv run ruff rekordbox_mcp/

# Type checking
uv run mypy rekordbox_mcp/
```

## License

MIT License

## Disclaimer

**⚠️ USE AT YOUR OWN RISK ⚠️**

- This project is **not affiliated** with AlphaTheta (Pioneer DJ) or the pyrekordbox project
- This software **directly accesses your rekordbox database**
- **No warranty or guarantee is provided**
- The developers are **not responsible** for any damage to your rekordbox library
- **You assume all risk** when using this software

**ALWAYS backup your rekordbox library before use. Test thoroughly with backup copies before using on your main library.**

By using this software, you acknowledge that you understand these risks and agree to use it at your own responsibility.
