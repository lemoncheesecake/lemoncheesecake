import time

from lemoncheesecake.reporting.report import format_timestamp, parse_timestamp

def test_format_and_parse_timestamp_1():
    ts = 1485093460.874194
    
    assert parse_timestamp(format_timestamp(ts)) == 1485093460.874

def test_format_and_parse_timestamp_2():
    ts = 1485093460.874794
    
    assert parse_timestamp(format_timestamp(ts)) == 1485093460.875

def test_format_and_parse_timestamp_3():
    ts = 1485093460.999001
    
    assert parse_timestamp(format_timestamp(ts)) == 1485093460.999

def test_format_and_parse_timestamp_4():
    ts = 1485093460.999999
    
    assert parse_timestamp(format_timestamp(ts)) == 1485093461.0

def test_format_and_parse_timestamp_5():
    ts = 1485105524.353112
    
    assert parse_timestamp(format_timestamp(ts)) == 1485105524.353