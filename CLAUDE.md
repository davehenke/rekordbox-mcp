# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

An MCP server that provides Claude with direct read/write access to the rekordbox DJ software database. Built with FastMCP and pyrekordbox, it connects to rekordbox's encrypted SQLite (SQLCipher) database to expose 29 tools and 1 resource for searching tracks, managing playlists, analyzing DJ history, and computing library statistics.

## Commands

```bash
# Install dependencies
uv sync

# Run the MCP server
uv run rekordbox-mcp
uv run rekordbox-mcp --database-path /path/to/Pioneer  # custom path

# Code quality
uv run black rekordbox_mcp/    # format
uv run ruff rekordbox_mcp/     # lint
uv run mypy rekordbox_mcp/     # type check

# Run tests (82 tests, mocked pyrekordbox — no real database needed)
uv run pytest tests/ -v
```

## Architecture

Three-layer design in `rekordbox_mcp/`:

- **`server.py`** -- FastMCP server. Defines all MCP tools as decorated async functions, manages a global `RekordboxDatabase` instance, handles signals (SIGINT/SIGTERM). Entry point is `main()`. Tools are grouped: search/discovery, playlist operations, DJ history, library analytics, and database management.

- **`database.py`** -- `RekordboxDatabase` class. Wraps pyrekordbox's `Rekordbox6Database` for encrypted SQLite access. Auto-detects the database path per platform (`~/Library/Pioneer` on macOS, `~/AppData/Roaming/Pioneer` on Windows). Lazy connection on first tool call. All queries filter soft-deleted records (`rb_local_deleted`). Mutation methods auto-create timestamped backups (`master_backup_YYYYMMDD_HHMMSS.db`) before writes.

- **`models.py`** -- Pydantic models for Track, Playlist, HistorySession, HistoryTrack, SearchOptions, LibraryStats, HistoryStats. Validators handle date parsing and range constraints.

**Connection flow:** MCP client request -> `server.py` tool handler -> `ensure_database_connected()` -> `RekordboxDatabase.connect()` (first call only) -> pyrekordbox SQLCipher decryption -> query/mutate.

## Key Conventions

- BPM is stored as int * 100 in the database (e.g., 12800 = 128.0 BPM). The database layer converts this for display.
- Track search results default to limit=50, max=1000. The `get_genre_filepaths` tool returns only file paths for token efficiency.
- Mutation tools (create_playlist, add_tracks_to_playlist, etc.) are annotated with `readOnlyHint=False`. Destructive tools (delete_playlist) have `destructiveHint=True`.
- Smart playlists cannot be deleted (protected by validation).
- Read-only tools work while rekordbox is open. Mutation tools require rekordbox to be closed — pyrekordbox's `commit()` blocks when it detects the running process.
- An encryption key is required for database access; `setup-key.py` handles downloading/verifying it.

## Database Tables (via pyrekordbox)

`Content` (tracks), `Playlist`, `PlaylistSong` (playlist-track join), `History` (DJ sessions), `HistorySong` (history-track join). Playlist folders use `Attribute=1`.
