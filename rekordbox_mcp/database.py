"""
Rekordbox Database Connection Layer

Handles connection to and interaction with the encrypted rekordbox SQLite database.
"""

import os
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

import pyrekordbox
from pyrekordbox import Rekordbox6Database
from loguru import logger

from .models import Track, Playlist, SearchOptions, HistorySession, HistoryTrack, HistoryStats


class RekordboxDatabase:
    """
    Main interface for rekordbox database operations.
    
    Handles connection and querying operations on the encrypted
    rekordbox SQLite database using pyrekordbox.
    """
    
    def __init__(self):
        self.db: Optional[Rekordbox6Database] = None
        self.database_path: Optional[Path] = None
        self._connected = False
    
    async def connect(self, database_path: Optional[Path] = None) -> None:
        """
        Connect to the rekordbox database.
        
        Args:
            database_path: Optional path to database directory. If None, auto-detect.
        """
        try:
            if database_path:
                self.database_path = database_path
                logger.info(f"Connecting to rekordbox database at: {database_path}")
            else:
                # Auto-detect rekordbox database location
                self.database_path = self._detect_database_path()
                logger.info(f"Auto-detected rekordbox database at: {self.database_path}")
            
            # Initialize pyrekordbox database connection
            # Note: This will handle the SQLCipher decryption automatically
            self.db = Rekordbox6Database()
            
            # Test connection by getting a simple count
            content = self.db.get_content()
            content_count = len(list(content))  # Convert Query to list
            logger.info(f"Successfully connected! Found {content_count} tracks in database.")
            
            self._connected = True
            
        except Exception as e:
            logger.error(f"Failed to connect to rekordbox database: {e}")
            raise RuntimeError(f"Database connection failed: {str(e)}")
    
    def _detect_database_path(self) -> Path:
        """
        Auto-detect the rekordbox database location based on OS.
        
        Returns:
            Path to the rekordbox database directory
        """
        if os.name == 'nt':  # Windows
            base_path = Path.home() / "AppData" / "Roaming" / "Pioneer"
        else:  # macOS/Linux
            base_path = Path.home() / "Library" / "Pioneer"
        
        if not base_path.exists():
            raise FileNotFoundError(f"Rekordbox directory not found at {base_path}")
        
        return base_path
    
    async def is_connected(self) -> bool:
        """Check if database connection is active."""
        return self._connected and self.db is not None
    
    async def disconnect(self) -> None:
        """Properly close the database connection."""
        if self.db:
            try:
                self.db.close()
                logger.info("Database connection closed")
            except Exception as e:
                logger.warning(f"Error closing database connection: {e}")
            finally:
                self.db = None
                self._connected = False
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        if self.db:
            try:
                self.db.close()
            except Exception:
                pass  # Ignore errors during cleanup
    
    async def get_track_count(self) -> int:
        """Get total number of active (non-deleted) tracks in the database."""
        if not self.db:
            raise RuntimeError("Database not connected")
        
        # Filter out soft-deleted tracks
        all_content = list(self.db.get_content())
        active_content = [c for c in all_content if getattr(c, 'rb_local_deleted', 0) == 0]
        return len(active_content)
    
    async def search_tracks(self, options: SearchOptions) -> List[Track]:
        """
        Search for tracks based on the provided options.
        
        Args:
            options: Search criteria and filters
            
        Returns:
            List of matching tracks
        """
        if not self.db:
            raise RuntimeError("Database not connected")
        
        # Get all content from database, filtering out soft-deleted tracks
        all_content = list(self.db.get_content())
        active_content = [c for c in all_content if getattr(c, 'rb_local_deleted', 0) == 0]
        
        # Apply filters
        filtered_tracks = []
        
        for content in active_content:
            # Get extracted field values for filtering
            artist_name = getattr(content, 'ArtistName', '') or ""
            genre_name = getattr(content, 'GenreName', '') or ""
            key_name = getattr(content, 'KeyName', '') or ""
            bpm_value = (getattr(content, 'BPM', 0) or 0) / 100.0
            rating_value = getattr(content, 'Rating', 0) or 0
            
            # Apply text-based filters
            if options.query and not any([
                options.query.lower() in str(content.Title or "").lower(),
                options.query.lower() in artist_name.lower(),
                options.query.lower() in genre_name.lower(),
            ]):
                continue
            
            if options.artist and options.artist.lower() not in artist_name.lower():
                continue
            
            if options.title and options.title.lower() not in str(content.Title or "").lower():
                continue
            
            if options.genre and options.genre.lower() not in genre_name.lower():
                continue
            
            if options.key and options.key != key_name:
                continue
            
            # Apply numeric filters
            if options.bpm_min and bpm_value < options.bpm_min:
                continue
            
            if options.bpm_max and bpm_value > options.bpm_max:
                continue
            
            if options.rating_min and rating_value < options.rating_min:
                continue
            
            # Convert to our Track model
            track = self._content_to_track(content)
            filtered_tracks.append(track)
            
            # Apply limit
            if len(filtered_tracks) >= options.limit:
                break
        
        return filtered_tracks
    
    async def get_track_by_id(self, track_id: str) -> Optional[Track]:
        """
        Get a specific track by its ID.
        
        Args:
            track_id: The track's unique identifier
            
        Returns:
            Track object if found, None otherwise
        """
        if not self.db:
            raise RuntimeError("Database not connected")
        
        try:
            # Get all content and find by ID, filtering out soft-deleted tracks
            all_content = list(self.db.get_content())
            active_content = [c for c in all_content if getattr(c, 'rb_local_deleted', 0) == 0]
            content_id = int(track_id)
            
            # Find content by ID
            for content in active_content:
                if content.ID == content_id:
                    return self._content_to_track(content)
            
            return None
        except (ValueError, Exception):
            return None
    
    
    async def get_playlists(self) -> List[Playlist]:
        """
        Get all playlists from the database.
        
        Returns:
            List of playlist objects
        """
        if not self.db:
            raise RuntimeError("Database not connected")
        
        try:
            # Get all playlists, filtering out soft-deleted ones
            all_playlists = list(self.db.get_playlist())
            active_playlists = [p for p in all_playlists if getattr(p, 'rb_local_deleted', 0) == 0]
            
            playlists = []
            for playlist in active_playlists:
                # Get track count for this playlist
                try:
                    playlist_songs = list(self.db.get_playlist_songs(PlaylistID=playlist.ID))
                    # Filter out soft-deleted song-playlist relationships
                    active_songs = [s for s in playlist_songs if getattr(s, 'rb_local_deleted', 0) == 0]
                    track_count = len(active_songs)
                except Exception:
                    track_count = 0
                
                # Check if this is a smart playlist
                is_smart = getattr(playlist, 'is_smart_playlist', False) or False
                smart_criteria = None
                if is_smart and hasattr(playlist, 'SmartList') and playlist.SmartList:
                    smart_criteria = str(playlist.SmartList)
                
                # Check if this is a folder (has children)
                is_folder = getattr(playlist, 'is_folder', False) or False
                if not is_folder and hasattr(playlist, 'Attribute'):
                    # Attribute 1 seems to indicate folders
                    is_folder = playlist.Attribute == 1
                
                playlists.append(Playlist(
                    id=str(playlist.ID),
                    name=playlist.Name or "",
                    track_count=track_count,
                    created_date=getattr(playlist, 'created_at', '') or "",
                    modified_date=getattr(playlist, 'updated_at', '') or "",
                    is_folder=is_folder,
                    is_smart_playlist=is_smart,
                    smart_criteria=smart_criteria,
                    parent_id=str(playlist.ParentID) if playlist.ParentID and playlist.ParentID != "root" else None
                ))
            
            return playlists
        except Exception as e:
            logger.error(f"Failed to get playlists: {e}")
            return []
    
    async def get_playlist_tracks(self, playlist_id: str) -> List[Track]:
        """
        Get all tracks in a specific playlist.
        
        Args:
            playlist_id: The playlist's unique identifier
            
        Returns:
            List of tracks in the playlist
        """
        if not self.db:
            raise RuntimeError("Database not connected")
        
        try:
            # Get song-playlist relationships for this playlist
            playlist_songs = list(self.db.get_playlist_songs(PlaylistID=int(playlist_id)))
            # Filter out soft-deleted relationships
            active_songs = [s for s in playlist_songs if getattr(s, 'rb_local_deleted', 0) == 0]
            
            # Get all content to match against
            all_content = list(self.db.get_content())
            active_content = [c for c in all_content if getattr(c, 'rb_local_deleted', 0) == 0]
            
            # Create a lookup for faster access
            content_lookup = {str(c.ID): c for c in active_content}
            
            # Build tracks list maintaining playlist order
            tracks = []
            # Sort by TrackNo to maintain playlist order
            sorted_songs = sorted(active_songs, key=lambda x: getattr(x, 'TrackNo', 0))
            
            for song_playlist in sorted_songs:
                content_id = str(song_playlist.ContentID)
                if content_id in content_lookup:
                    track = self._content_to_track(content_lookup[content_id])
                    tracks.append(track)
            
            return tracks
            
        except Exception as e:
            logger.error(f"Failed to get playlist tracks for playlist {playlist_id}: {e}")
            return []
    
    async def get_most_played_tracks(self, limit: int = 20) -> List[Track]:
        """Get the most played tracks."""
        if not self.db:
            raise RuntimeError("Database not connected")
        
        all_content = list(self.db.get_content())
        active_content = [c for c in all_content if getattr(c, 'rb_local_deleted', 0) == 0]
        # Sort by play count descending
        sorted_content = sorted(active_content, key=lambda x: getattr(x, 'DJPlayCount', 0) or 0, reverse=True)
        
        return [self._content_to_track(content) for content in sorted_content[:limit]]
    
    async def get_top_rated_tracks(self, limit: int = 20) -> List[Track]:
        """Get the highest rated tracks."""
        if not self.db:
            raise RuntimeError("Database not connected")
        
        all_content = list(self.db.get_content())
        active_content = [c for c in all_content if getattr(c, 'rb_local_deleted', 0) == 0]
        # Sort by rating descending, then by play count
        sorted_content = sorted(active_content, key=lambda x: (getattr(x, 'Rating', 0) or 0, getattr(x, 'DJPlayCount', 0) or 0), reverse=True)
        
        return [self._content_to_track(content) for content in sorted_content[:limit]]
    
    async def get_unplayed_tracks(self, limit: int = 50) -> List[Track]:
        """Get tracks that have never been played."""
        if not self.db:
            raise RuntimeError("Database not connected")
        
        all_content = list(self.db.get_content())
        active_content = [c for c in all_content if getattr(c, 'rb_local_deleted', 0) == 0]
        # Filter tracks with 0 play count
        unplayed = [content for content in active_content if (getattr(content, 'DJPlayCount', 0) or 0) == 0]
        
        return [self._content_to_track(content) for content in unplayed[:limit]]
    
    async def search_tracks_by_filename(self, filename: str) -> List[Track]:
        """Search tracks by filename."""
        if not self.db:
            raise RuntimeError("Database not connected")
        
        all_content = list(self.db.get_content())
        active_content = [c for c in all_content if getattr(c, 'rb_local_deleted', 0) == 0]
        filename_lower = filename.lower()
        
        matching_tracks = []
        for content in active_content:
            file_path = content.Location or ""
            if filename_lower in file_path.lower():
                matching_tracks.append(self._content_to_track(content))
        
        return matching_tracks
    
    async def analyze_library(self, group_by: str, aggregate_by: str, top_n: int) -> Dict[str, Any]:
        """Analyze library with grouping and aggregation."""
        if not self.db:
            raise RuntimeError("Database not connected")
        
        all_content = list(self.db.get_content())
        active_content = [c for c in all_content if getattr(c, 'rb_local_deleted', 0) == 0]
        groups = {}
        
        for content in active_content:
            # Get grouping key
            if group_by == "genre":
                key = getattr(content, 'GenreName', '') or "Unknown"
            elif group_by == "key":
                key = getattr(content, 'KeyName', '') or "Unknown"
            elif group_by == "year":
                key = str(getattr(content, 'ReleaseYear', '') or "Unknown")
            elif group_by == "artist":
                key = getattr(content, 'ArtistName', '') or "Unknown"
            elif group_by == "rating":
                key = str(getattr(content, 'Rating', 0) or 0)
            else:
                key = "Unknown"
            
            if key not in groups:
                groups[key] = {"count": 0, "playCount": 0, "totalTime": 0}
            
            groups[key]["count"] += 1
            groups[key]["playCount"] += getattr(content, 'DJPlayCount', 0) or 0
            groups[key]["totalTime"] += getattr(content, 'Length', 0) or 0
        
        # Sort by the requested aggregation
        sorted_groups = sorted(groups.items(), key=lambda x: x[1][aggregate_by], reverse=True)
        
        return {
            "group_by": group_by,
            "aggregate_by": aggregate_by,
            "results": dict(sorted_groups[:top_n]),
            "total_groups": len(groups)
        }
    
    async def validate_track_ids(self, track_ids: List[str]) -> Dict[str, Any]:
        """Validate track IDs."""
        if not self.db:
            raise RuntimeError("Database not connected")
        
        all_content = list(self.db.get_content())
        active_content = [c for c in all_content if getattr(c, 'rb_local_deleted', 0) == 0]
        existing_ids = {str(content.ID) for content in active_content}
        
        valid = []
        invalid = []
        
        for track_id in track_ids:
            if track_id in existing_ids:
                valid.append(track_id)
            else:
                invalid.append(track_id)
        
        return {
            "valid": valid,
            "invalid": invalid,
            "total_checked": len(track_ids),
            "valid_count": len(valid),
            "invalid_count": len(invalid)
        }

    async def get_library_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive library statistics.
        
        Returns:
            Dictionary containing various statistics
        """
        if not self.db:
            raise RuntimeError("Database not connected")
        
        all_content = list(self.db.get_content())
        active_content = [c for c in all_content if getattr(c, 'rb_local_deleted', 0) == 0]
        
        # Calculate statistics
        total_tracks = len(active_content)
        total_playtime = sum(getattr(c, 'Length', 0) or 0 for c in active_content)
        avg_bpm = sum((getattr(c, 'BPM', 0) or 0) / 100.0 for c in active_content) / total_tracks if total_tracks > 0 else 0
        
        # Genre distribution
        genres = {}
        for content in active_content:
            genre = getattr(content, 'GenreName', '') or "Unknown"
            genres[genre] = genres.get(genre, 0) + 1
        
        return {
            "total_tracks": total_tracks,
            "total_playtime_seconds": total_playtime,
            "average_bpm": round(avg_bpm, 2),
            "genre_distribution": dict(sorted(genres.items(), key=lambda x: x[1], reverse=True)[:10]),
            "database_path": str(self.database_path),
            "connection_status": "connected"
        }
    
    def _content_to_track(self, content) -> Track:
        """
        Convert pyrekordbox content object to our Track model.
        
        Args:
            content: pyrekordbox content object
            
        Returns:
            Track model instance
        """
        # Handle BPM - it's stored as integer * 100 in the database
        bpm_value = getattr(content, 'BPM', 0) or 0
        bpm_float = float(bpm_value) / 100.0 if bpm_value else 0.0
        
        # Handle artist - it might be an object or string
        artist_name = ""
        if hasattr(content, 'ArtistName'):
            artist_name = content.ArtistName or ""
        elif hasattr(content, 'Artist'):
            artist_obj = content.Artist
            if hasattr(artist_obj, 'Name'):
                artist_name = artist_obj.Name or ""
            else:
                artist_name = str(artist_obj) if artist_obj else ""
        
        # Handle key - it might be an object
        key_name = ""
        if hasattr(content, 'KeyName'):
            key_name = content.KeyName or ""
        elif hasattr(content, 'Key'):
            key_obj = content.Key
            if hasattr(key_obj, 'Name'):
                key_name = key_obj.Name or ""
            else:
                key_name = str(key_obj) if key_obj else ""
        
        # Handle album - it might be an object
        album_name = ""
        if hasattr(content, 'AlbumName'):
            album_name = content.AlbumName or ""
        elif hasattr(content, 'Album'):
            album_obj = content.Album
            if hasattr(album_obj, 'Name'):
                album_name = album_obj.Name or ""
            else:
                album_name = str(album_obj) if album_obj else ""
        
        # Handle genre - it might be an object
        genre_name = ""
        if hasattr(content, 'GenreName'):
            genre_name = content.GenreName or ""
        elif hasattr(content, 'Genre'):
            genre_obj = content.Genre
            if hasattr(genre_obj, 'Name'):
                genre_name = genre_obj.Name or ""
            else:
                genre_name = str(genre_obj) if genre_obj else ""
        
        return Track(
            id=str(content.ID),
            title=content.Title or "",
            artist=artist_name,
            album=album_name,
            genre=genre_name,
            bpm=bpm_float,
            key=key_name,
            rating=int(getattr(content, 'Rating', 0) or 0),
            play_count=int(getattr(content, 'DJPlayCount', 0) or 0),
            length=int(getattr(content, 'Length', 0) or 0),
            file_path=getattr(content, 'FolderPath', '') or "",
            date_added=getattr(content, 'DateCreated', '') or "",
            date_modified=getattr(content, 'StockDate', '') or "",
            bitrate=int(getattr(content, 'BitRate', 0) or 0),
            sample_rate=int(getattr(content, 'SampleRate', 0) or 0),
            comments=getattr(content, 'Commnt', '') or ""
        )
    
    async def get_history_sessions(self, include_folders: bool = False) -> List[HistorySession]:
        """
        Get all DJ history sessions from the database.
        
        Args:
            include_folders: Whether to include folder entries
            
        Returns:
            List of history sessions
        """
        if not self.db:
            raise RuntimeError("Database not connected")
        
        try:
            # Get all histories, filtering out soft-deleted ones
            all_histories = list(self.db.get_history())
            active_histories = [h for h in all_histories if getattr(h, 'rb_local_deleted', 0) == 0]
            
            sessions = []
            for history in active_histories:
                # Filter by type: Attribute 1 = folder, Attribute 0 = session
                is_folder = history.Attribute == 1
                
                if not include_folders and is_folder:
                    continue
                
                # Get track count for sessions
                track_count = 0
                duration_minutes = None
                if not is_folder:
                    try:
                        history_songs = list(self.db.get_history_songs(HistoryID=history.ID))
                        active_songs = [s for s in history_songs if getattr(s, 'rb_local_deleted', 0) == 0]
                        track_count = len(active_songs)
                        
                        # Calculate duration if we have tracks
                        if active_songs:
                            all_content = list(self.db.get_content())
                            content_lookup = {str(c.ID): c for c in all_content if getattr(c, 'rb_local_deleted', 0) == 0}
                            
                            total_seconds = 0
                            for song in active_songs:
                                content_id = str(song.ContentID)
                                if content_id in content_lookup:
                                    track_length = getattr(content_lookup[content_id], 'Length', 0) or 0
                                    total_seconds += track_length
                            duration_minutes = round(total_seconds / 60) if total_seconds > 0 else None
                    except Exception:
                        track_count = 0
                
                sessions.append(HistorySession(
                    id=str(history.ID),
                    name=history.Name or "",
                    parent_id=str(history.ParentID) if history.ParentID and history.ParentID != "root" else None,
                    is_folder=is_folder,
                    date_created=history.DateCreated,
                    track_count=track_count,
                    duration_minutes=duration_minutes
                ))
            
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to get history sessions: {e}")
            return []
    
    async def get_session_tracks(self, session_id: str) -> List[HistoryTrack]:
        """
        Get all tracks from a specific DJ history session.
        
        Args:
            session_id: The session's unique identifier
            
        Returns:
            List of tracks in the session with performance context
        """
        if not self.db:
            raise RuntimeError("Database not connected")
        
        try:
            # Get songs for this session
            history_songs = list(self.db.get_history_songs(HistoryID=int(session_id)))
            active_songs = [s for s in history_songs if getattr(s, 'rb_local_deleted', 0) == 0]
            
            # Get all content to match against
            all_content = list(self.db.get_content())
            active_content = [c for c in all_content if getattr(c, 'rb_local_deleted', 0) == 0]
            content_lookup = {str(c.ID): c for c in active_content}
            
            # Build tracks list maintaining session order
            tracks = []
            sorted_songs = sorted(active_songs, key=lambda x: x.TrackNo)
            
            for song in sorted_songs:
                content_id = str(song.ContentID)
                if content_id in content_lookup:
                    content = content_lookup[content_id]
                    
                    # Extract track info using same logic as _content_to_track
                    bmp_value = getattr(content, 'BPM', 0) or 0
                    bpm_float = float(bmp_value) / 100.0 if bmp_value else 0.0
                    
                    artist_name = getattr(content, 'ArtistName', '') or ""
                    album_name = getattr(content, 'AlbumName', '') or ""
                    genre_name = getattr(content, 'GenreName', '') or ""
                    key_name = getattr(content, 'KeyName', '') or ""
                    
                    tracks.append(HistoryTrack(
                        id=str(content.ID),
                        title=content.Title or "",
                        artist=artist_name,
                        album=album_name,
                        genre=genre_name,
                        bpm=bpm_float,
                        key=key_name,
                        length=int(getattr(content, 'Length', 0) or 0),
                        track_number=song.TrackNo,
                        history_id=session_id,
                        play_order=song.TrackNo
                    ))
            
            return tracks
            
        except Exception as e:
            logger.error(f"Failed to get session tracks for session {session_id}: {e}")
            return []
    
    async def get_history_stats(self) -> HistoryStats:
        """
        Get comprehensive statistics about DJ history sessions.
        
        Returns:
            Statistics about all history sessions
        """
        if not self.db:
            raise RuntimeError("Database not connected")
        
        try:
            # Get all sessions (not folders)
            sessions = await self.get_history_sessions(include_folders=False)
            
            # Calculate basic stats
            total_sessions = len(sessions)
            total_tracks_played = sum(s.track_count for s in sessions)
            total_minutes = sum(s.duration_minutes for s in sessions if s.duration_minutes)
            total_hours_played = total_minutes / 60 if total_minutes > 0 else 0.0
            avg_session_length = total_minutes / total_sessions if total_sessions > 0 else 0.0
            
            # Group sessions by month
            sessions_by_month = {}
            for session in sessions:
                if session.date_created:
                    try:
                        # Extract year-month from date string
                        date_part = session.date_created[:7]  # "2025-08"
                        sessions_by_month[date_part] = sessions_by_month.get(date_part, 0) + 1
                    except:
                        pass
            
            # For more detailed stats, we'd need to analyze all tracks
            # This is a basic implementation
            return HistoryStats(
                total_sessions=total_sessions,
                total_tracks_played=total_tracks_played,
                total_hours_played=round(total_hours_played, 1),
                sessions_by_month=sessions_by_month,
                avg_session_length=round(avg_session_length, 1),
                favorite_genres=[],  # Would require analyzing all session tracks
                most_played_track=None  # Would require counting track occurrences
            )
            
        except Exception as e:
            logger.error(f"Failed to get history stats: {e}")
            return HistoryStats()
    
    async def create_playlist(self, name: str, parent_id: Optional[str] = None) -> str:
        """
        Create a new playlist.
        
        Args:
            name: Name for the new playlist
            parent_id: Optional parent folder ID
            
        Returns:
            ID of the created playlist
        """
        if not self.db:
            raise RuntimeError("Database not connected")
        
        try:
            # Create backup before mutation
            await self._create_backup()
            
            # Create playlist using pyrekordbox
            playlist = self.db.create_playlist(
                name=name,
                parent=parent_id if parent_id and parent_id != "root" else None
            )
            
            # Debug: check what type playlist is
            logger.debug(f"playlist type: {type(playlist)}")
            logger.debug(f"playlist value: {playlist}")
            
            # Commit changes
            self.db.commit()
            
            # Handle different return types
            if hasattr(playlist, 'ID'):
                playlist_id = str(playlist.ID)
            elif isinstance(playlist, str):
                playlist_id = playlist
            else:
                # Try to get ID from the playlist object
                playlist_id = str(playlist)
            
            logger.info(f"Created playlist '{name}' with ID {playlist_id}")
            return playlist_id
            
        except Exception as e:
            logger.error(f"Failed to create playlist '{name}': {e}")
            # Rollback on error
            if hasattr(self.db, 'rollback'):
                self.db.rollback()
            raise RuntimeError(f"Failed to create playlist: {str(e)}")
    
    async def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]) -> Dict[str, Any]:
        """
        Add multiple tracks to a playlist.
        
        Args:
            playlist_id: ID of the playlist to modify
            track_ids: List of track IDs to add
            
        Returns:
            Dictionary with success/failure details
        """
        if not self.db:
            raise RuntimeError("Database not connected")
        
        try:
            # Create backup before mutation
            await self._create_backup()
            
            results = {
                "added": [],
                "failed": [],
                "skipped": []
            }
            
            playlist_int_id = int(playlist_id)
            
            for track_id in track_ids:
                try:
                    track_int_id = int(track_id)
                    
                    # Use the same method as the working single-track function
                    self.db.add_to_playlist(playlist_int_id, track_int_id)
                    results["added"].append(track_id)
                    logger.info(f"Added track {track_id} to playlist {playlist_id}")
                    
                except Exception as e:
                    results["failed"].append({"track_id": track_id, "reason": str(e)})
                    logger.warning(f"Failed to add track {track_id}: {e}")
            
            # Commit all changes
            self.db.commit()
            
            logger.info(f"Batch add to playlist {playlist_id}: {len(results['added'])} added, {len(results['failed'])} failed")
            return results
            
        except Exception as e:
            logger.error(f"Failed to add tracks to playlist {playlist_id}: {e}")
            # Rollback on error
            if hasattr(self.db, 'rollback'):
                self.db.rollback()
            raise RuntimeError(f"Failed to add tracks to playlist: {str(e)}")

    async def add_track_to_playlist(self, playlist_id: str, track_id: str) -> bool:
        """
        Add a track to an existing playlist.
        
        Args:
            playlist_id: ID of the playlist
            track_id: ID of the track to add
            
        Returns:
            True if successful
        """
        if not self.db:
            raise RuntimeError("Database not connected")
        
        try:
            # Create backup before mutation
            await self._create_backup()
            
            # Verify playlist and track exist
            playlist_int_id = int(playlist_id)
            track_int_id = int(track_id)
            
            # Add track to playlist using pyrekordbox
            self.db.add_to_playlist(playlist_int_id, track_int_id)
            
            # Commit changes
            self.db.commit()
            
            logger.info(f"Added track {track_id} to playlist {playlist_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add track {track_id} to playlist {playlist_id}: {e}")
            # Rollback on error
            if hasattr(self.db, 'rollback'):
                self.db.rollback()
            raise RuntimeError(f"Failed to add track to playlist: {str(e)}")
    
    async def remove_track_from_playlist(self, playlist_id: str, track_id: str) -> bool:
        """
        Remove a track from a playlist.
        
        Args:
            playlist_id: ID of the playlist
            track_id: ID of the track to remove
            
        Returns:
            True if successful
        """
        if not self.db:
            raise RuntimeError("Database not connected")
        
        try:
            # Create backup before mutation
            await self._create_backup()
            
            # Remove track from playlist using pyrekordbox
            playlist_int_id = int(playlist_id)
            track_int_id = int(track_id)
            
            self.db.remove_from_playlist(playlist_int_id, track_int_id)
            
            # Commit changes
            self.db.commit()
            
            logger.info(f"Removed track {track_id} from playlist {playlist_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove track {track_id} from playlist {playlist_id}: {e}")
            # Rollback on error
            if hasattr(self.db, 'rollback'):
                self.db.rollback()
            raise RuntimeError(f"Failed to remove track from playlist: {str(e)}")
    
    async def delete_playlist(self, playlist_id: str) -> bool:
        """
        Delete a playlist.
        
        Args:
            playlist_id: ID of the playlist to delete
            
        Returns:
            True if successful
        """
        if not self.db:
            raise RuntimeError("Database not connected")
        
        try:
            # Create backup before mutation
            await self._create_backup()
            
            # Delete playlist using pyrekordbox
            playlist_int_id = int(playlist_id)
            self.db.delete_playlist(playlist_int_id)
            
            # Commit changes
            self.db.commit()
            
            logger.info(f"Deleted playlist {playlist_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete playlist {playlist_id}: {e}")
            # Rollback on error
            if hasattr(self.db, 'rollback'):
                self.db.rollback()
            raise RuntimeError(f"Failed to delete playlist: {str(e)}")
    
    async def _create_backup(self) -> None:
        """
        Create a backup of the database before performing mutations.
        """
        if not self.database_path:
            return
        
        try:
            import shutil
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Try different database file patterns
            possible_files = [
                self.database_path / "master.db",
                self.database_path / "rekordbox" / "master.db",
                *list(self.database_path.glob("**/master.db")),
                *list(self.database_path.glob("**/*.db"))
            ]
            
            db_file = None
            for file_path in possible_files:
                if file_path.exists() and file_path.is_file():
                    db_file = file_path
                    break
            
            if db_file:
                backup_path = self.database_path / f"master_backup_{timestamp}.db"
                shutil.copy2(db_file, backup_path)
                logger.info(f"Database backup created: {backup_path}")
            else:
                # List available files for debugging
                all_files = list(self.database_path.rglob("*"))
                db_files = [f for f in all_files if f.suffix == '.db']
                logger.warning(f"No database file found for backup. Available .db files: {db_files}")
            
        except Exception as e:
            logger.warning(f"Failed to create database backup: {e}")
    
