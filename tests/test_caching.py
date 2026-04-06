"""Tests for content caching and backup deduplication."""

import time
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from rekordbox_mcp.database import RekordboxDatabase


class TestContentCache:
    async def test_cache_hit(self, database, mock_db):
        """Repeated calls within TTL should use cache (single get_content call)."""
        await database.get_track_count()
        await database.get_track_count()
        await database.get_track_count()

        # get_content() should be called only once (cache hit on 2nd and 3rd)
        assert mock_db.get_content.call_count == 1

    async def test_cache_miss_after_ttl(self, database, mock_db):
        """Cache should refresh after TTL expires."""
        database._content_cache_ttl = 0.01  # 10ms TTL for testing

        await database.get_track_count()
        assert mock_db.get_content.call_count == 1

        time.sleep(0.02)  # Wait past TTL
        await database.get_track_count()
        assert mock_db.get_content.call_count == 2

    async def test_invalidate_forces_refresh(self, database, mock_db):
        """_invalidate_content_cache should force a reload."""
        await database.get_track_count()
        assert mock_db.get_content.call_count == 1

        database._invalidate_content_cache()
        await database.get_track_count()
        assert mock_db.get_content.call_count == 2

    async def test_mutation_invalidates_cache(self, database, mock_db):
        """Mutation operations should invalidate the cache."""
        # Prime the cache
        await database.get_track_count()
        assert mock_db.get_content.call_count == 1

        # Mutation should invalidate
        await database.add_track_to_playlist("100", "1")
        assert database._content_cache is None

        # Next read should reload
        await database.get_track_count()
        assert mock_db.get_content.call_count == 2

    async def test_filters_deleted_content(self, database):
        """Cache should not contain soft-deleted content."""
        count = await database.get_track_count()
        assert count == 11  # 12 total - 1 deleted


class TestBackupDedup:
    async def test_first_mutation_creates_backup(self, database, tmp_path):
        """First mutation should create a backup file."""
        # Create a fake master.db to be backed up
        fake_db = tmp_path / "master.db"
        fake_db.write_text("fake database")

        await database.add_track_to_playlist("100", "1")
        backup_files = list(tmp_path.glob("master_backup_*.db"))
        assert len(backup_files) == 1

    async def test_second_mutation_skips_backup(self, database, tmp_path):
        """Second mutation within cooldown should skip backup."""
        fake_db = tmp_path / "master.db"
        fake_db.write_text("fake database")

        await database.add_track_to_playlist("100", "1")
        await database.add_track_to_playlist("100", "2")

        backup_files = list(tmp_path.glob("master_backup_*.db"))
        assert len(backup_files) == 1  # only one backup

    async def test_backup_after_cooldown(self, database, tmp_path):
        """Mutation after cooldown should create a new backup."""
        database._backup_cooldown = 0.05  # 50ms for testing

        fake_db = tmp_path / "master.db"
        fake_db.write_text("fake database")

        await database.add_track_to_playlist("100", "1")
        first_backup_time = database._last_backup_time

        time.sleep(0.1)  # Wait well past cooldown
        await database.add_track_to_playlist("100", "2")
        second_backup_time = database._last_backup_time

        # The backup time should have been updated (new backup was created)
        assert second_backup_time > first_backup_time

    async def test_backup_handles_missing_path(self):
        """Backup should handle missing database_path gracefully."""
        db = RekordboxDatabase()
        db.database_path = None
        # Should not raise
        db._create_backup()
