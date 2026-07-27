"""
Regression test for a real bug found running on an actual
Windows machine: the installed `mss` package version there only
exposed the older, lowercase `mss.mss()` factory function, not
the newer `mss.MSS` class this project originally assumed -
`AttributeError: module 'mss' has no attribute 'MSS'`.

`platforms.mss_compat.create_mss()` should work regardless of
which API the installed `mss` version exposes.
"""

from __future__ import annotations

import types

from platforms.mss_compat import create_mss
from tests.conftest import requires_display


def _fail_if_called():

    raise AssertionError(
        "mss.mss() should not be called when mss.MSS is available"
    )


class TestMssCompat:

    def test_uses_mss_capital_when_available(self, monkeypatch):

        import platforms.mss_compat as mss_compat

        created = {"value": False}

        class FakeInstance:
            pass

        def fake_MSS():
            created["value"] = True
            return FakeInstance()

        fake_module = types.SimpleNamespace(
            MSS=fake_MSS, mss=_fail_if_called,
        )

        monkeypatch.setattr(mss_compat, "mss", fake_module)

        instance = create_mss()

        assert created["value"] is True

        assert isinstance(instance, FakeInstance)

    def test_falls_back_to_lowercase_mss_when_MSS_missing(
        self, monkeypatch
    ):
        """
        This is exactly the real-world failure mode: an older
        installed `mss` version with no `MSS` attribute at all.
        """

        import platforms.mss_compat as mss_compat

        created = {"value": False}

        class FakeInstance:
            pass

        def fake_mss():
            created["value"] = True
            return FakeInstance()

        fake_module = types.SimpleNamespace(mss=fake_mss)
        # Deliberately no `.MSS` attribute at all, matching the
        # older mss version that caused the original crash.

        monkeypatch.setattr(mss_compat, "mss", fake_module)

        instance = create_mss()

        assert created["value"] is True

        assert isinstance(instance, FakeInstance)

    def test_raises_clear_error_when_neither_api_exists(self, monkeypatch):

        import pytest

        import platforms.mss_compat as mss_compat

        fake_module = types.SimpleNamespace()  # neither MSS nor mss

        monkeypatch.setattr(mss_compat, "mss", fake_module)

        with pytest.raises(RuntimeError, match="mss"):
            create_mss()

    @requires_display
    def test_real_mss_module_works(self):
        """
        Sanity check against whatever `mss` version is actually
        installed in this environment.
        """

        instance = create_mss()

        assert instance is not None

        instance.close()
