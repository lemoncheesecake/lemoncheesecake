import pytest
from pytest_mock import mocker

import lemoncheesecake.runtime

@pytest.fixture
def runtime_mock(mocker):
    mocker.patch("lemoncheesecake.runtime.get_runtime")
    return mocker


def get_mocked_logged_checks():
    return [call[1] for call in lemoncheesecake.runtime.get_runtime.return_value.method_calls if call[0] == "log_check"]


def get_last_mocked_logged_check():
    return next(reversed(get_mocked_logged_checks()))
