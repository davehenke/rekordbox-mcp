"""
Rekordbox MCP Server

A FastMCP-based server for rekordbox database management with real-time database access.
"""

import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastmcp import FastMCP
from loguru import logger
from pydantic import BaseModel, Field

from .database import RekordboxDatabase
from .models import Track, Playlist, SearchOptions


# Initialize FastMCP server
mcp = FastMCP("Rekordbox Database MCP Server")

# Global database instance
db: Optional[RekordboxDatabase] = None
_db_initialized = False


class ServerConfig(BaseModel):
    """Server configuration model."""
    
    database_path: Optional[Path] = Field(
        default=None,
        description="Path to rekordbox database directory"
    )
    auto_detect: bool = Field(
        default=True,
        description="Automatically detect rekordbox database location"
    )
    backup_enabled: bool = Field(
        default=True,
        description="Enable automatic database backups before mutations"
    )


@mcp.tool()
async def search_tracks(
    query: str = "",
    artist: Optional[str] = None,
    title: Optional[str] = None,
    genre: Optional[str] = None,
    key: Optional[str] = None,
    bpm_min: Optional[float] = None,
    bpm_max: Optional[float] = None,
    rating_min: Optional[int] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Search tracks in the rekordbox database.
    
    Args:
        query: General search query (searches across multiple fields)
        artist: Filter by artist name
        title: Filter by track title
        genre: Filter by genre
        key: Filter by musical key (e.g., "5A", "12B")
        bpm_min: Minimum BPM
        bpm_max: Maximum BPM
        rating_min: Minimum rating (0-5)
        limit: Maximum number of results to return
    
    Returns:
        List of matching tracks with metadata
    """
    await ensure_database_connected()
    
    search_options = SearchOptions(
        query=query,
        artist=artist,
        title=title,
        genre=genre,
        key=key,
        bpm_min=bpm_min,
        bpm_max=bpm_max,
        rating_min=rating_min,
        limit=limit
    )
    
    tracks = await db.search_tracks(search_options)
    return [track.model_dump() for track in tracks]


@mcp.tool()
async def get_track_details(track_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific track.
    
    Args:
        track_id: The unique track identifier
        
    Returns:
        Detailed track information including metadata, cue points, and play history
    """
    if not db:
        raise RuntimeError("Database not initialized.")
    
    track = await db.get_track_by_id(track_id)
    if not track:
        raise ValueError(f"Track with ID {track_id} not found")
    
    return track.model_dump()


@mcp.tool()
async def get_tracks_by_key(key: str) -> List[Dict[str, Any]]:
    """
    Get all tracks in a specific musical key.
    
    Args:
        key: Musical key (e.g., "5A", "12B")
        
    Returns:
        List of tracks in the specified key
    """
    if not db:
        raise RuntimeError("Database not initialized.")
    
    search_options = SearchOptions(key=key, limit=1000)
    tracks = await db.search_tracks(search_options)
    return [track.model_dump() for track in tracks]


@mcp.tool()
async def get_tracks_by_bpm_range(bpm_min: float, bpm_max: float) -> List[Dict[str, Any]]:
    """
    Get tracks within a specific BPM range.
    
    Args:
        bpm_min: Minimum BPM
        bpm_max: Maximum BPM
        
    Returns:
        List of tracks within the BPM range
    """
    if not db:
        raise RuntimeError("Database not initialized.")
    
    search_options = SearchOptions(bpm_min=bpm_min, bpm_max=bpm_max, limit=1000)
    tracks = await db.search_tracks(search_options)
    return [track.model_dump() for track in tracks]


@mcp.tool()
async def get_most_played_tracks(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get the most played tracks in the library.
    
    Args:
        limit: Maximum number of tracks to return
        
    Returns:
        List of most played tracks
    """
    if not db:
        raise RuntimeError("Database not initialized.")
    
    tracks = await db.get_most_played_tracks(limit)
    return [track.model_dump() for track in tracks]


@mcp.tool()
async def get_top_rated_tracks(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get the highest rated tracks in the library.
    
    Args:
        limit: Maximum number of tracks to return
        
    Returns:
        List of top rated tracks
    """
    if not db:
        raise RuntimeError("Database not initialized.")
    
    tracks = await db.get_top_rated_tracks(limit)
    return [track.model_dump() for track in tracks]


@mcp.tool()
async def get_unplayed_tracks(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get tracks that have never been played.
    
    Args:
        limit: Maximum number of tracks to return
        
    Returns:
        List of unplayed tracks
    """
    if not db:
        raise RuntimeError("Database not initialized.")
    
    tracks = await db.get_unplayed_tracks(limit)
    return [track.model_dump() for track in tracks]


@mcp.tool()
async def get_track_file_path(track_id: str) -> Dict[str, str]:
    """
    Get the file system path for a specific track.
    
    Args:
        track_id: The unique track identifier
        
    Returns:
        Dictionary containing file path information
    """
    if not db:
        raise RuntimeError("Database not initialized.")
    
    track = await db.get_track_by_id(track_id)
    if not track:
        raise ValueError(f"Track with ID {track_id} not found")
    
    return {
        "track_id": track_id,
        "file_path": track.file_path or "",
        "file_name": track.file_path.split("/")[-1] if track.file_path else ""
    }


@mcp.tool()
async def search_tracks_by_filename(filename: str) -> List[Dict[str, Any]]:
    """
    Search for tracks by filename.
    
    Args:
        filename: Filename to search for (partial match)
        
    Returns:
        List of tracks matching the filename
    """
    if not db:
        raise RuntimeError("Database not initialized.")
    
    tracks = await db.search_tracks_by_filename(filename)
    return [track.model_dump() for track in tracks]


@mcp.tool()
async def analyze_library(
    group_by: str = "genre",
    aggregate_by: str = "count",
    top_n: int = 10
) -> Dict[str, Any]:
    """
    Analyze library with grouping and aggregation.
    
    Args:
        group_by: Field to group by (genre, key, year, artist, rating)
        aggregate_by: Aggregation method (count, playCount, totalTime)
        top_n: Number of top results to return
        
    Returns:
        Analysis results
    """
    if not db:
        raise RuntimeError("Database not initialized.")
    
    analysis = await db.analyze_library(group_by, aggregate_by, top_n)
    return analysis


@mcp.tool()
async def validate_track_ids(track_ids: List[str]) -> Dict[str, Any]:
    """
    Validate a list of track IDs and show which are valid/invalid.
    
    Args:
        track_ids: List of track IDs to validate
        
    Returns:
        Validation results with valid and invalid IDs
    """
    if not db:
        raise RuntimeError("Database not initialized.")
    
    validation = await db.validate_track_ids(track_ids)
    return validation


@mcp.tool()
async def get_playlists() -> List[Dict[str, Any]]:
    """
    Get all playlists from the rekordbox database.
    
    Returns:
        List of playlists with metadata
    """
    await ensure_database_connected()
    
    playlists = await db.get_playlists()
    return [playlist.model_dump() for playlist in playlists]


@mcp.tool()
async def get_playlist_tracks(playlist_id: str) -> List[Dict[str, Any]]:
    """
    Get all tracks in a specific playlist.
    
    Args:
        playlist_id: The unique playlist identifier
        
    Returns:
        List of tracks in the playlist
    """
    if not db:
        raise RuntimeError("Database not initialized.")
    
    tracks = await db.get_playlist_tracks(playlist_id)
    return [track.model_dump() for track in tracks]


@mcp.tool()
async def get_library_stats() -> Dict[str, Any]:
    """
    Get comprehensive library statistics.
    
    Returns:
        Dictionary containing various library statistics
    """
    if not db:
        raise RuntimeError("Database not initialized.")
    
    stats = await db.get_library_stats()
    return stats


@mcp.tool()
async def connect_database(database_path: Optional[str] = None) -> Dict[str, str]:
    """
    Connect to the rekordbox database.
    
    Args:
        database_path: Optional path to database directory. If not provided, auto-detection is used.
        
    Returns:
        Connection status message
    """
    global db
    
    try:
        db = RekordboxDatabase()
        path = Path(database_path) if database_path else None
        await db.connect(database_path=path)
        
        return {
            "status": "success", 
            "message": f"Connected to rekordbox database at {db.database_path}",
            "total_tracks": str(await db.get_track_count())
        }
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return {"status": "error", "message": f"Failed to connect: {str(e)}"}


@mcp.resource("file://database-status")
async def database_status() -> str:
    """Get the current database connection status."""
    if not db:
        return "Database not connected. Use connect_database tool to establish connection."
    
    if await db.is_connected():
        track_count = await db.get_track_count()
        return f"Connected to rekordbox database at {db.database_path}. Total tracks: {track_count}"
    else:
        return "Database connection lost. Please reconnect."


async def ensure_database_connected():
    """Ensure database is connected, initialize if not."""
    global db, _db_initialized
    
    if _db_initialized and db and await db.is_connected():
        return
    
    if not _db_initialized:
        logger.info("Initializing database connection...")
        
        try:
            db = RekordboxDatabase()
            await db.connect()
            
            track_count = await db.get_track_count()
            playlist_count = len(await db.get_playlists())
            
            logger.success(f"✅ Connected to rekordbox database!")
            logger.info(f"📊 Database contains {track_count} tracks and {playlist_count} playlists")
            _db_initialized = True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to rekordbox database: {e}")
            logger.error("🔧 Please ensure:")
            logger.error("   - Rekordbox is closed") 
            logger.error("   - Database key is available (run: uv run python -m pyrekordbox download-key)")
            logger.error("   - Database path is accessible")
            raise RuntimeError(f"Database initialization failed: {str(e)}")
    
    elif db and not await db.is_connected():
        # Reconnect if connection was lost
        await db.connect()


def main():
    """Main entry point for the MCP server."""
    
    # Configure logging
    logger.remove()
    logger.add(
        sink=lambda msg: print(msg, end=""),
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        level="INFO"
    )
    
    # Run the FastMCP server (database will be initialized on first tool call)
    mcp.run()


if __name__ == "__main__":
    main()