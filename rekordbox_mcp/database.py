"""
Rekordbox Database Connection Layer

Handles connection to and interaction with the encrypted rekordbox SQLite database.
"""

import os
import sys
import time
import asyncio
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from pyrekordbox import Rekordbox6Database
from loguru import logger

from .models import (
    Track,
    Playlist,
    SearchOptions,
    HistorySession,
    HistoryTrack,
    HistoryStats,
    LibraryStats,
)


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
        # Content cache
        self._content_cache: Optional[list] = None
        self._content_cache_time: Optional[float] = None
        self._content_cache_ttl: float = 30.0  # seconds
        # Backup dedup
        self._last_backup_time: Optional[float] = None
        self._backup_cooldown: float = 300.0  # 5 minutes

    async def connect(self, database_path: Optional[Path] = None) -> None:
        """Connect to the rekordbox database."""

        def _connect():
            if database_path:
                self.database_path = database_path
                logger.info(f"Connecting to rekordbox database at: {database_path}")
            else:
                self.database_path = self._detect_database_path()
                logger.info(
                    f"Auto-detected rekordbox database at: {self.database_path}"
                )

            if self.database_path:
                self.db = Rekordbox6Database(db_dir=str(self.database_path))
            else:
                self.db = Rekordbox6Database()

            content = self.db.get_content()
            content_count = len(list(content))
            logger.info(
                f"Successfully connected! Found {content_count} tracks in database."
            )
            self._connected = True

        try:
            await asyncio.to_thread(_connect)
        except Exception as e:
            logger.error(f"Failed to connect to rekordbox database: {e}")
            raise RuntimeError(f"Database connection failed: {str(e)}")

    def _detect_database_path(self) -> Path:
        """Auto-detect the rekordbox database location based on OS."""
        if os.name == "nt":  # Windows
            base_path = Path.home() / "AppData" / "Roaming" / "Pioneer"
        elif sys.platform == "darwin":  # macOS
            base_path = Path.home() / "Library" / "Pioneer"
        else:  # Linux
            base_path = Path.home() / ".config" / "Pioneer"

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
                await asyncio.to_thread(self.db.close)
                logger.info("Database connection closed")
            except Exception as e:
                logger.warning(f"Error closing database connection: {e}")
            finally:
                self.db = None
                self._connected = False
                self._invalidate_content_cache()

    def __del__(self):
        """Cleanup when object is destroyed."""
        if self.db:
            try:
                self.db.close()
            except Exception:
                pass

    # --- Cache management ---

    def _get_active_content(self) -> list:
        """Get active (non-deleted) content with caching."""
        now = time.monotonic()
        if (
            self._content_cache is not None
            and self._content_cache_time is not None
            and (now - self._content_cache_time) < self._content_cache_ttl
        ):
            return self._content_cache

        all_content = list(self.db.get_content())
        self._content_cache = [
            c for c in all_content if getattr(c, "rb_local_deleted", 0) == 0
        ]
        self._content_cache_time = now
        return self._content_cache

    def _invalidate_content_cache(self):
        """Clear content cache, forcing refresh on next access."""
        self._content_cache = None
        self._content_cache_time = None

    # --- Backup management ---

    def _create_backup(self) -> None:
        """Create a backup of the database before mutations. Deduplicates within cooldown."""
        if not self.database_path:
            return

        now = time.monotonic()
        if (
            self._last_backup_time is not None
            and (now - self._last_backup_time) < self._backup_cooldown
        ):
            logger.debug("Skipping backup — recent backup exists")
            return

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            possible_files = [
                self.database_path / "master.db",
                self.database_path / "rekordbox" / "master.db",
                *list(self.database_path.glob("**/master.db")),
                *list(self.database_path.glob("**/*.db")),
            ]

            db_file = None
            for file_path in possible_files:
                if file_path.exists() and file_path.is_file():
                    db_file = file_path
                    break

            if db_file:
                backup_path = self.database_path / f"master_backup_{timestamp}.db"
                shutil.copy2(db_file, backup_path)
                self._last_backup_time = now
                logger.info(f"Database backup created: {backup_path}")
            else:
                all_files = list(self.database_path.rglob("*"))
                db_files = [f for f in all_files if f.suffix == ".db"]
                logger.warning(
                    f"No database file found for backup. Available .db files: {db_files}"
                )

        except Exception as e:
            logger.warning(f"Failed to create database backup: {e}")

    # --- Read operations ---

    async def get_track_count(self) -> int:
        """Get total number of active (non-deleted) tracks in the database."""
        if not self.db:
            raise RuntimeError("Database not connected")

        def _inner():
            return len(self._get_active_content())

        return await asyncio.to_thread(_inner)

    async def search_tracks(self, options: SearchOptions) -> List[Track]:
        """Search for tracks based on the provided options."""
        if not self.db:
            raise RuntimeError("Database not connected")

        def _inner():
            active_content = self._get_active_content()
            filtered_tracks = []

            for content in active_content:
                artist_name = getattr(content, "ArtistName", "") or ""
                genre_name = getattr(content, "GenreName", "") or ""
                key_name = getattr(content, "KeyName", "") or ""
                bpm_value = (getattr(content, "BPM", 0) or 0) / 100.0
                rating_value = getattr(content, "Rating", 0) or 0

                if options.query and not any(
                    [
                        options.query.lower() in str(content.Title or "").lower(),
                        options.query.lower() in artist_name.lower(),
                        options.query.lower() in genre_name.lower(),
                    ]
                ):
                    continue

                if options.artist and options.artist.lower() not in artist_name.lower():
                    continue
                if (
                    options.title
                    and options.title.lower() not in str(content.Title or "").lower()
                ):
                    continue
                if options.genre and options.genre.lower() not in genre_name.lower():
                    continue
                if options.key and options.key != key_name:
                    continue
                if options.bpm_min and bpm_value < options.bpm_min:
                    continue
                if options.bpm_max and bpm_value > options.bpm_max:
                    continue
                if options.rating_min and rating_value < options.rating_min:
                    continue

                track = self._content_to_track(content)
                filtered_tracks.append(track)

            return filtered_tracks[: options.limit]

        return await asyncio.to_thread(_inner)

    async def get_track_by_id(self, track_id: str) -> Optional[Track]:
        """Get a specific track by its ID."""
        if not self.db:
            raise RuntimeError("Database not connected")

        def _inner():
            try:
                content = self.db.get_content(ID=int(track_id))
                if content and getattr(content, "rb_local_deleted", 0) == 0:
                    return self._content_to_track(content)
                return None
            except (ValueError, Exception):
                return None

        return await asyncio.to_thread(_inner)

    async def get_playlists(self) -> List[Playlist]:
        """Get all playlists from the database."""
        if not self.db:
            raise RuntimeError("Database not connected")

        def _inner():
            all_playlists = list(self.db.get_playlist())
            active_playlists = [
                p for p in all_playlists if getattr(p, "rb_local_deleted", 0) == 0
            ]

            playlists = []
            for playlist in active_playlists:
                try:
                    playlist_songs = list(
                        self.db.get_playlist_songs(PlaylistID=playlist.ID)
                    )
                    active_songs = [
                        s
                        for s in playlist_songs
                        if getattr(s, "rb_local_deleted", 0) == 0
                    ]
                    track_count = len(active_songs)
                except Exception:
                    track_count = 0

                is_smart = getattr(playlist, "is_smart_playlist", False) or False
                smart_criteria = None
                if is_smart and hasattr(playlist, "SmartList") and playlist.SmartList:
                    smart_criteria = str(playlist.SmartList)

                is_folder = getattr(playlist, "is_folder", False) or False
                if not is_folder and hasattr(playlist, "Attribute"):
                    is_folder = playlist.Attribute == 1

                playlists.append(
                    Playlist(
                        id=str(playlist.ID),
                        name=playlist.Name or "",
                        track_count=track_count,
                        created_date=getattr(playlist, "created_at", "") or "",
                        modified_date=getattr(playlist, "updated_at", "") or "",
                        is_folder=is_folder,
                        is_smart_playlist=is_smart,
                        smart_criteria=smart_criteria,
                        parent_id=(
                            str(playlist.ParentID)
                            if playlist.ParentID and playlist.ParentID != "root"
                            else None
                        ),
                    )
                )

            return playlists

        return await asyncio.to_thread(_inner)

    async def get_playlist_tracks(self, playlist_id: str) -> List[Track]:
        """Get all tracks in a specific playlist."""
        if not self.db:
            raise RuntimeError("Database not connected")

        def _inner():
            playlist_songs = list(
                self.db.get_playlist_songs(PlaylistID=int(playlist_id))
            )
            active_songs = [
                s for s in playlist_songs if getattr(s, "rb_local_deleted", 0) == 0
            ]

            active_content = self._get_active_content()
            content_lookup = {str(c.ID): c for c in active_content}

            tracks = []
            sorted_songs = sorted(active_songs, key=lambda x: getattr(x, "TrackNo", 0))
            for song_playlist in sorted_songs:
                content_id = str(song_playlist.ContentID)
                if content_id in content_lookup:
                    track = self._content_to_track(content_lookup[content_id])
                    tracks.append(track)

            return tracks

        return await asyncio.to_thread(_inner)

    async def get_most_played_tracks(self, limit: int = 20) -> List[Track]:
        """Get the most played tracks."""
        if not self.db:
            raise RuntimeError("Database not connected")

        def _inner():
            active_content = self._get_active_content()
            sorted_content = sorted(
                active_content,
                key=lambda x: getattr(x, "DJPlayCount", 0) or 0,
                reverse=True,
            )
            return [self._content_to_track(c) for c in sorted_content[:limit]]

        return await asyncio.to_thread(_inner)

    async def get_top_rated_tracks(self, limit: int = 20) -> List[Track]:
        """Get the highest rated tracks."""
        if not self.db:
            raise RuntimeError("Database not connected")

        def _inner():
            active_content = self._get_active_content()
            sorted_content = sorted(
                active_content,
                key=lambda x: (
                    getattr(x, "Rating", 0) or 0,
                    getattr(x, "DJPlayCount", 0) or 0,
                ),
                reverse=True,
            )
            return [self._content_to_track(c) for c in sorted_content[:limit]]

        return await asyncio.to_thread(_inner)

    async def get_unplayed_tracks(self, limit: int = 50) -> List[Track]:
        """Get tracks that have never been played."""
        if not self.db:
            raise RuntimeError("Database not connected")

        def _inner():
            active_content = self._get_active_content()
            unplayed = [
                c for c in active_content if (getattr(c, "DJPlayCount", 0) or 0) == 0
            ]
            return [self._content_to_track(c) for c in unplayed[:limit]]

        return await asyncio.to_thread(_inner)

    async def search_tracks_by_filename(self, filename: str) -> List[Track]:
        """Search tracks by filename."""
        if not self.db:
            raise RuntimeError("Database not connected")

        def _inner():
            active_content = self._get_active_content()
            filename_lower = filename.lower()
            return [
                self._content_to_track(c)
                for c in active_content
                if filename_lower in (getattr(c, "FolderPath", "") or "").lower()
            ]

        return await asyncio.to_thread(_inner)

    async def analyze_library(
        self, group_by: str, aggregate_by: str, top_n: int
    ) -> Dict[str, Any]:
        """Analyze library with grouping and aggregation."""
        if not self.db:
            raise RuntimeError("Database not connected")

        def _inner():
            active_content = self._get_active_content()
            groups: Dict[str, Dict[str, int]] = {}

            field_map = {
                "genre": "GenreName",
                "key": "KeyName",
                "year": "ReleaseYear",
                "artist": "ArtistName",
                "rating": "Rating",
            }
            attr_name = field_map.get(group_by, "GenreName")

            for content in active_content:
                raw = getattr(content, attr_name, "") or ""
                key = str(raw) if raw else "Unknown"

                if key not in groups:
                    groups[key] = {"count": 0, "playCount": 0, "totalTime": 0}

                groups[key]["count"] += 1
                groups[key]["playCount"] += getattr(content, "DJPlayCount", 0) or 0
                groups[key]["totalTime"] += getattr(content, "Length", 0) or 0

            sorted_groups = sorted(
                groups.items(), key=lambda x: x[1][aggregate_by], reverse=True
            )
            return {
                "group_by": group_by,
                "aggregate_by": aggregate_by,
                "results": dict(sorted_groups[:top_n]),
                "total_groups": len(groups),
            }

        return await asyncio.to_thread(_inner)

    async def validate_track_ids(self, track_ids: List[str]) -> Dict[str, Any]:
        """Validate track IDs."""
        if not self.db:
            raise RuntimeError("Database not connected")

        def _inner():
            active_content = self._get_active_content()
            existing_ids = {str(c.ID) for c in active_content}

            valid = [tid for tid in track_ids if tid in existing_ids]
            invalid = [tid for tid in track_ids if tid not in existing_ids]

            return {
                "valid": valid,
                "invalid": invalid,
                "total_checked": len(track_ids),
                "valid_count": len(valid),
                "invalid_count": len(invalid),
            }

        return await asyncio.to_thread(_inner)

    async def get_library_stats(self) -> LibraryStats:
        """Get comprehensive library statistics."""
        if not self.db:
            raise RuntimeError("Database not connected")

        def _inner():
            active_content = self._get_active_content()
            total_tracks = len(active_content)
            total_playtime = sum(getattr(c, "Length", 0) or 0 for c in active_content)
            avg_bpm = (
                sum((getattr(c, "BPM", 0) or 0) / 100.0 for c in active_content)
                / total_tracks
                if total_tracks > 0
                else 0
            )

            genres: Dict[str, int] = {}
            for content in active_content:
                genre = getattr(content, "GenreName", "") or "Unknown"
                genres[genre] = genres.get(genre, 0) + 1

            return LibraryStats(
                total_tracks=total_tracks,
                total_playtime_seconds=total_playtime,
                average_bpm=round(avg_bpm, 2),
                genre_distribution=dict(
                    sorted(genres.items(), key=lambda x: x[1], reverse=True)[:10]
                ),
                database_path=str(self.database_path),
                last_updated=datetime.now().isoformat(),
            )

        return await asyncio.to_thread(_inner)

    async def get_tracks_by_genre(self, genre: str) -> List[str]:
        """Get filepaths for all tracks matching a genre."""
        if not self.db:
            raise RuntimeError("Database not connected")

        def _inner():
            active_content = self._get_active_content()
            genre_lower = genre.lower()
            return [
                getattr(c, "FolderPath", "")
                for c in active_content
                if genre_lower in (getattr(c, "GenreName", "") or "").lower()
                and getattr(c, "FolderPath", "")
            ]

        return await asyncio.to_thread(_inner)

    # --- History operations ---

    async def get_history_sessions(
        self, include_folders: bool = False
    ) -> List[HistorySession]:
        """Get all DJ history sessions from the database."""
        if not self.db:
            raise RuntimeError("Database not connected")

        def _inner():
            all_histories = list(self.db.get_history())
            active_histories = [
                h for h in all_histories if getattr(h, "rb_local_deleted", 0) == 0
            ]

            # Build content lookup ONCE for duration calculation
            active_content = self._get_active_content()
            content_lookup = {str(c.ID): c for c in active_content}

            sessions = []
            for history in active_histories:
                is_folder = history.Attribute == 1

                if not include_folders and is_folder:
                    continue

                track_count = 0
                duration_minutes = None
                if not is_folder:
                    try:
                        history_songs = list(
                            self.db.get_history_songs(HistoryID=history.ID)
                        )
                        active_songs = [
                            s
                            for s in history_songs
                            if getattr(s, "rb_local_deleted", 0) == 0
                        ]
                        track_count = len(active_songs)

                        if active_songs:
                            total_seconds = 0
                            for song in active_songs:
                                content_id = str(song.ContentID)
                                if content_id in content_lookup:
                                    total_seconds += (
                                        getattr(content_lookup[content_id], "Length", 0)
                                        or 0
                                    )
                            duration_minutes = (
                                round(total_seconds / 60) if total_seconds > 0 else None
                            )
                    except Exception:
                        track_count = 0

                sessions.append(
                    HistorySession(
                        id=str(history.ID),
                        name=history.Name or "",
                        parent_id=(
                            str(history.ParentID)
                            if history.ParentID and history.ParentID != "root"
                            else None
                        ),
                        is_folder=is_folder,
                        date_created=history.DateCreated,
                        track_count=track_count,
                        duration_minutes=duration_minutes,
                    )
                )

            return sessions

        return await asyncio.to_thread(_inner)

    async def get_session_tracks(self, session_id: str) -> List[HistoryTrack]:
        """Get all tracks from a specific DJ history session."""
        if not self.db:
            raise RuntimeError("Database not connected")

        def _inner():
            history_songs = list(self.db.get_history_songs(HistoryID=int(session_id)))
            active_songs = [
                s for s in history_songs if getattr(s, "rb_local_deleted", 0) == 0
            ]

            active_content = self._get_active_content()
            content_lookup = {str(c.ID): c for c in active_content}

            tracks = []
            sorted_songs = sorted(active_songs, key=lambda x: x.TrackNo)
            for song in sorted_songs:
                content_id = str(song.ContentID)
                if content_id in content_lookup:
                    track = self._content_to_track(content_lookup[content_id])
                    tracks.append(
                        HistoryTrack(
                            id=track.id,
                            title=track.title,
                            artist=track.artist,
                            album=track.album,
                            genre=track.genre,
                            bpm=track.bpm,
                            key=track.key,
                            length=track.length,
                            track_number=song.TrackNo,
                            history_id=session_id,
                            play_order=song.TrackNo,
                        )
                    )

            return tracks

        return await asyncio.to_thread(_inner)

    async def get_history_stats(self) -> HistoryStats:
        """Get comprehensive statistics about DJ history sessions."""
        if not self.db:
            raise RuntimeError("Database not connected")

        # This method calls other async methods, so no to_thread wrapper
        sessions = await self.get_history_sessions(include_folders=False)

        total_sessions = len(sessions)
        total_tracks_played = sum(s.track_count for s in sessions)
        total_minutes = sum(s.duration_minutes for s in sessions if s.duration_minutes)
        total_hours_played = total_minutes / 60 if total_minutes > 0 else 0.0
        avg_session_length = (
            total_minutes / total_sessions if total_sessions > 0 else 0.0
        )

        sessions_by_month: Dict[str, int] = {}
        for session in sessions:
            if session.date_created:
                try:
                    date_part = session.date_created[:7]
                    sessions_by_month[date_part] = (
                        sessions_by_month.get(date_part, 0) + 1
                    )
                except Exception:
                    pass

        return HistoryStats(
            total_sessions=total_sessions,
            total_tracks_played=total_tracks_played,
            total_hours_played=round(total_hours_played, 1),
            sessions_by_month=sessions_by_month,
            avg_session_length=round(avg_session_length, 1),
            favorite_genres=[],
            most_played_track=None,
        )

    # --- Import operations ---

    SUPPORTED_EXTENSIONS = {".mp3", ".m4a", ".flac", ".wav", ".aiff", ".aif"}

    @staticmethod
    def _read_audio_tags(path: Path) -> Dict[str, Any]:
        """Extract basic tags from an audio file. Returns empty dict on failure."""
        try:
            from mutagen import File as MutagenFile
        except ImportError:
            return {}

        try:
            audio = MutagenFile(str(path), easy=True)
        except Exception as e:
            logger.debug(f"mutagen failed to read {path}: {e}")
            return {}

        if audio is None:
            return {}

        def first(key: str) -> Optional[str]:
            val = audio.get(key)
            if not val:
                return None
            return val[0] if isinstance(val, list) else str(val)

        tags: Dict[str, Any] = {
            "title": first("title"),
            "artist": first("artist"),
            "album": first("album"),
            "genre": first("genre"),
            "label": first("organization") or first("label"),
            "comments": first("comment"),
        }

        bpm_raw = first("bpm")
        if bpm_raw:
            try:
                tags["bpm"] = float(bpm_raw)
            except ValueError:
                pass

        year_raw = first("date") or first("year")
        if year_raw:
            try:
                tags["year"] = int(str(year_raw)[:4])
            except ValueError:
                pass

        info = getattr(audio, "info", None)
        if info is not None:
            if getattr(info, "length", None):
                tags["length"] = int(info.length)
            if getattr(info, "bitrate", None):
                tags["bitrate"] = (
                    int(info.bitrate // 1000)
                    if info.bitrate > 10000
                    else int(info.bitrate)
                )
            if getattr(info, "sample_rate", None):
                tags["sample_rate"] = int(info.sample_rate)

        return {k: v for k, v in tags.items() if v is not None}

    def _resolve_or_create(self, getter_name: str, adder_name: str, name: str):
        """Look up an entity by name; create if missing. Returns the ORM row or None."""
        if not name or not name.strip():
            return None
        clean = name.strip()
        try:
            existing = getattr(self.db, getter_name)(Name=clean)
            existing_first = existing.first() if hasattr(existing, "first") else None
            if existing_first is None and hasattr(existing, "__iter__"):
                for row in existing:
                    existing_first = row
                    break
            if existing_first is not None:
                return existing_first
        except Exception as e:
            logger.debug(f"{getter_name}(Name={clean!r}) lookup failed: {e}")

        try:
            return getattr(self.db, adder_name)(clean)
        except Exception as e:
            logger.warning(f"Failed to create {adder_name}({clean!r}): {e}")
            return None

    def _build_content_kwargs(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Translate user metadata into DjmdContent kwargs, creating related rows as needed."""
        kwargs: Dict[str, Any] = {}

        if metadata.get("title"):
            kwargs["Title"] = metadata["title"].strip()

        artist_row = None
        if metadata.get("artist"):
            artist_row = self._resolve_or_create(
                "get_artist", "add_artist", metadata["artist"]
            )
            if artist_row is not None:
                kwargs["ArtistID"] = artist_row.ID

        if metadata.get("album"):
            album_row = None
            clean = metadata["album"].strip()
            try:
                existing = self.db.get_album(Name=clean)
                album_row = (
                    existing.first()
                    if hasattr(existing, "first")
                    else next(iter(existing), None)
                )
            except Exception:
                album_row = None
            if album_row is None:
                try:
                    album_row = self.db.add_album(clean, artist=artist_row)
                except Exception as e:
                    logger.warning(f"Failed to create album {clean!r}: {e}")
            if album_row is not None:
                kwargs["AlbumID"] = album_row.ID

        if metadata.get("genre"):
            genre_row = self._resolve_or_create(
                "get_genre", "add_genre", metadata["genre"]
            )
            if genre_row is not None:
                kwargs["GenreID"] = genre_row.ID

        if metadata.get("label"):
            label_row = self._resolve_or_create(
                "get_label", "add_label", metadata["label"]
            )
            if label_row is not None:
                kwargs["LabelID"] = label_row.ID

        if metadata.get("bpm") is not None:
            kwargs["BPM"] = int(round(float(metadata["bpm"]) * 100))

        if metadata.get("rating") is not None:
            rating = int(metadata["rating"])
            if 0 <= rating <= 5:
                kwargs["Rating"] = rating

        if metadata.get("comments"):
            kwargs["Commnt"] = metadata["comments"]

        if metadata.get("year") is not None:
            kwargs["ReleaseYear"] = int(metadata["year"])

        if metadata.get("length") is not None:
            kwargs["Length"] = int(metadata["length"])

        if metadata.get("bitrate") is not None:
            kwargs["BitRate"] = int(metadata["bitrate"])

        if metadata.get("sample_rate") is not None:
            kwargs["SampleRate"] = int(metadata["sample_rate"])

        return kwargs

    async def import_track(
        self,
        path: str,
        metadata: Optional[Dict[str, Any]] = None,
        auto_tag: bool = True,
    ) -> Dict[str, Any]:
        """Import a single audio file into the rekordbox library.

        Metadata precedence (highest first): explicit ``metadata`` overrides tag values.
        Returns a result dict with status, track_id, and resolved metadata.
        """
        if not self.db:
            raise RuntimeError("Database not connected")

        def _inner():
            file_path = Path(path).expanduser().resolve()
            if not file_path.is_file():
                return {
                    "status": "error",
                    "path": str(file_path),
                    "reason": "file not found",
                }

            if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                return {
                    "status": "error",
                    "path": str(file_path),
                    "reason": f"unsupported extension {file_path.suffix}",
                }

            merged: Dict[str, Any] = {}
            if auto_tag:
                merged.update(self._read_audio_tags(file_path))
            if metadata:
                merged.update({k: v for k, v in metadata.items() if v is not None})

            self._create_backup()

            try:
                kwargs = self._build_content_kwargs(merged)
                content = self.db.add_content(str(file_path), **kwargs)
                self.db.commit()
                self._invalidate_content_cache()
                logger.info(f"Imported track {content.ID}: {file_path.name}")
                return {
                    "status": "success",
                    "track_id": str(content.ID),
                    "path": str(file_path),
                    "metadata": merged,
                }
            except ValueError as e:
                msg = str(e)
                if "already exists" in msg.lower():
                    return {
                        "status": "skipped",
                        "path": str(file_path),
                        "reason": "already in library",
                    }
                return {"status": "error", "path": str(file_path), "reason": msg}

        try:
            return await asyncio.to_thread(_inner)
        except Exception as e:
            logger.error(f"Failed to import track {path}: {e}")
            if self.db and hasattr(self.db, "rollback"):
                self.db.rollback()
            return {"status": "error", "path": path, "reason": str(e)}

    async def import_tracks(
        self,
        paths: List[str],
        recursive: bool = True,
        auto_tag: bool = True,
        extensions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Import multiple audio files and/or directories into the rekordbox library.

        Each entry in ``paths`` may be a file or a directory. Directories are scanned
        (recursively by default) for files matching ``extensions`` (default: all supported).
        """
        if not self.db:
            raise RuntimeError("Database not connected")

        ext_filter = (
            {e.lower() if e.startswith(".") else f".{e.lower()}" for e in extensions}
            if extensions
            else self.SUPPORTED_EXTENSIONS
        )

        collected: List[Path] = []
        for entry in paths:
            p = Path(entry).expanduser()
            if p.is_file():
                if p.suffix.lower() in ext_filter:
                    collected.append(p.resolve())
            elif p.is_dir():
                iterator = p.rglob("*") if recursive else p.iterdir()
                for candidate in iterator:
                    if candidate.is_file() and candidate.suffix.lower() in ext_filter:
                        collected.append(candidate.resolve())
            else:
                logger.warning(f"Skipping non-existent path: {p}")

        # Dedupe while preserving order
        seen = set()
        unique: List[Path] = []
        for fp in collected:
            if fp not in seen:
                seen.add(fp)
                unique.append(fp)

        logger.info(f"Importing {len(unique)} files from {len(paths)} source paths")

        imported: List[Dict[str, Any]] = []
        skipped: List[Dict[str, Any]] = []
        failed: List[Dict[str, Any]] = []

        for fp in unique:
            result = await self.import_track(str(fp), auto_tag=auto_tag)
            status = result.get("status")
            if status == "success":
                imported.append(
                    {"track_id": result["track_id"], "path": result["path"]}
                )
            elif status == "skipped":
                skipped.append({"path": result["path"], "reason": result["reason"]})
            else:
                failed.append(
                    {
                        "path": result.get("path", str(fp)),
                        "reason": result.get("reason", "unknown"),
                    }
                )

        return {
            "summary": {
                "scanned": len(unique),
                "imported": len(imported),
                "skipped": len(skipped),
                "failed": len(failed),
            },
            "imported": imported,
            "skipped": skipped,
            "failed": failed,
        }

    # --- Mutation operations ---

    async def create_playlist(
        self, name: str, parent_id: Optional[str] = None, is_folder: bool = False
    ) -> str:
        """Create a new playlist or folder."""
        if not self.db:
            raise RuntimeError("Database not connected")

        def _inner():
            self._create_backup()

            parent_int_id = (
                int(parent_id) if parent_id and parent_id != "root" else None
            )

            if is_folder:
                playlist = self.db.create_playlist_folder(
                    name=name, parent=parent_int_id
                )
            else:
                playlist = self.db.create_playlist(name=name, parent=parent_int_id)

            if hasattr(playlist, "ID"):
                playlist_id = str(playlist.ID)
            elif isinstance(playlist, str):
                playlist_id = playlist
            else:
                playlist_id = str(playlist)

            self.db.commit()
            self._invalidate_content_cache()

            item_type = "folder" if is_folder else "playlist"
            logger.info(f"Created {item_type} '{name}' with ID {playlist_id}")
            return playlist_id

        try:
            return await asyncio.to_thread(_inner)
        except Exception as e:
            logger.error(f"Failed to create playlist '{name}': {e}")
            if self.db and hasattr(self.db, "rollback"):
                self.db.rollback()
            raise RuntimeError(f"Failed to create playlist: {str(e)}")

    async def add_tracks_to_playlist(
        self, playlist_id: str, track_ids: List[str]
    ) -> Dict[str, Any]:
        """Add multiple tracks to a playlist."""
        if not self.db:
            raise RuntimeError("Database not connected")

        def _inner():
            self._create_backup()

            results: Dict[str, list] = {"added": [], "failed": [], "skipped": []}
            playlist_int_id = int(playlist_id)

            for track_id in track_ids:
                try:
                    self.db.add_to_playlist(playlist_int_id, int(track_id))
                    results["added"].append(track_id)
                    logger.info(f"Added track {track_id} to playlist {playlist_id}")
                except Exception as e:
                    results["failed"].append({"track_id": track_id, "reason": str(e)})
                    logger.warning(f"Failed to add track {track_id}: {e}")

            self.db.commit()
            self._invalidate_content_cache()

            logger.info(
                f"Batch add to playlist {playlist_id}: {len(results['added'])} added, {len(results['failed'])} failed"
            )
            return results

        try:
            return await asyncio.to_thread(_inner)
        except Exception as e:
            logger.error(f"Failed to add tracks to playlist {playlist_id}: {e}")
            if self.db and hasattr(self.db, "rollback"):
                self.db.rollback()
            raise RuntimeError(f"Failed to add tracks to playlist: {str(e)}")

    async def add_track_to_playlist(self, playlist_id: str, track_id: str) -> bool:
        """Add a track to an existing playlist."""
        if not self.db:
            raise RuntimeError("Database not connected")

        def _inner():
            self._create_backup()
            self.db.add_to_playlist(int(playlist_id), int(track_id))
            self.db.commit()
            self._invalidate_content_cache()
            logger.info(f"Added track {track_id} to playlist {playlist_id}")
            return True

        try:
            return await asyncio.to_thread(_inner)
        except Exception as e:
            logger.error(
                f"Failed to add track {track_id} to playlist {playlist_id}: {e}"
            )
            if self.db and hasattr(self.db, "rollback"):
                self.db.rollback()
            raise RuntimeError(f"Failed to add track to playlist: {str(e)}")

    async def remove_track_from_playlist(self, playlist_id: str, track_id: str) -> bool:
        """Remove a track from a playlist."""
        if not self.db:
            raise RuntimeError("Database not connected")

        def _inner():
            self._create_backup()
            self.db.remove_from_playlist(int(playlist_id), int(track_id))
            self.db.commit()
            self._invalidate_content_cache()
            logger.info(f"Removed track {track_id} from playlist {playlist_id}")
            return True

        try:
            return await asyncio.to_thread(_inner)
        except Exception as e:
            logger.error(
                f"Failed to remove track {track_id} from playlist {playlist_id}: {e}"
            )
            if self.db and hasattr(self.db, "rollback"):
                self.db.rollback()
            raise RuntimeError(f"Failed to remove track from playlist: {str(e)}")

    async def delete_playlist(self, playlist_id: str) -> bool:
        """Delete a playlist."""
        if not self.db:
            raise RuntimeError("Database not connected")

        def _inner():
            self._create_backup()
            self.db.delete_playlist(int(playlist_id))
            self.db.commit()
            self._invalidate_content_cache()
            logger.info(f"Deleted playlist {playlist_id}")
            return True

        try:
            return await asyncio.to_thread(_inner)
        except Exception as e:
            logger.error(f"Failed to delete playlist {playlist_id}: {e}")
            if self.db and hasattr(self.db, "rollback"):
                self.db.rollback()
            raise RuntimeError(f"Failed to delete playlist: {str(e)}")

    # --- Cleanup operations ---

    async def find_broken_tracks(self) -> Dict[str, Any]:
        """Scan the library for broken tracks and orphaned playlist references."""
        if not self.db:
            raise RuntimeError("Database not connected")

        def _inner():
            active_content = self._get_active_content()

            empty_path: List[Dict[str, str]] = []
            apple_music: List[Dict[str, str]] = []
            missing_file: List[Dict[str, str]] = []

            for c in active_content:
                fp = getattr(c, "FolderPath", "") or ""
                title = getattr(c, "Title", "") or ""
                if not fp.strip():
                    empty_path.append({"id": str(c.ID), "title": title})
                elif fp.startswith("apple-music:"):
                    apple_music.append({"id": str(c.ID), "title": title, "path": fp})
                elif not os.path.exists(fp):
                    missing_file.append({"id": str(c.ID), "title": title, "path": fp})

            # Find orphaned playlist refs
            active_ids = {c.ID for c in active_content}
            all_playlists = [
                p
                for p in list(self.db.get_playlist())
                if not getattr(p, "rb_local_deleted", 0)
            ]
            orphaned_refs: List[Dict[str, str]] = []
            for p in all_playlists:
                try:
                    songs = list(self.db.get_playlist_songs(PlaylistID=p.ID))
                    for s in songs:
                        if (
                            not getattr(s, "rb_local_deleted", 0)
                            and s.ContentID not in active_ids
                        ):
                            orphaned_refs.append(
                                {
                                    "playlist_id": str(p.ID),
                                    "playlist_name": p.Name or "",
                                    "content_id": str(s.ContentID),
                                    "song_id": str(s.ID),
                                }
                            )
                except Exception as e:
                    logger.debug(f"Error scanning playlist {p.Name}: {e}")

            return {
                "empty_path": empty_path,
                "apple_music_streams": apple_music,
                "missing_files": missing_file,
                "orphaned_playlist_refs": orphaned_refs,
                "summary": {
                    "empty_path_count": len(empty_path),
                    "apple_music_count": len(apple_music),
                    "missing_file_count": len(missing_file),
                    "orphaned_ref_count": len(orphaned_refs),
                },
            }

        return await asyncio.to_thread(_inner)

    async def remove_orphaned_playlist_entries(self) -> Dict[str, Any]:
        """Remove PlaylistSong rows that reference soft-deleted content."""
        if not self.db:
            raise RuntimeError("Database not connected")

        def _inner():
            self._create_backup()

            active_ids = {c.ID for c in self._get_active_content()}
            all_playlists = [
                p
                for p in list(self.db.get_playlist())
                if not getattr(p, "rb_local_deleted", 0)
            ]

            removed: List[Dict[str, str]] = []
            for p in all_playlists:
                try:
                    songs = list(self.db.get_playlist_songs(PlaylistID=p.ID))
                    for s in songs:
                        if (
                            not getattr(s, "rb_local_deleted", 0)
                            and s.ContentID not in active_ids
                        ):
                            self.db.remove_from_playlist(p.ID, s)
                            removed.append(
                                {
                                    "playlist": p.Name or "",
                                    "content_id": str(s.ContentID),
                                }
                            )
                except Exception as e:
                    logger.warning(f"Error cleaning playlist {p.Name}: {e}")

            self.db.commit()
            self._invalidate_content_cache()

            logger.info(f"Removed {len(removed)} orphaned playlist entries")
            return {"removed_count": len(removed), "details": removed}

        try:
            return await asyncio.to_thread(_inner)
        except Exception as e:
            logger.error(f"Failed to remove orphaned entries: {e}")
            if self.db and hasattr(self.db, "rollback"):
                self.db.rollback()
            raise RuntimeError(f"Failed to remove orphaned entries: {str(e)}")

    async def remove_tracks_by_ids(self, track_ids: List[str]) -> Dict[str, Any]:
        """Soft-delete tracks and remove them from all playlists."""
        if not self.db:
            raise RuntimeError("Database not connected")

        def _inner():
            self._create_backup()

            all_playlists = [
                p
                for p in list(self.db.get_playlist())
                if not getattr(p, "rb_local_deleted", 0)
            ]

            removed: List[Dict[str, str]] = []
            not_found: List[str] = []

            for tid in track_ids:
                try:
                    content = self.db.get_content(ID=int(tid))
                except (ValueError, Exception):
                    not_found.append(tid)
                    continue

                if not content:
                    not_found.append(tid)
                    continue

                # Remove from all playlists first
                for p in all_playlists:
                    try:
                        songs = list(self.db.get_playlist_songs(PlaylistID=p.ID))
                        for s in songs:
                            if s.ContentID == int(tid):
                                self.db.remove_from_playlist(p.ID, s)
                    except Exception:
                        pass

                # Soft-delete the content
                content.rb_local_deleted = 1
                removed.append(
                    {"id": tid, "title": getattr(content, "Title", "") or ""}
                )

            self.db.commit()
            self._invalidate_content_cache()

            logger.info(f"Removed {len(removed)} tracks, {len(not_found)} not found")
            return {"removed": removed, "not_found": not_found}

        try:
            return await asyncio.to_thread(_inner)
        except Exception as e:
            logger.error(f"Failed to remove tracks: {e}")
            if self.db and hasattr(self.db, "rollback"):
                self.db.rollback()
            raise RuntimeError(f"Failed to remove tracks: {str(e)}")

    # --- Field mapping ---

    def _content_to_track(self, content) -> Track:
        """Convert pyrekordbox content object to our Track model."""
        bpm_value = getattr(content, "BPM", 0) or 0
        bpm_float = float(bpm_value) / 100.0 if bpm_value else 0.0

        artist_name = ""
        if hasattr(content, "ArtistName"):
            artist_name = content.ArtistName or ""
        elif hasattr(content, "Artist"):
            artist_obj = content.Artist
            artist_name = (
                artist_obj.Name
                if hasattr(artist_obj, "Name")
                else str(artist_obj or "")
            )

        key_name = ""
        if hasattr(content, "KeyName"):
            key_name = content.KeyName or ""
        elif hasattr(content, "Key"):
            key_obj = content.Key
            key_name = key_obj.Name if hasattr(key_obj, "Name") else str(key_obj or "")

        album_name = ""
        if hasattr(content, "AlbumName"):
            album_name = content.AlbumName or ""
        elif hasattr(content, "Album"):
            album_obj = content.Album
            album_name = (
                album_obj.Name if hasattr(album_obj, "Name") else str(album_obj or "")
            )

        genre_name = ""
        if hasattr(content, "GenreName"):
            genre_name = content.GenreName or ""
        elif hasattr(content, "Genre"):
            genre_obj = content.Genre
            genre_name = (
                genre_obj.Name if hasattr(genre_obj, "Name") else str(genre_obj or "")
            )

        return Track(
            id=str(content.ID),
            title=content.Title or "",
            artist=artist_name,
            album=album_name,
            genre=genre_name,
            bpm=bpm_float,
            key=key_name,
            rating=int(getattr(content, "Rating", 0) or 0),
            play_count=int(getattr(content, "DJPlayCount", 0) or 0),
            length=int(getattr(content, "Length", 0) or 0),
            file_path=getattr(content, "FolderPath", "") or "",
            date_added=getattr(content, "DateCreated", "") or "",
            date_modified=getattr(content, "StockDate", "") or "",
            bitrate=int(getattr(content, "BitRate", 0) or 0),
            sample_rate=int(getattr(content, "SampleRate", 0) or 0),
            comments=getattr(content, "Commnt", "") or "",
        )
