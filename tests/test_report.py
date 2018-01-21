from lemoncheesecake.reporting.report import format_timestamp, parse_timestamp


def _test_timestamp_round(raw, rounded):
    assert parse_timestamp(format_timestamp(raw)) == rounded


def test_format_and_parse_timestamp_1():
    _test_timestamp_round(1485093460.874194, 1485093460.874)


def test_format_and_parse_timestamp_2():
    _test_timestamp_round(1485093460.874794, 1485093460.875)


def test_format_and_parse_timestamp_3():
    _test_timestamp_round(1485093460.999001, 1485093460.999)


def test_format_and_parse_timestamp_4():
    _test_timestamp_round(1485093460.999999, 1485093461.0)


def test_format_and_parse_timestamp_5():
    _test_timestamp_round(1485105524.353112, 1485105524.353)
