"""Proves the live tier is genuinely skipped by default.

If someone (you, on Day 40, tired) deletes the skip hook from conftest.py,
this test goes red immediately.
"""

from pathlib import Path

pytest_plugins = ["pytester"]


def test_live_tests_are_skipped_by_default(pytester):
    hook_source = (Path(__file__).parent / "conftest.py").read_text(encoding="utf-8")
    pytester.makeconftest(hook_source)
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.live
        def test_costs_quota():
            raise AssertionError("this must never run in the default suite")
        """
    )
    result = pytester.runpytest("-p", "no:randomly")
    result.assert_outcomes(skipped=1)


def test_live_tests_run_when_asked(pytester):
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.live
        def test_opt_in():
            assert True
        """
    )
    result = pytester.runpytest("-m", "live")
    result.assert_outcomes(passed=1)
