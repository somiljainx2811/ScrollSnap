"""
Tests for history.recovery.SessionRecoveryManager and
storage.cache.CacheStorage - the crash-recovery mechanism.
"""

from __future__ import annotations

from PIL import Image

from history.recovery import SessionRecoveryManager
from models.capture_region import CaptureRegion
from models.capture_session import CaptureSession
from models.enums import CaptureStatus
from models.frame import Frame
from models.rectangle import Rectangle
from storage.cache import CacheStorage
from storage.sessions import SessionStorage


def make_manager(tmp_path):

    return SessionRecoveryManager(
        session_dir=tmp_path / "sessions",
        session_storage=SessionStorage(),
        cache_storage=CacheStorage(cache_dir=tmp_path / "cache"),
    )


class TestCacheStorage:

    def test_save_and_load_frame_image(self, tmp_path):

        cache = CacheStorage(cache_dir=tmp_path / "cache")

        frame = Frame(
            image=Image.new("RGB", (50, 40), (10, 20, 30)),
            region=Rectangle.from_xywh(0, 0, 50, 40),
        )

        path = cache.save_frame("session-1", frame)

        assert path.exists()

        assert frame.cache_path == path

        reloaded = cache.load_frame_image(frame)

        assert reloaded.size == (50, 40)

    def test_hydrate_only_loads_if_image_missing(self, tmp_path):

        cache = CacheStorage(cache_dir=tmp_path / "cache")

        frame = Frame(
            image=Image.new("RGB", (10, 10)),
            region=Rectangle.from_xywh(0, 0, 10, 10),
        )

        cache.save_frame("session-1", frame)

        frame.image = None

        cache.hydrate(frame)

        assert frame.image is not None

    def test_clear_session_removes_files(self, tmp_path):

        cache = CacheStorage(cache_dir=tmp_path / "cache")

        frame = Frame(
            image=Image.new("RGB", (10, 10)),
            region=Rectangle.from_xywh(0, 0, 10, 10),
        )

        cache.save_frame("session-x", frame)

        cache.clear_session("session-x")

        assert not cache.session_dir("session-x").exists()


class TestSessionRecoveryManager:

    def test_no_pending_recovery_by_default(self, tmp_path):

        manager = make_manager(tmp_path)

        assert not manager.has_pending_recovery()

        assert manager.check_for_recovery() is None

    def test_mark_active_then_recover(self, tmp_path):

        manager = make_manager(tmp_path)

        region = CaptureRegion(rectangle=Rectangle.from_xywh(0, 0, 100, 100))

        session = CaptureSession(region=region, status=CaptureStatus.CAPTURING)

        frame = Frame(
            image=Image.new("RGB", (100, 100), (5, 5, 5)),
            region=region.rectangle,
        )

        manager.cache.save_frame(session.id, frame)

        session.add_frame(frame)

        manager.mark_active(session)

        assert manager.has_pending_recovery()

        recovered = manager.check_for_recovery()

        assert recovered is not None

        assert recovered.frame_count == 1

        assert recovered.frames[0].image is not None

    def test_clear_active_removes_marker(self, tmp_path):

        manager = make_manager(tmp_path)

        session = CaptureSession()

        manager.mark_active(session)

        manager.clear_active()

        assert not manager.has_pending_recovery()

    def test_discard_recovery_cleans_up_cache(self, tmp_path):

        manager = make_manager(tmp_path)

        session = CaptureSession()

        frame = Frame(
            image=Image.new("RGB", (10, 10)),
            region=Rectangle.from_xywh(0, 0, 10, 10),
        )

        manager.cache.save_frame(session.id, frame)

        session.add_frame(frame)

        manager.mark_active(session)

        manager.discard_recovery()

        assert not manager.has_pending_recovery()

        assert not manager.cache.session_dir(session.id).exists()
