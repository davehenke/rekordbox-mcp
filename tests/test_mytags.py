"""Tests for the My Tag layer (djmdMyTag / djmdSongMyTag)."""

import pytest


class TestGetMyTags:
    async def test_tree_structure(self, database):
        result = await database.get_my_tags()

        # Two categories, sorted by Seq
        names = [c["name"] for c in result["categories"]]
        assert names == ["STYLE", "VIBE"]

        style = result["categories"][0]
        assert style["id"] == "1"
        tag_names = [t["name"] for t in style["tags"]]
        assert tag_names == ["House", "Techno"]  # soft-deleted "Deleted Tag" excluded

    async def test_track_counts(self, database):
        result = await database.get_my_tags()
        style = result["categories"][0]
        house = next(t for t in style["tags"] if t["name"] == "House")
        # s1, s2 active; s5 soft-deleted -> 2
        assert house["track_count"] == 2

    async def test_orphan_tags(self, database):
        result = await database.get_my_tags()
        orphan_names = [t["name"] for t in result["orphan_tags"]]
        assert orphan_names == ["Orphaned"]

    async def test_summary(self, database):
        result = await database.get_my_tags()
        summary = result["summary"]
        assert summary["category_count"] == 2
        # House, Techno, Dark, Orphaned = 4 active leaves (Deleted Tag excluded)
        assert summary["tag_count"] == 4
        assert summary["total_assignments"] == 4  # s1..s4 active


class TestGetTrackMyTags:
    async def test_track_with_tags(self, database):
        tags = await database.get_track_my_tags("1")
        names = sorted(t.name for t in tags)
        assert names == ["Dark", "House"]

    async def test_category_resolved(self, database):
        tags = await database.get_track_my_tags("1")
        house = next(t for t in tags if t.name == "House")
        assert house.category == "STYLE"
        assert house.category_id == "1"
        assert house.is_category is False

    async def test_track_without_tags(self, database):
        tags = await database.get_track_my_tags("7")
        assert tags == []


class TestGetTracksByMyTag:
    async def test_by_id(self, database):
        tracks = await database.get_tracks_by_my_tag(my_tag_id="1001")
        ids = sorted(t.id for t in tracks)
        assert ids == ["1", "5"]  # s1, s2 (s5 soft-deleted)

    async def test_by_name_case_insensitive(self, database):
        tracks = await database.get_tracks_by_my_tag(my_tag_name="house")
        ids = sorted(t.id for t in tracks)
        assert ids == ["1", "5"]

    async def test_unknown_tag_returns_empty(self, database):
        tracks = await database.get_tracks_by_my_tag(my_tag_name="Nonexistent")
        assert tracks == []


class TestAddMyTagToTracks:
    async def test_adds_new_and_skips_existing(self, database, mock_db):
        # Track 1 already has House (s1); track 8 does not
        result = await database.add_my_tag_to_tracks(["1", "8"], my_tag_id="1001")
        assert result["added"] == ["8"]
        assert result["skipped"] == ["1"]
        assert result["failed"] == []
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    async def test_backup_created(self, database):
        with pytest.MonkeyPatch.context() as mp:
            called = {"n": 0}
            mp.setattr(database, "_create_backup", lambda: called.__setitem__("n", 1))
            await database.add_my_tag_to_tracks(["8"], my_tag_id="1001")
            assert called["n"] == 1

    async def test_missing_track_failed(self, database):
        result = await database.add_my_tag_to_tracks(["123456"], my_tag_id="1001")
        assert result["added"] == []
        assert result["failed"][0]["track_id"] == "123456"

    async def test_category_rejected(self, database):
        with pytest.raises(RuntimeError, match="category"):
            await database.add_my_tag_to_tracks(["8"], my_tag_id="1")

    async def test_unknown_tag_raises(self, database):
        with pytest.raises(RuntimeError, match="not found"):
            await database.add_my_tag_to_tracks(["8"], my_tag_id="999999")

    async def test_by_name(self, database):
        result = await database.add_my_tag_to_tracks(["8"], my_tag_name="Techno")
        assert result["tag_name"] == "Techno"
        assert result["added"] == ["8"]


class TestRemoveMyTagFromTracks:
    async def test_soft_deletes_assignment(self, database, mock_db, mock_song_my_tags):
        result = await database.remove_my_tag_from_tracks(["1"], my_tag_id="1001")
        assert result["removed"] == ["1"]
        # s1 (track 1, tag 1001) should now be soft-deleted
        s1 = next(s for s in mock_song_my_tags if s.ID == "s1")
        assert s1.rb_local_deleted == 1
        mock_db.commit.assert_called_once()

    async def test_not_carrying_tag(self, database):
        result = await database.remove_my_tag_from_tracks(["7"], my_tag_id="1001")
        assert result["removed"] == []
        assert result["not_found"] == ["7"]


class TestCreateMyTag:
    async def test_create_category(self, database, mock_db):
        result = await database.create_my_tag_category("USE")
        assert result["id"] == "987654321"
        assert result["seq"] == 3  # after STYLE(1), VIBE(2)
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    async def test_create_tag_under_category_by_name(self, database, mock_db):
        result = await database.create_my_tag("Deep House", category_name="STYLE")
        assert result["category_id"] == "1"
        assert result["seq"] == 3  # after House(1), Techno(2)
        mock_db.add.assert_called_once()

    async def test_create_tag_unknown_category(self, database):
        with pytest.raises(RuntimeError, match="category not found"):
            await database.create_my_tag("X", category_name="Nope")


class TestDeleteMyTag:
    async def test_delete_single_tag(self, database, mock_db, mock_my_tags):
        result = await database.delete_my_tag(my_tag_id="1001")
        assert result["tags_deleted"] == 1
        assert result["assignments_removed"] == 2  # s1, s2
        tag = next(t for t in mock_my_tags if t.ID == "1001")
        assert tag.rb_local_deleted == 1

    async def test_delete_category_cascades(self, database, mock_my_tags):
        result = await database.delete_my_tag(my_tag_name="STYLE")
        assert result["is_category"] is True
        # STYLE + its active children House, Techno = 3
        assert result["tags_deleted"] == 3

    async def test_delete_unknown_raises(self, database):
        with pytest.raises(RuntimeError, match="not found"):
            await database.delete_my_tag(my_tag_id="does-not-exist")
