"""
ScrollSnap
==========

MSS Compatibility Shim

Different installed versions of the `mss` package expose
different entry points:

    - Newer versions: `mss.MSS` (a class)
    - Older versions: only `mss.mss` (a factory function;
      still present but deprecated on newer versions)

Rather than hard-coding one or the other and breaking on
whichever version a user's `pip install` happens to resolve,
everything in ScrollSnap that needs an `mss` instance should go
through `create_mss()` here.
"""

from __future__ import annotations

import mss


def create_mss():
    """
    Construct an `mss` screen-capture instance, regardless of
    which API the installed `mss` version exposes.
    """

    factory = getattr(mss, "MSS", None) or getattr(mss, "mss", None)

    if factory is None:
        raise RuntimeError(
            "The installed 'mss' package exposes neither 'MSS' "
            "nor 'mss' - it may not be a genuine mss install "
            "(check for a naming collision with another package) "
            "or may be a version too old/new for this shim. Try: "
            "pip install --upgrade mss"
        )

    return factory()
