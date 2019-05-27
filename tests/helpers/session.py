import pytest
from pytest_mock import mocker

import lemoncheesecake.session

@pytest.fixture
def session_mock(mocker):
    mocker.patch("lemoncheesecake.session.get_session")
    return mocker


def get_mocked_logged_checks():
    return [call[1] for call in lemoncheesecake.session.get_session.return_value.method_calls if call[0] == "log_check"]


def get_last_mocked_logged_check():
    return next(reversed(get_mocked_logged_checks()))
