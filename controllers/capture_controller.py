"""
ScrollSnap
==========

Capture Controller

The UI-facing entry point for everything capture related:
selecting a region, taking a single screenshot, or running a
full auto-scrolling capture session.

Per the architecture, the UI never touches `CaptureEngine`,
`RegionManager`, or platform backends directly - it only calls
methods on this controller.
"""

from __future__ import annotations

from typing import Callable

from capture.capture_engine import CaptureEngine
from capture.capture_scheduler import CaptureScheduler
from capture.capture_session import RuntimeCaptureSession
from capture.region_manager import RegionManager

from capture.auto_scroll.auto_scroll_engine import AutoScrollEngine
from capture.auto_scroll.end_detector import EndDetector
from capture.auto_scroll.scroll_strategies import (
    ScrollDirection,
    ScrollRequest,
    default_registry,
)
from capture.auto_scroll.smart_timing import StabilityWaiter
from capture.auto_scroll.timing import FrameRateLimiter

from core.event_bus import EventBus, event_bus as default_event_bus
from image_processing.alignment import images_visually_stable, quick_fingerprint
from image_processing.pillow_backend import PillowScrollDetector
from models.capture_region import CaptureRegion
from models.enums import CaptureMode, ShapeType
from models.frame import Frame
from models.rectangle import Rectangle

from platforms.factory import PlatformServices


class CaptureController:
    """
    Coordinates region selection and screenshot capture.
    """

    def __init__(
        self,
        platform_services: PlatformServices | None = None,
        bus: EventBus | None = None,
    ) -> None:

        self._services = platform_services or PlatformServices()

        self._bus = bus or default_event_bus

        self._region_manager = RegionManager()

        self._scheduler = CaptureScheduler()

        self._auto_scroll: AutoScrollEngine | None = None

        self._scroll_detector: PillowScrollDetector | None = None

        self._previous_captured_frame: Frame | None = None

        self._pending_scroll_request = ScrollRequest()

        self._engine = CaptureEngine(
            screen_capture=self._services.screen_capture,
            region_manager=self._region_manager,
            scheduler=self._scheduler,
        )

        self._engine.add_listener(self._on_frame_captured)

        self._engine.add_error_listener(self._on_capture_error)

        self._scroll_strategy_name = "Mouse Wheel"

    # ---------------------------------------------------------
    # Properties
    # ---------------------------------------------------------

    @property
    def region_manager(self) -> RegionManager:
        return self._region_manager

    @property
    def engine(self) -> CaptureEngine:
        return self._engine

    @property
    def session(self) -> RuntimeCaptureSession | None:
        return self._engine.session

    @property
    def is_running(self) -> bool:
        return self._engine.running

    @property
    def frames(self) -> list[Frame]:
        session = self.session
        return list(session.frames) if session else []

    # ---------------------------------------------------------
    # Region Selection
    # ---------------------------------------------------------

    def select_region(
        self,
        rectangle: Rectangle,
        shape: ShapeType = ShapeType.RECTANGLE,
        mode: CaptureMode = CaptureMode.REGION,
        monitor_id: int = 0,
    ) -> CaptureRegion:

        region = CaptureRegion(
            rectangle=rectangle,
            shape=shape,
            mode=mode,
            monitor_id=monitor_id,
        )

        self._region_manager.set_region(region)

        self._bus.publish("capture.region_selected", region)

        return region

    def active_window_bounds(self) -> Rectangle | None:
        """
        Convenience helper for the UI: bounds of the currently
        active window, if the platform's window detector can
        determine one.
        """

        window = self._services.window_detector.active_window()

        return window.bounds if window else None

    # ---------------------------------------------------------
    # Single Snapshot
    # ---------------------------------------------------------

    def snap(self) -> Frame:
        """
        Take exactly one screenshot of the selected region,
        outside of any running session.
        """

        region = self._region_manager.region

        if region is None:
            raise RuntimeError("No capture region selected.")

        image = self._services.screen_capture.capture_region(
            region.rectangle
        )

        frame = Frame(image=image, region=region.rectangle)

        self._bus.publish("capture.snapped", frame)

        return frame

    # ---------------------------------------------------------
    # Continuous / Scrolling Capture
    # ---------------------------------------------------------

    def start_capture(
        self,
        interval_seconds: float = 0.5,
        auto_scroll: bool = False,
        scroll_direction: ScrollDirection = ScrollDirection.DOWN,
        scroll_amount: int = 3,
        scroll_strategy: str | None = None,
        smart_timing: bool = True,
    ) -> RuntimeCaptureSession:

        self._scheduler.set_interval(interval_seconds)

        self._previous_captured_frame = None

        if auto_scroll:

            self._auto_scroll = self._build_auto_scroll_engine(
                scroll_strategy or self._scroll_strategy_name,
                smart_timing=smart_timing,
                max_wait=interval_seconds * 4,
            )

            self._engine.set_auto_scroll(self._auto_scroll)

            self._pending_scroll_request = ScrollRequest(
                direction=scroll_direction,
                amount=scroll_amount,
            )

        else:

            self._auto_scroll = None

            self._engine.set_auto_scroll(None)

        session = self._engine.start()

        self._bus.publish("capture.started", session)

        return session

    def stop_capture(self) -> None:

        self._engine.stop()

        self._bus.publish("capture.stopped", self.session)

    def cancel_capture(self) -> None:

        self._engine.cancel()

        self._bus.publish("capture.cancelled", None)

    def pause_capture(self) -> None:
        self._engine.pause()

    def resume_capture(self) -> None:
        self._engine.resume()

    def set_scroll_strategy(self, name: str) -> None:
        self._scroll_strategy_name = name

    def available_scroll_strategies(self) -> list[str]:
        return default_registry.names()

    # ---------------------------------------------------------
    # Events
    # ---------------------------------------------------------

    def add_frame_listener(
        self, callback: Callable[[Frame], None]
    ) -> None:
        self._engine.add_listener(callback)

    def remove_frame_listener(
        self, callback: Callable[[Frame], None]
    ) -> None:
        self._engine.remove_listener(callback)

    def _on_frame_captured(self, frame: Frame) -> None:

        self._bus.publish("capture.frame_captured", frame)

        if (
            self._auto_scroll is not None
            and self._auto_scroll.running
            and self._scroll_detector is not None
        ):

            analysis = self._scroll_detector.analyze(
                self._previous_captured_frame, frame
            )

            keep_going = self._auto_scroll.step(
                self._pending_scroll_request, analysis
            )

            if not keep_going:
                self.stop_capture()

        self._previous_captured_frame = frame

    def _on_capture_error(self, exc: Exception) -> None:
        """
        The scheduler's background thread caught an exception from
        a capture callback. Republish it on the event bus so the
        UI (running on the main thread) can tell the user instead
        of the failure disappearing along with the dead thread.
        """

        self._bus.publish("capture.error", exc)

    # ---------------------------------------------------------
    # Internal Construction
    # ---------------------------------------------------------

    def _build_auto_scroll_engine(
        self,
        strategy_name: str,
        smart_timing: bool = True,
        max_wait: float = 2.0,
    ) -> AutoScrollEngine:

        strategy = default_registry.get(strategy_name)

        self._scroll_detector = PillowScrollDetector()

        stability_waiter = None

        if smart_timing:
            stability_waiter = self._build_stability_waiter(max_wait)

        return AutoScrollEngine(
            strategy=strategy,
            controller=self._services.input_controller,
            detector=self._scroll_detector,
            end_detector=EndDetector(),
            limiter=FrameRateLimiter(interval=0.3),
            stability_waiter=stability_waiter,
            move_to_target=self._build_cursor_positioner(),
        )

    def _build_cursor_positioner(self) -> Callable[[], None] | None:
        """
        Mouse-wheel input is routed by the OS to whatever window is
        under the cursor, not whichever window last had focus. If
        we don't explicitly move the cursor over the capture
        region before each scroll, the very first scroll (and
        possibly every one after it) lands on the ScrollSnap
        window itself - typically wherever the user's cursor was
        when they clicked "Start Scrolling Capture" - and nothing
        in the target app appears to move at all.
        """

        region = self._region_manager.region

        if region is None:
            return None

        rect = region.rectangle

        target_x = int(rect.left + rect.width / 2)

        target_y = int(rect.top + rect.height / 2)

        def move_to_region() -> None:
            self._services.mouse.move(target_x, target_y)

        return move_to_region

    def _build_stability_waiter(
        self, max_wait: float
    ) -> StabilityWaiter | None:
        """
        Build a `StabilityWaiter` that probes the real, currently
        selected capture region and waits for rendering to settle
        after each scroll, instead of a fixed delay.
        """

        region = self._region_manager.region

        if region is None:
            return None

        def probe():

            image = self._services.screen_capture.capture_region(
                region.rectangle
            )

            return quick_fingerprint(image)

        return StabilityWaiter(
            probe=probe,
            is_stable=images_visually_stable,
            max_wait=max(0.1, max_wait),
        )

    def shutdown(self) -> None:

        self.cancel_capture()

        self._services.screen_capture.close()
