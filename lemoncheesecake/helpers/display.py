

def get_status_color(status):
    if status == "passed":
        return "green"
    elif status == "failed":
        return "red"
    elif status == "disabled":
        return "cyan"
    else:
        return "yellow"
