import pytest

import lemoncheesecake.api as lcc


def test_log_invalid_argument():
    with pytest.raises(TypeError, match="got int"):
        lcc.log_debug(1)

    with pytest.raises(TypeError, match="got int"):
        lcc.log_info(1)

    with pytest.raises(TypeError, match="got int"):
        lcc.log_warning(1)

    with pytest.raises(TypeError, match="got int"):
        lcc.log_error(1)


def test_log_check_invalid_arguments():
    with pytest.raises(TypeError, match="got int"):
        lcc.log_check(1, True)

    with pytest.raises(TypeError, match="got str"):
        lcc.log_check("foo", "bar")

    with pytest.raises(TypeError, match="got int"):
        lcc.log_check("foo", True, 1)


def test_prepare_attachment_invalid_arguments():
    with pytest.raises(TypeError, match="got int"):
        lcc.save_attachment_content("foo", "foo.txt", 1)


def test_set_step_invalid_argument():
    with pytest.raises(TypeError, match="got int"):
        lcc.set_step(1)


def test_log_url_invalid_argument():
    with pytest.raises(TypeError, match="got int"):
        lcc.log_url(1, "foo")

    with pytest.raises(TypeError, match="got int"):
        lcc.log_url("http://www.example.com", 1)


def test_add_report_info_invalid_argument():
    with pytest.raises(TypeError, match="got int"):
        lcc.add_report_info(1, "bar")

    with pytest.raises(TypeError, match="got int"):
        lcc.add_report_info("foo", 1)
