"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from rekordbox_mcp.models import (
    Track, Playlist, HistorySession, HistoryTrack, HistoryStats,
    SearchOptions, LibraryStats,
)


class TestTrack:
    def test_basic_construction(self):
        track = Track(id="1", title="Test", artist="Artist")
        assert track.id == "1"
        assert track.bpm == 0.0
        assert track.rating == 0

    def test_rating_bounds(self):
        track = Track(id="1", title="T", artist="A", rating=5)
        assert track.rating == 5
        with pytest.raises(ValidationError):
            Track(id="1", title="T", artist="A", rating=6)

    def test_key_field_accepts_any_string(self):
        # No-op validator was removed; any string should work
        track = Track(id="1", title="T", artist="A", key="5A")
        assert track.key == "5A"

    def test_duration_formatted(self):
        track = Track(id="1", title="T", artist="A", length=185)
        assert track.duration_formatted() == "3:05"

    def test_duration_formatted_zero(self):
        track = Track(id="1", title="T", artist="A", length=0)
        assert track.duration_formatted() == "0:00"


class TestPlaylist:
    def test_basic(self):
        pl = Playlist(id="1", name="My Playlist")
        assert pl.is_folder is False
        assert pl.track_count == 0

    def test_date_validator_with_datetime(self):
        from datetime import datetime
        dt = datetime(2024, 6, 15, 10, 30, 0)
        pl = Playlist(id="1", name="P", created_date=dt)
        assert pl.created_date == "2024-06-15 10:30:00"


class TestSearchOptions:
    def test_defaults(self):
        opts = SearchOptions()
        assert opts.limit == 50
        assert opts.query == ""

    def test_bpm_range_validation(self):
        with pytest.raises(ValidationError):
            SearchOptions(bpm_min=140, bpm_max=120)

    def test_rating_range_validation(self):
        with pytest.raises(ValidationError):
            SearchOptions(rating_min=4, rating_max=2)

    def test_limit_bounds(self):
        with pytest.raises(ValidationError):
            SearchOptions(limit=0)
        with pytest.raises(ValidationError):
            SearchOptions(limit=1001)


class TestHistoryModels:
    def test_history_session(self):
        s = HistorySession(id="1", name="2024-08-15 Set", track_count=10)
        assert s.is_folder is False

    def test_history_track(self):
        t = HistoryTrack(id="1", track_number=3, history_id="100")
        assert t.track_number == 3
        assert t.title == ""

    def test_history_stats_defaults(self):
        stats = HistoryStats()
        assert stats.total_sessions == 0
        assert stats.favorite_genres == []


class TestLibraryStats:
    def test_playtime_formatted_hours(self):
        stats = LibraryStats(
            total_tracks=100,
            total_playtime_seconds=7500,
            average_bpm=128.0,
            genre_distribution={"House": 50},
            database_path="/test",
            last_updated="2024-01-01",
        )
        assert stats.total_playtime_formatted() == "2h 5m"

    def test_playtime_formatted_minutes_only(self):
        stats = LibraryStats(
            total_tracks=10,
            total_playtime_seconds=1800,
            average_bpm=120.0,
            genre_distribution={},
            database_path="/test",
            last_updated="2024-01-01",
        )
        assert stats.total_playtime_formatted() == "30m"
