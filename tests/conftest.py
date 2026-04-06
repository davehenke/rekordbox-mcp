"""Shared test fixtures for rekordbox-mcp tests."""

from dataclasses import dataclass, field
from typing import Optional, List
from unittest.mock import MagicMock

import pytest

from rekordbox_mcp.database import RekordboxDatabase


# --- Mock dataclasses mimicking pyrekordbox ORM objects ---


@dataclass
class MockContent:
    ID: int
    Title: str = ""
    ArtistName: str = ""
    AlbumName: str = ""
    GenreName: str = ""
    KeyName: str = ""
    BPM: int = 0  # stored as int * 100
    Rating: int = 0
    DJPlayCount: int = 0
    Length: int = 0  # seconds
    FolderPath: str = ""
    Location: str = ""
    DateCreated: str = ""
    StockDate: str = ""
    BitRate: int = 0
    SampleRate: int = 0
    Commnt: str = ""
    rb_local_deleted: int = 0
    ReleaseYear: Optional[int] = None


@dataclass
class MockPlaylist:
    ID: int
    Name: str = ""
    ParentID: Optional[int] = None
    Attribute: int = 0  # 1 = folder
    is_smart_playlist: bool = False
    is_folder: bool = False
    SmartList: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    rb_local_deleted: int = 0


@dataclass
class MockPlaylistSong:
    ID: int = 0
    PlaylistID: int = 0
    ContentID: int = 0
    TrackNo: int = 0
    rb_local_deleted: int = 0


@dataclass
class MockHistory:
    ID: int
    Name: str = ""
    ParentID: Optional[int] = None
    Attribute: int = 0  # 1 = folder
    DateCreated: str = ""
    rb_local_deleted: int = 0


@dataclass
class MockHistorySong:
    HistoryID: int = 0
    ContentID: int = 0
    TrackNo: int = 0
    rb_local_deleted: int = 0


# --- Fixtures ---


@pytest.fixture
def mock_content_list():
    """10 varied tracks for testing, plus 1 soft-deleted."""
    return [
        MockContent(ID=1, Title="Deep House Groove", ArtistName="DJ Alpha", GenreName="Deep House",
                     KeyName="5A", BPM=12400, Rating=5, DJPlayCount=42, Length=360,
                     FolderPath="/music/deep_house_groove.mp3", Location="/music/deep_house_groove.mp3",
                     DateCreated="2024-01-15", BitRate=320, SampleRate=44100),
        MockContent(ID=2, Title="Techno Blast", ArtistName="DJ Beta", GenreName="Techno",
                     KeyName="8B", BPM=13800, Rating=4, DJPlayCount=30, Length=420,
                     FolderPath="/music/techno_blast.mp3", Location="/music/techno_blast.mp3",
                     DateCreated="2024-02-20", BitRate=320, SampleRate=44100),
        MockContent(ID=3, Title="Trance Dream", ArtistName="DJ Gamma", GenreName="Trance",
                     KeyName="12A", BPM=14000, Rating=3, DJPlayCount=10, Length=480,
                     FolderPath="/music/trance_dream.mp3", Location="/music/trance_dream.mp3",
                     DateCreated="2024-03-10", BitRate=256, SampleRate=44100),
        MockContent(ID=4, Title="Minimal Vibes", ArtistName="DJ Alpha", GenreName="Minimal",
                     KeyName="2B", BPM=12800, Rating=4, DJPlayCount=25, Length=300,
                     FolderPath="/music/minimal_vibes.mp3", Location="/music/minimal_vibes.mp3",
                     DateCreated="2024-04-05", BitRate=320, SampleRate=48000),
        MockContent(ID=5, Title="Progressive Journey", ArtistName="DJ Delta", GenreName="Progressive House",
                     KeyName="5A", BPM=12600, Rating=5, DJPlayCount=50, Length=540,
                     FolderPath="/music/progressive_journey.mp3", Location="/music/progressive_journey.mp3",
                     DateCreated="2024-05-12", BitRate=320, SampleRate=44100),
        MockContent(ID=6, Title="Drum and Bass Fury", ArtistName="DJ Epsilon", GenreName="Drum and Bass",
                     KeyName="7A", BPM=17400, Rating=2, DJPlayCount=5, Length=270,
                     FolderPath="/music/dnb_fury.mp3", Location="/music/dnb_fury.mp3",
                     DateCreated="2024-06-01", BitRate=192, SampleRate=44100),
        MockContent(ID=7, Title="Ambient Chill", ArtistName="DJ Zeta", GenreName="Ambient",
                     KeyName="1A", BPM=9000, Rating=3, DJPlayCount=0, Length=600,
                     FolderPath="/music/ambient_chill.mp3", Location="/music/ambient_chill.mp3",
                     DateCreated="2024-07-20", BitRate=320, SampleRate=48000),
        MockContent(ID=8, Title="House Party", ArtistName="DJ Alpha", GenreName="House",
                     KeyName="10B", BPM=12800, Rating=0, DJPlayCount=0, Length=330,
                     FolderPath="/music/house_party.mp3", Location="/music/house_party.mp3",
                     DateCreated="2024-08-15", BitRate=256, SampleRate=44100),
        MockContent(ID=9, Title="Acid Techno Ride", ArtistName="DJ Beta", GenreName="Techno",
                     KeyName="3A", BPM=14200, Rating=4, DJPlayCount=18, Length=390,
                     FolderPath="/music/acid_techno.mp3", Location="/music/acid_techno.mp3",
                     DateCreated="2024-09-01", BitRate=320, SampleRate=44100),
        MockContent(ID=10, Title="Deep Dub", ArtistName="DJ Gamma", GenreName="Dub Techno",
                     KeyName="6B", BPM=12000, Rating=3, DJPlayCount=8, Length=450,
                     FolderPath="/music/deep_dub.mp3", Location="/music/deep_dub.mp3",
                     DateCreated="2024-10-10", BitRate=320, SampleRate=44100),
        # Apple Music streaming track (can't export to USB)
        MockContent(ID=11, Title="Streaming Track", ArtistName="DJ Stream", GenreName="House",
                     KeyName="3A", BPM=12600, Rating=0, DJPlayCount=0, Length=200,
                     FolderPath="apple-music:tracks:1234567890", Location="apple-music:tracks:1234567890",
                     DateCreated="2024-11-01", BitRate=0, SampleRate=44100),
        # Soft-deleted track — should be filtered out
        MockContent(ID=99, Title="Deleted Track", ArtistName="Nobody", GenreName="Unknown",
                     KeyName="1A", BPM=12000, Rating=0, DJPlayCount=0, Length=100,
                     FolderPath="/music/deleted.mp3", Location="/music/deleted.mp3",
                     rb_local_deleted=1),
    ]


@pytest.fixture
def mock_playlists():
    return [
        MockPlaylist(ID=100, Name="Warm Up", Attribute=0, created_at="2024-01-01"),
        MockPlaylist(ID=101, Name="Peak Time", Attribute=0, created_at="2024-02-01"),
        MockPlaylist(ID=102, Name="Sets", Attribute=1, is_folder=True),  # folder
        MockPlaylist(ID=103, Name="Smart Mix", Attribute=0, is_smart_playlist=True, SmartList="<criteria/>"),
        MockPlaylist(ID=199, Name="Deleted Playlist", Attribute=0, rb_local_deleted=1),
    ]


@pytest.fixture
def mock_playlist_songs():
    return [
        MockPlaylistSong(ID=1001, PlaylistID=100, ContentID=1, TrackNo=1),
        MockPlaylistSong(ID=1002, PlaylistID=100, ContentID=5, TrackNo=2),
        MockPlaylistSong(ID=1003, PlaylistID=100, ContentID=3, TrackNo=3),
        MockPlaylistSong(ID=1004, PlaylistID=100, ContentID=99, TrackNo=4),  # orphan: points to deleted content
        MockPlaylistSong(ID=1005, PlaylistID=101, ContentID=2, TrackNo=1),
        MockPlaylistSong(ID=1006, PlaylistID=101, ContentID=9, TrackNo=2),
    ]


@pytest.fixture
def mock_histories():
    return [
        MockHistory(ID=200, Name="2024", Attribute=1, DateCreated="2024-01-01"),  # folder
        MockHistory(ID=201, Name="2024-08-15 Set", Attribute=0, DateCreated="2024-08-15 22:00:00"),
        MockHistory(ID=202, Name="2024-09-01 Set", Attribute=0, DateCreated="2024-09-01 21:00:00"),
    ]


@pytest.fixture
def mock_history_songs():
    return [
        MockHistorySong(HistoryID=201, ContentID=1, TrackNo=1),
        MockHistorySong(HistoryID=201, ContentID=2, TrackNo=2),
        MockHistorySong(HistoryID=201, ContentID=5, TrackNo=3),
        MockHistorySong(HistoryID=202, ContentID=4, TrackNo=1),
        MockHistorySong(HistoryID=202, ContentID=9, TrackNo=2),
    ]


@pytest.fixture
def mock_db(mock_content_list, mock_playlists, mock_playlist_songs, mock_histories, mock_history_songs):
    """A MagicMock of Rekordbox6Database wired with test data."""
    db = MagicMock()

    # get_content() with no args returns iterable of all content
    # get_content(ID=x) returns single item or None
    def get_content_side_effect(**kwargs):
        if "ID" in kwargs:
            content_id = kwargs["ID"]
            for c in mock_content_list:
                if c.ID == content_id:
                    return c
            return None
        return mock_content_list

    db.get_content = MagicMock(side_effect=get_content_side_effect)

    db.get_playlist = MagicMock(return_value=mock_playlists)

    def get_playlist_songs_side_effect(**kwargs):
        pid = kwargs.get("PlaylistID")
        return [s for s in mock_playlist_songs if s.PlaylistID == pid]

    db.get_playlist_songs = MagicMock(side_effect=get_playlist_songs_side_effect)

    db.get_history = MagicMock(return_value=mock_histories)

    def get_history_songs_side_effect(**kwargs):
        hid = kwargs.get("HistoryID")
        return [s for s in mock_history_songs if s.HistoryID == hid]

    db.get_history_songs = MagicMock(side_effect=get_history_songs_side_effect)

    db.add_to_playlist = MagicMock()
    db.remove_from_playlist = MagicMock()
    db.create_playlist = MagicMock(return_value=MockPlaylist(ID=500, Name="New Playlist"))
    db.create_playlist_folder = MagicMock(return_value=MockPlaylist(ID=501, Name="New Folder"))
    db.delete_playlist = MagicMock()
    db.commit = MagicMock()
    db.close = MagicMock()

    return db


@pytest.fixture
def database(mock_db, tmp_path):
    """A RekordboxDatabase instance wired with mock db, ready to use."""
    rdb = RekordboxDatabase()
    rdb.db = mock_db
    rdb._connected = True
    rdb.database_path = tmp_path
    return rdb
