# Rekordbox MCP Server

A powerful Model Context Protocol (MCP) server that transforms your rekordbox DJ library into an intelligent, queryable database. Perfect for DJs who want to analyze their music collection, create smart playlists, and integrate rekordbox data with AI assistants and other tools.

> **⚠️ IMPORTANT DISCLAIMER**: rekordbox is a trademark and product of AlphaTheta Corporation (formerly Pioneer DJ Corporation). This project is an unofficial, community-created tool that works with rekordbox XML exports. It is not affiliated with, endorsed by, or supported by AlphaTheta Corporation. Users assume all responsibility for using this software with their rekordbox data.

## 🎵 What is this?

This MCP server connects your exported rekordbox library to MCP-compatible applications like **Claude Code**, **Cursor**, **VS Code**, and other development environments. It provides intelligent querying, analytics, and playlist generation capabilities for your DJ library.

## ✨ Features

### Core Library Management
- **Advanced Search**: Multi-field search with unlimited results and sorting
- **Analytics Engine**: Group by genre, key, artist, year with aggregation (play count, total time)
- **Smart Filtering**: BPM ranges, play counts, ratings, release years
- **File System Integration**: Full file paths and filename access

### DJ-Specific Tools
- **Harmonic Mixing**: Find tracks by musical key (Camelot notation: 1A-12B)
- **BPM Analysis**: Range queries and tempo-based searches
- **Cue Point Management**: Access hot cues and memory cues
- **Playlist Operations**: Browse and query existing playlists

### Playlist Creation
- **Export Formats**: M3U8, M3U, PLS, and TXT playlists
- **Smart Playlists**: Create from search results automatically
- **File Integration**: Full file paths for external DJ software

### Data Insights
- **Most Played Tracks**: Discover your favorites by genre
- **Unplayed Gems**: Find neglected tracks in your collection  
- **Library Statistics**: Comprehensive analytics and breakdowns
- **Track Discovery**: Advanced filtering and recommendation queries

## 🚀 Quick Start

### 1. Export Your Rekordbox Library

**Required Step**: You must export your rekordbox library as XML first.

1. Open **rekordbox**
2. Go to **File** → **Export Collection in XML format**
3. Save the XML file (e.g., `rekordbox.xml`)

> ⚠️ **Important**: This server works with XML exports only.

### 2. Install the Server

```bash
git clone https://github.com/your-username/rekordbox-mcp
cd rekordbox-mcp
npm install
npm run build
```

### 3. Configure Your MCP Client

The server requires the path to your XML file as a startup argument:

```json
{
  "mcpServers": {
    "rekordbox": {
      "command": "node",
      "args": [
        "/path/to/rekordbox-mcp/dist/index.js",
        "/path/to/your/rekordbox.xml"
      ]
    }
  }
}
```

## 🛠️ Integration Guide

### Claude Code
Add to `~/.claude/mcp_servers.json`:
```json
{
  "mcpServers": {
    "rekordbox": {
      "command": "node",
      "args": [
        "/Users/yourname/rekordbox-mcp/dist/index.js",
        "/Users/yourname/rekordbox.xml"
      ]
    }
  }
}
```

### VS Code with MCP Extension
Add to VS Code MCP settings:
```json
{
  "mcp.servers": {
    "rekordbox": {
      "command": "node",
      "args": [
        "/path/to/rekordbox-mcp/dist/index.js", 
        "/path/to/rekordbox.xml"
      ]
    }
  }
}
```

### Cursor IDE
In Cursor settings, add:
```json
{
  "mcp": {
    "servers": {
      "rekordbox": {
        "command": "node",
        "args": [
          "/path/to/rekordbox-mcp/dist/index.js",
          "/path/to/rekordbox.xml"  
        ]
      }
    }
  }
}
```

### Other MCP Clients
Any MCP-compatible client can use this server. The key requirements:
- Node.js runtime available
- Path to compiled server (`dist/index.js`)
- Path to your rekordbox XML export as argument

## 🎛️ Available Tools (19 total)

### Search & Discovery
- `search_tracks` - Advanced multi-field search with sorting
- `get_most_played_tracks` - Your hits by genre  
- `get_top_rated_tracks` - Highest rated tracks
- `get_unplayed_tracks` - Discover neglected music
- `search_tracks_by_filename` - Find tracks by file name

### Analytics & Insights  
- `analyze_library` - Advanced analytics with grouping
- `get_library_stats` - Complete library breakdown
- `get_tracks_by_key` - Harmonic mixing queries
- `get_tracks_by_bpm_range` - Tempo-based filtering

### Track Details
- `get_track_details` - Full metadata including cue points
- `get_track_file_path` - Complete file system path
- `get_track_file_name` - Just the filename

### Playlist Operations
- `get_all_playlists` - Browse existing playlists
- `get_tracks_by_playlist` - Query playlist contents
- `create_playlist_file` - Export playlists (M3U8/PLS/etc)
- `create_playlist_from_search` - Generate smart playlists

### Data Management
- `update_track_play_count` - Modify play statistics
- `update_track_rating` - Update track ratings
- `validate_track_ids` - Check track ID validity

## 💡 Example Use Cases

### DJ Set Preparation
```
"Find me 20 house tracks in key 2A with high energy ratings, sorted by play count"

search_tracks: {
  genre: "house",
  key: "2A", 
  sort_by: "playCount",
  sort_order: "desc",
  limit: 20
}
```

### Harmonic Mixing
```
"Show me all tracks that mix well with this 2A track"

get_tracks_by_key: { key: "2B" }  # Perfect fifth
get_tracks_by_key: { key: "11A" } # Relative minor
get_tracks_by_key: { key: "3A" }  # Next in circle
```

### Smart Playlist Creation
```
"Create a workout playlist with high-energy tracks around 128 BPM"

create_playlist_from_search: {
  file_path: "/Users/me/workout.m3u8",
  playlist_name: "High Energy Workout",
  search_filters: {
    bpm_min: 126, 
    bpm_max: 130,
    rating: 4
  }
}
```

### Library Analysis
```
"What are my top 10 genres by total play time?"

analyze_library: {
  group_by: "genre",
  aggregate_by: "playTime", 
  top_n: 10
}
```

## 📊 What Data is Available?

The server parses your rekordbox XML export and provides access to:

### Track Metadata
- **Basic Info**: Title, Artist, Album, Genre, Year, Label
- **Technical**: BPM, Key (Camelot notation), Duration, File format
- **DJ Data**: Play count, Rating (0-5), Comments/Energy levels
- **File System**: Complete file paths and filenames

### Performance Data
- **Cue Points**: Hot cues (1-8) and memory cues with precise timing
- **Beat Grids**: Tempo changes and beat markers
- **Analysis**: Key detection and BPM analysis results

### Playlist Structure  
- **Hierarchical**: Nested playlist folders and organization
- **Track Lists**: Complete playlist contents with track references
- **Metadata**: Playlist names, track counts, creation dates

## ⚠️ Current Limitations

### XML-Based Approach
- **Manual Export Required**: Must export XML from rekordbox manually
- **No Real-time Sync**: Changes don't automatically reflect in rekordbox
- **Update Workflow**: Re-export XML when library changes significantly

### Data Scope
- **No Artwork**: Album covers not included in XML exports
- **No Waveforms**: Audio analysis data not available
- **Limited Metadata**: Some rekordbox-specific data may be missing

### File System Dependencies
- **Absolute Paths**: XML contains full file paths that may change
- **Missing Files**: Broken if tracks moved/deleted after export

## 🚀 Future Enhancements

We're continuously working to improve the rekordbox MCP server. Potential future features include:

- **Enhanced Analytics**: Advanced library insights and recommendations
- **Multiple Format Support**: Additional playlist and export formats
- **Performance Optimizations**: Faster processing of large libraries
- **Extended Metadata**: Support for additional rekordbox data fields

## 🤝 Contributing

This is an open-source project! Contributions are welcome:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and add tests
4. **Commit your changes**: `git commit -m 'Add amazing feature'`
5. **Push to the branch**: `git push origin feature/amazing-feature`
6. **Open a Pull Request**

### Development Setup
```bash
git clone https://github.com/your-username/rekordbox-mcp
cd rekordbox-mcp
npm install
npm run dev  # Watch mode for development
```

## 📄 Legal & License

### License
MIT License - see [LICENSE](LICENSE) file for details.

### Disclaimers & Legal Notices

**Trademark Notice**: rekordbox is a trademark of AlphaTheta Corporation. This project is not affiliated with, endorsed by, or supported by AlphaTheta Corporation.

**No Warranty**: This software is provided "as is" without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, and non-infringement. In no event shall the authors or copyright holders be liable for any claim, damages, or other liability arising from the use of this software.

**Data Responsibility**: Users are solely responsible for:
- The security and backup of their rekordbox library data
- Compliance with rekordbox terms of service
- Any modifications made to their music library
- File system changes or data loss that may occur

**Data Processing**: This project works exclusively with XML export files provided by rekordbox's official export functionality. It only parses publicly exported data and does not modify or access proprietary database files.

**XML Format**: The rekordbox XML export format is generated by AlphaTheta's rekordbox software. This project provides tools to analyze and work with this exported data.

## 🙏 Acknowledgments

- **AlphaTheta/Pioneer DJ** - For rekordbox and the DJ Link ecosystem
- **Anthropic** - For the Model Context Protocol specification
- **DJ Community** - For feedback, testing, and feature requests

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-username/rekordbox-mcp/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/rekordbox-mcp/discussions)  
- **Documentation**: [Wiki](https://github.com/your-username/rekordbox-mcp/wiki)

---

**Made with ❤️ for the DJ community**
