"""
ScrollSnap
==========

DPI Awareness

On Windows, an application that hasn't declared itself
"DPI-aware" gets coordinates and window sizes reported by the OS
in a virtualized, scaled coordinate space - which does *not*
match the physical pixels `mss` captures. On a 150% scaled
display, for example, a region the user drags out at what Tk
reports as (0,0)-(300,300) actually corresponds to a
450x450 physical-pixel area, so the captured screenshot would be
cropped wrong.

Declaring per-monitor DPI awareness *before* any window is
created makes Windows report physical pixel coordinates
everywhere, so Tk's event coordinates line up with what `mss`
captures.

This has no effect (and is safe to call) on Linux and macOS.
"""

from __future__ import annotations

import sys


def enable_dpi_awareness() -> bool:
    """
    Attempt to mark this process as per-monitor DPI aware.
    Must be called before any Tk window is created. Returns True
    if awareness was successfully set (or wasn't needed), False
    if the attempt failed (the app will still run, just with
    the OS-scaled coordinate caveat above).
    """

    if not sys.platform.startswith("win"):
        return True

    import ctypes

    # Try the modern, per-monitor-v2 API first (Windows 10+).
    try:

        DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4

        result = ctypes.windll.user32.SetProcessDpiAwarenessContext(
            DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
        )

        if result:
            return True

    except (AttributeError, OSError):
        pass

    # Fall back to the Windows 8.1+ API.
    try:

        PROCESS_PER_MONITOR_DPI_AWARE = 2

        hresult = ctypes.windll.shcore.SetProcessDpiAwareness(
            PROCESS_PER_MONITOR_DPI_AWARE
        )

        # S_OK == 0
        if hresult == 0:
            return True

    except (AttributeError, OSError):
        pass

    # Last resort: the original Vista-era, system-wide-only API.
    try:
        return bool(ctypes.windll.user32.SetProcessDPIAware())

    except (AttributeError, OSError):
        return False
