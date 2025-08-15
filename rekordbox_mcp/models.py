"""
Data Models for Rekordbox MCP Server

Pydantic models for type-safe data handling.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class Track(BaseModel):
    """
    Rekordbox track model with comprehensive metadata.
    """
    
    id: str = Field(..., description="Unique track identifier")
    title: str = Field(..., description="Track title")
    artist: str = Field(..., description="Track artist")
    album: Optional[str] = Field(None, description="Album name")
    genre: Optional[str] = Field(None, description="Musical genre")
    bpm: float = Field(0.0, description="Beats per minute")
    key: Optional[str] = Field(None, description="Musical key (e.g., '5A', '12B')")
    rating: int = Field(0, ge=0, le=5, description="Track rating (0-5)")
    play_count: int = Field(0, ge=0, description="Number of times played")
    length: int = Field(0, ge=0, description="Track length in seconds")
    file_path: Optional[str] = Field(None, description="Path to audio file")
    date_added: Optional[str] = Field(None, description="Date track was added to library")
    date_modified: Optional[str] = Field(None, description="Date track was last modified")
    
    # Additional metadata
    bitrate: Optional[int] = Field(None, description="Audio bitrate in kbps")
    sample_rate: Optional[int] = Field(None, description="Audio sample rate in Hz")
    color: Optional[str] = Field(None, description="Track color tag")
    comments: Optional[str] = Field(None, description="Track comments")
    
    @field_validator('key')
    @classmethod
    def validate_key(cls, v):
        """Validate musical key format."""
        if v and v not in []:  # Add valid key formats
            # Basic validation - could be more sophisticated
            pass
        return v
    
    def duration_formatted(self) -> str:
        """Get track duration in MM:SS format."""
        if self.length <= 0:
            return "0:00"
        
        minutes = self.length // 60
        seconds = self.length % 60
        return f"{minutes}:{seconds:02d}"


class CuePoint(BaseModel):
    """
    Rekordbox cue point model.
    """
    
    id: str = Field(..., description="Cue point identifier")
    track_id: str = Field(..., description="Associated track ID")
    position: float = Field(..., ge=0, description="Position in track (seconds)")
    type: str = Field(..., description="Cue type (memory, hot, loop, etc.)")
    name: Optional[str] = Field(None, description="Cue point name/label")
    color: Optional[str] = Field(None, description="Cue point color")


class Playlist(BaseModel):
    """
    Rekordbox playlist model.
    """
    
    id: str = Field(..., description="Unique playlist identifier")
    name: str = Field(..., description="Playlist name")
    parent_id: Optional[str] = Field(None, description="Parent folder ID")
    is_folder: bool = Field(False, description="Whether this is a folder")
    is_smart_playlist: bool = Field(False, description="Whether this is a smart/intelligent playlist")
    track_count: int = Field(0, ge=0, description="Number of tracks in playlist")
    created_date: Optional[str] = Field(None, description="Date playlist was created")
    modified_date: Optional[str] = Field(None, description="Date playlist was last modified")
    smart_criteria: Optional[str] = Field(None, description="Smart playlist criteria (XML)")
    
    @field_validator('created_date', 'modified_date', mode='before')
    @classmethod
    def validate_date(cls, v):
        """Convert datetime objects to strings."""
        if hasattr(v, 'strftime'):  # datetime object
            return v.strftime("%Y-%m-%d %H:%M:%S")
        return str(v) if v is not None else None


class HistorySession(BaseModel):
    """
    Rekordbox DJ history session model.
    """
    
    id: str = Field(..., description="Unique history session identifier")
    name: str = Field(..., description="Session name (usually date)")
    parent_id: Optional[str] = Field(None, description="Parent folder ID")
    is_folder: bool = Field(False, description="Whether this is a folder")
    date_created: Optional[str] = Field(None, description="Date session was created")
    track_count: int = Field(0, ge=0, description="Number of tracks in session")
    duration_minutes: Optional[int] = Field(None, description="Total session duration in minutes")
    
    @field_validator('date_created', mode='before')
    @classmethod
    def validate_date(cls, v):
        """Convert datetime objects to strings."""
        if hasattr(v, 'strftime'):  # datetime object
            return v.strftime("%Y-%m-%d %H:%M:%S")
        return str(v) if v is not None else None


class HistoryTrack(BaseModel):
    """
    Track within a DJ history session with performance context.
    """
    
    # Track basic info (from Track model)
    id: str = Field(..., description="Track identifier")
    title: str = Field("", description="Track title")
    artist: str = Field("", description="Artist name")
    album: Optional[str] = Field(None, description="Album name")
    genre: Optional[str] = Field(None, description="Genre")
    bpm: float = Field(0.0, ge=0, description="Beats per minute")
    key: Optional[str] = Field(None, description="Musical key")
    length: int = Field(0, ge=0, description="Track length in seconds")
    
    # History-specific context
    track_number: int = Field(..., ge=1, description="Position in DJ set")
    history_id: str = Field(..., description="History session ID")
    play_order: Optional[int] = Field(None, description="Order played in session")


class HistoryStats(BaseModel):
    """
    Statistics about DJ history sessions.
    """
    
    total_sessions: int = Field(0, ge=0, description="Total number of sessions")
    total_tracks_played: int = Field(0, ge=0, description="Total tracks across all sessions")
    total_hours_played: float = Field(0.0, ge=0, description="Total hours of DJ sets")
    most_played_track: Optional[Dict[str, Any]] = Field(None, description="Most played track across sessions")
    favorite_genres: List[Dict[str, Any]] = Field(default_factory=list, description="Top genres by play count")
    sessions_by_month: Dict[str, int] = Field(default_factory=dict, description="Sessions grouped by month")
    avg_session_length: float = Field(0.0, ge=0, description="Average session length in minutes")


class SearchOptions(BaseModel):
    """
    Search criteria for track queries.
    """
    
    query: str = Field("", description="General search query")
    artist: Optional[str] = Field(None, description="Filter by artist name")
    title: Optional[str] = Field(None, description="Filter by track title")
    album: Optional[str] = Field(None, description="Filter by album name")
    genre: Optional[str] = Field(None, description="Filter by genre")
    key: Optional[str] = Field(None, description="Filter by musical key")
    bpm_min: Optional[float] = Field(None, ge=0, description="Minimum BPM")
    bpm_max: Optional[float] = Field(None, ge=0, description="Maximum BPM")
    rating_min: Optional[int] = Field(None, ge=0, le=5, description="Minimum rating")
    rating_max: Optional[int] = Field(None, ge=0, le=5, description="Maximum rating")
    play_count_min: Optional[int] = Field(None, ge=0, description="Minimum play count")
    play_count_max: Optional[int] = Field(None, ge=0, description="Maximum play count")
    limit: int = Field(50, ge=1, le=1000, description="Maximum number of results")
    
    @field_validator('bpm_max')
    @classmethod
    def validate_bpm_range(cls, v, info):
        """Ensure bpm_max is greater than bpm_min."""
        if v and info.data.get('bpm_min') and v < info.data['bpm_min']:
            raise ValueError('bpm_max must be greater than bpm_min')
        return v
    
    @field_validator('rating_max')
    @classmethod
    def validate_rating_range(cls, v, info):
        """Ensure rating_max is greater than rating_min."""
        if v and info.data.get('rating_min') and v < info.data['rating_min']:
            raise ValueError('rating_max must be greater than rating_min')
        return v


class LibraryStats(BaseModel):
    """
    Comprehensive library statistics model.
    """
    
    total_tracks: int = Field(..., description="Total number of tracks")
    total_playtime_seconds: int = Field(..., description="Total library playtime in seconds")
    total_size_bytes: Optional[int] = Field(None, description="Total library size in bytes")
    average_bpm: float = Field(..., description="Average BPM across all tracks")
    genre_distribution: Dict[str, int] = Field(..., description="Track count by genre")
    key_distribution: Dict[str, int] = Field(default_factory=dict, description="Track count by key")
    rating_distribution: Dict[int, int] = Field(default_factory=dict, description="Track count by rating")
    most_played_tracks: List[str] = Field(default_factory=list, description="IDs of most played tracks")
    recently_added_tracks: List[str] = Field(default_factory=list, description="IDs of recently added tracks")
    database_path: str = Field(..., description="Path to database")
    last_updated: str = Field(..., description="Last update timestamp")
    
    def total_playtime_formatted(self) -> str:
        """Get total playtime in human-readable format."""
        hours = self.total_playtime_seconds // 3600
        minutes = (self.total_playtime_seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"


class DatabaseConnection(BaseModel):
    """
    Database connection status model.
    """
    
    is_connected: bool = Field(..., description="Whether database is connected")
    database_path: Optional[str] = Field(None, description="Path to database")
    total_tracks: Optional[int] = Field(None, description="Total tracks in database")
    connection_time: Optional[str] = Field(None, description="When connection was established")
    last_error: Optional[str] = Field(None, description="Last connection error message")


class MutationResult(BaseModel):
    """
    Result of a database mutation operation.
    """
    
    success: bool = Field(..., description="Whether operation was successful")
    message: str = Field(..., description="Success or error message")
    affected_records: int = Field(0, description="Number of records affected")
    backup_created: bool = Field(False, description="Whether backup was created")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Operation timestamp")