"""Tests for the database layer."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from rekordbox_mcp.database import RekordboxDatabase
from rekordbox_mcp.models import SearchOptions, LibraryStats


class TestConnection:
    async def test_connect_with_path(self, tmp_path):
        """database_path should be passed as db_dir to Rekordbox6Database."""
        db = RekordboxDatabase()
        mock_rb = MagicMock()
        mock_rb.get_content.return_value = []

        with patch("rekordbox_mcp.database.Rekordbox6Database", return_value=mock_rb) as mock_cls:
            await db.connect(database_path=tmp_path)
            mock_cls.assert_called_once_with(db_dir=str(tmp_path))
            assert db._connected is True

    async def test_connect_without_path(self):
        """Without path, auto-detect should be used."""
        db = RekordboxDatabase()
        mock_rb = MagicMock()
        mock_rb.get_content.return_value = []

        with patch("rekordbox_mcp.database.Rekordbox6Database", return_value=mock_rb) as mock_cls, \
             patch.object(db, "_detect_database_path", return_value=Path("/fake/path")):
            await db.connect()
            mock_cls.assert_called_once_with(db_dir="/fake/path")

    async def test_disconnect(self, database, mock_db):
        await database.disconnect()
        mock_db.close.assert_called_once()
        assert database._connected is False
        assert database.db is None

    async def test_is_connected(self, database):
        assert await database.is_connected() is True
        database._connected = False
        assert await database.is_connected() is False


class TestDetectDatabasePath:
    def test_macos(self):
        db = RekordboxDatabase()
        with patch("rekordbox_mcp.database.os.name", "posix"), \
             patch("rekordbox_mcp.database.sys.platform", "darwin"), \
             patch.object(Path, "exists", return_value=True):
            path = db._detect_database_path()
            assert "Library" in str(path)
            assert "Pioneer" in str(path)

    def test_windows(self):
        db = RekordboxDatabase()
        fake_home = Path("/Users/testuser")
        with patch("rekordbox_mcp.database.os.name", "nt"), \
             patch.object(Path, "home", return_value=fake_home), \
             patch.object(Path, "exists", return_value=True):
            path = db._detect_database_path()
            assert "AppData" in str(path)

    def test_linux(self):
        db = RekordboxDatabase()
        with patch("rekordbox_mcp.database.os.name", "posix"), \
             patch("rekordbox_mcp.database.sys.platform", "linux"), \
             patch.object(Path, "exists", return_value=True):
            path = db._detect_database_path()
            assert ".config" in str(path)

    def test_not_found(self):
        db = RekordboxDatabase()
        with patch("rekordbox_mcp.database.os.name", "posix"), \
             patch("rekordbox_mcp.database.sys.platform", "darwin"), \
             patch.object(Path, "exists", return_value=False):
            with pytest.raises(FileNotFoundError):
                db._detect_database_path()


class TestSearchTracks:
    async def test_search_by_query(self, database):
        results = await database.search_tracks(SearchOptions(query="Techno"))
        titles = [t.title for t in results]
        assert "Techno Blast" in titles
        assert "Acid Techno Ride" in titles

    async def test_search_by_artist(self, database):
        results = await database.search_tracks(SearchOptions(artist="DJ Alpha"))
        assert len(results) == 3  # Deep House Groove, Minimal Vibes, House Party

    async def test_search_by_genre(self, database):
        results = await database.search_tracks(SearchOptions(genre="Techno"))
        genres = [t.genre for t in results]
        assert all("Techno" in g for g in genres)

    async def test_search_by_key(self, database):
        results = await database.search_tracks(SearchOptions(key="5A"))
        assert len(results) == 2  # Deep House Groove, Progressive Journey

    async def test_search_by_bpm_range(self, database):
        results = await database.search_tracks(SearchOptions(bpm_min=130, bpm_max=145))
        for track in results:
            assert 130 <= track.bpm <= 145

    async def test_search_by_rating(self, database):
        results = await database.search_tracks(SearchOptions(rating_min=4))
        assert all(t.rating >= 4 for t in results)

    async def test_search_limit(self, database):
        results = await database.search_tracks(SearchOptions(limit=3))
        assert len(results) <= 3

    async def test_search_filters_deleted(self, database):
        """Soft-deleted tracks should not appear."""
        results = await database.search_tracks(SearchOptions(query="Deleted"))
        assert len(results) == 0

    async def test_search_collects_all_then_limits(self, database):
        """Limit should apply after collecting all matches, not mid-iteration."""
        all_results = await database.search_tracks(SearchOptions(limit=1000))
        limited = await database.search_tracks(SearchOptions(limit=5))
        assert len(limited) == min(5, len(all_results))


class TestGetTrackById:
    async def test_found(self, database):
        track = await database.get_track_by_id("1")
        assert track is not None
        assert track.title == "Deep House Groove"

    async def test_not_found(self, database):
        track = await database.get_track_by_id("9999")
        assert track is None

    async def test_deleted_filtered(self, database):
        track = await database.get_track_by_id("99")
        assert track is None

    async def test_invalid_id(self, database):
        track = await database.get_track_by_id("not_a_number")
        assert track is None


class TestContentToTrack:
    def test_bpm_conversion(self, database, mock_content_list):
        """BPM stored as int*100 should be converted to float."""
        content = mock_content_list[0]  # BPM=12400
        track = database._content_to_track(content)
        assert track.bpm == 124.0

    def test_all_fields_mapped(self, database, mock_content_list):
        content = mock_content_list[0]
        track = database._content_to_track(content)
        assert track.id == "1"
        assert track.title == "Deep House Groove"
        assert track.artist == "DJ Alpha"
        assert track.genre == "Deep House"
        assert track.key == "5A"
        assert track.rating == 5
        assert track.play_count == 42


class TestPlaylistOperations:
    async def test_get_playlists(self, database):
        playlists = await database.get_playlists()
        active = [p for p in playlists if p.name != "Deleted Playlist"]
        assert len(active) >= 3  # Warm Up, Peak Time, Sets, Smart Mix

    async def test_playlist_filters_deleted(self, database):
        playlists = await database.get_playlists()
        names = [p.name for p in playlists]
        assert "Deleted Playlist" not in names

    async def test_get_playlist_tracks_ordering(self, database):
        tracks = await database.get_playlist_tracks("100")
        assert len(tracks) == 3
        # TrackNo order: 1 (ID=1), 2 (ID=5), 3 (ID=3)
        assert tracks[0].title == "Deep House Groove"
        assert tracks[1].title == "Progressive Journey"
        assert tracks[2].title == "Trance Dream"


class TestRankedQueries:
    async def test_most_played(self, database):
        tracks = await database.get_most_played_tracks(limit=3)
        assert len(tracks) == 3
        # Progressive Journey (50) > Deep House Groove (42) > Techno Blast (30)
        assert tracks[0].play_count >= tracks[1].play_count >= tracks[2].play_count

    async def test_top_rated(self, database):
        tracks = await database.get_top_rated_tracks(limit=3)
        assert len(tracks) == 3
        assert tracks[0].rating >= tracks[1].rating

    async def test_unplayed(self, database):
        tracks = await database.get_unplayed_tracks()
        assert all(t.play_count == 0 for t in tracks)
        titles = [t.title for t in tracks]
        assert "Ambient Chill" in titles
        assert "House Party" in titles


class TestSearchByFilename:
    async def test_partial_match(self, database):
        tracks = await database.search_tracks_by_filename("techno")
        assert len(tracks) >= 1


class TestAnalyzeLibrary:
    async def test_group_by_genre(self, database):
        result = await database.analyze_library("genre", "count", 5)
        assert result["group_by"] == "genre"
        assert "results" in result
        assert result["total_groups"] > 0

    async def test_group_by_rating(self, database):
        result = await database.analyze_library("rating", "playCount", 5)
        assert result["group_by"] == "rating"


class TestValidateTrackIds:
    async def test_mixed_ids(self, database):
        result = await database.validate_track_ids(["1", "2", "9999"])
        assert result["valid_count"] == 2
        assert result["invalid_count"] == 1
        assert "9999" in result["invalid"]


class TestLibraryStatsReturn:
    async def test_returns_model(self, database):
        stats = await database.get_library_stats()
        assert isinstance(stats, LibraryStats)
        assert stats.total_tracks == 11  # excludes deleted
        assert stats.average_bpm > 0


class TestHistoryOperations:
    async def test_get_sessions_excludes_folders(self, database):
        sessions = await database.get_history_sessions(include_folders=False)
        assert all(not s.is_folder for s in sessions)
        assert len(sessions) == 2

    async def test_get_sessions_includes_folders(self, database):
        sessions = await database.get_history_sessions(include_folders=True)
        assert any(s.is_folder for s in sessions)

    async def test_get_session_tracks(self, database):
        tracks = await database.get_session_tracks("201")
        assert len(tracks) == 3
        assert tracks[0].track_number == 1

    async def test_session_tracks_use_content_to_track(self, database):
        """Verify tracks are built via _content_to_track (no bmp_value typo)."""
        tracks = await database.get_session_tracks("201")
        # BPM should be properly converted (not raw int)
        assert tracks[0].bpm == 124.0  # ID=1, BPM=12400

    async def test_history_stats(self, database):
        stats = await database.get_history_stats()
        assert stats.total_sessions == 2
        assert stats.total_tracks_played == 5  # 3 + 2


class TestGenreFilepaths:
    async def test_genre_search(self, database):
        paths = await database.get_tracks_by_genre("Techno")
        assert len(paths) >= 2  # Techno Blast + Acid Techno Ride
        assert all(isinstance(p, str) for p in paths)


class TestFindBrokenTracks:
    async def test_detects_apple_music(self, database):
        result = await database.find_broken_tracks()
        assert result["summary"]["apple_music_count"] == 1
        assert result["apple_music_streams"][0]["title"] == "Streaming Track"

    async def test_detects_orphaned_refs(self, database):
        result = await database.find_broken_tracks()
        assert result["summary"]["orphaned_ref_count"] >= 1
        orphan_content_ids = [r["content_id"] for r in result["orphaned_playlist_refs"]]
        assert "99" in orphan_content_ids

    async def test_detects_missing_files(self, database):
        """All mock FolderPaths are /music/... which don't exist on disk."""
        result = await database.find_broken_tracks()
        # Mock paths like /music/deep_house_groove.mp3 don't exist
        assert result["summary"]["missing_file_count"] >= 1


class TestRemoveOrphanedPlaylistEntries:
    async def test_removes_orphans(self, database, mock_db):
        result = await database.remove_orphaned_playlist_entries()
        assert result["removed_count"] >= 1
        # Verify remove_from_playlist was called
        mock_db.remove_from_playlist.assert_called()
        mock_db.commit.assert_called()

    async def test_creates_backup(self, database, tmp_path):
        fake_db = tmp_path / "master.db"
        fake_db.write_text("fake database")
        await database.remove_orphaned_playlist_entries()
        backup_files = list(tmp_path.glob("master_backup_*.db"))
        assert len(backup_files) >= 1


class TestRemoveTracksByIds:
    async def test_soft_deletes_track(self, database, mock_db, mock_content_list):
        result = await database.remove_tracks_by_ids(["11"])
        assert len(result["removed"]) == 1
        assert result["removed"][0]["title"] == "Streaming Track"
        # Content should be soft-deleted
        content_11 = next(c for c in mock_content_list if c.ID == 11)
        assert content_11.rb_local_deleted == 1

    async def test_not_found_ids(self, database):
        result = await database.remove_tracks_by_ids(["9999"])
        assert len(result["not_found"]) == 1
        assert "9999" in result["not_found"]

    async def test_removes_from_playlists(self, database, mock_db):
        """Removing a track should also remove it from any playlists."""
        await database.remove_tracks_by_ids(["1"])
        # Should have called remove_from_playlist for track in playlist 100
        mock_db.remove_from_playlist.assert_called()
