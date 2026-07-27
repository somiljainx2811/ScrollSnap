"""
Tests for history.capture_history.CaptureHistory and its
underlying storage.
"""

from __future__ import annotations

from PIL import Image

from history.capture_history import CaptureHistory
from storage.recent_projects import RecentProjectsStorage
from storage.thumbnails import ThumbnailStorage


def make_history(tmp_path):

    return CaptureHistory(
        recent=RecentProjectsStorage(index_path=tmp_path / "recent.json"),
        thumbnails=ThumbnailStorage(thumbnail_dir=tmp_path / "thumbs"),
    )


class TestCaptureHistory:

    def test_record_creates_entry_with_thumbnail(self, tmp_path):

        history = make_history(tmp_path)

        image = Image.new("RGB", (400, 300), (10, 20, 30))

        entry = history.record(image, title="Test Capture")

        assert entry.width == 400

        assert entry.height == 300

        assert entry.thumbnail_path is not None

    def test_list_returns_most_recent_first(self, tmp_path):

        history = make_history(tmp_path)

        history.record(Image.new("RGB", (10, 10)), title="First")

        history.record(Image.new("RGB", (10, 10)), title="Second")

        entries = history.list()

        assert entries[0].title == "Second"

        assert entries[1].title == "First"

    def test_remove_deletes_entry_and_thumbnail(self, tmp_path):

        history = make_history(tmp_path)

        entry = history.record(Image.new("RGB", (10, 10)), title="Gone")

        history.remove(entry.id)

        assert history.list() == []

    def test_clear_empties_history(self, tmp_path):

        history = make_history(tmp_path)

        history.record(Image.new("RGB", (10, 10)))

        history.record(Image.new("RGB", (10, 10)))

        history.clear()

        assert history.list() == []

    def test_max_entries_caps_list_length(self, tmp_path):

        recent = RecentProjectsStorage(
            index_path=tmp_path / "recent.json", max_entries=2
        )

        history = CaptureHistory(
            recent=recent,
            thumbnails=ThumbnailStorage(thumbnail_dir=tmp_path / "thumbs"),
        )

        for i in range(5):
            history.record(Image.new("RGB", (10, 10)), title=f"Entry {i}")

        assert len(history.list()) == 2
