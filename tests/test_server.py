"""Tests for MCP server tool handlers."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from rekordbox_mcp.models import Track, Playlist, SearchOptions


# FastMCP's @mcp.tool() wraps functions as FunctionTool objects.
# Access the original function via .fn attribute.
def _get_fn(tool_obj):
    """Get the underlying async function from a FastMCP tool."""
    return tool_obj.fn if hasattr(tool_obj, 'fn') else tool_obj


# We need to reset server globals between tests
@pytest.fixture(autouse=True)
def reset_server_globals():
    """Reset server module globals before each test."""
    import rekordbox_mcp.server as srv
    srv.db = None
    srv._db_initialized = False
    yield
    srv.db = None
    srv._db_initialized = False


@pytest.fixture
def mock_server_db(database):
    """Patch server.db with our mock database."""
    import rekordbox_mcp.server as srv
    srv.db = database
    srv._db_initialized = True
    return database


class TestEnsureDatabaseConnected:
    async def test_initializes_on_first_call(self):
        """First call should create and connect the database."""
        import rekordbox_mcp.server as srv

        mock_rdb = MagicMock()
        mock_rdb.connect = AsyncMock()
        mock_rdb.is_connected = AsyncMock(return_value=True)
        mock_rdb.get_track_count = AsyncMock(return_value=100)
        mock_rdb.get_playlists = AsyncMock(return_value=[])

        with patch("rekordbox_mcp.server.RekordboxDatabase", return_value=mock_rdb):
            await srv.ensure_database_connected()
            assert srv._db_initialized is True
            mock_rdb.connect.assert_called_once()

    async def test_skips_if_already_connected(self, mock_server_db):
        """Should not reinitialize if already connected."""
        import rekordbox_mcp.server as srv

        with patch.object(mock_server_db, "is_connected", new=AsyncMock(return_value=True)):
            await srv.ensure_database_connected()
            # Should not have tried to reconnect


class TestSearchTracksTool:
    async def test_returns_list_of_dicts(self, mock_server_db):
        import rekordbox_mcp.server as srv
        fn = _get_fn(srv.search_tracks)
        result = await fn(query="Techno")
        assert isinstance(result, list)
        assert all(isinstance(r, dict) for r in result)
        assert any("Techno" in r.get("title", "") or "Techno" in r.get("genre", "") for r in result)


class TestGetTrackDetailsTool:
    async def test_returns_track_dict(self, mock_server_db):
        import rekordbox_mcp.server as srv
        fn = _get_fn(srv.get_track_details)
        result = await fn("1")
        assert result["title"] == "Deep House Groove"

    async def test_raises_for_missing(self, mock_server_db):
        import rekordbox_mcp.server as srv
        fn = _get_fn(srv.get_track_details)
        with pytest.raises(ValueError, match="not found"):
            await fn("9999")


class TestPlaylistTools:
    async def test_get_playlists_returns_dicts(self, mock_server_db):
        import rekordbox_mcp.server as srv
        fn = _get_fn(srv.get_playlists)
        result = await fn()
        assert isinstance(result, list)
        assert all(isinstance(r, dict) for r in result)

    async def test_create_playlist_rejects_empty_name(self, mock_server_db):
        import rekordbox_mcp.server as srv
        fn = _get_fn(srv.create_playlist)
        with pytest.raises(ValueError, match="cannot be empty"):
            await fn(name="  ")

    async def test_delete_playlist_prevents_smart(self, mock_server_db):
        import rekordbox_mcp.server as srv
        fn = _get_fn(srv.delete_playlist)
        # ID 103 is the smart playlist
        result = await fn("103")
        assert result["status"] == "error"
        assert "smart" in result["message"].lower()


class TestLibraryStatsTool:
    async def test_returns_dict(self, mock_server_db):
        import rekordbox_mcp.server as srv
        fn = _get_fn(srv.get_library_stats)
        result = await fn()
        assert isinstance(result, dict)
        assert "total_tracks" in result
