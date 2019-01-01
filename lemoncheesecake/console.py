def test_status_to_color(status):
    return {
        "passed": "green",
        "failed": "red",
        "disabled": "cyan",
    }.get(status, "yellow")
