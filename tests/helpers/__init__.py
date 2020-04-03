import pytest

pytest.register_assert_rewrite(
    "helpers.cli",
    "helpers.matching",
    "helpers.project",
    "helpers.report",
    "helpers.reporttests",
    "helpers.runner",
    "helpers.utils"
)
