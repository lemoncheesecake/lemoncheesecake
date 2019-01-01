def humanize_duration(duration, show_milliseconds=False):
    ret = ""

    if duration / 3600 >= 1:
        ret += ("%02dh" if ret else "%dh") % (duration / 3600)
        duration %= 3600

    if duration / 60 >= 1:
        ret += ("%02dm" if ret else "%dm") % (duration / 60)
        duration %= 60

    if show_milliseconds:
        if duration >= 0:
            ret += ("%06.03fs" if ret else "%.03fs") % duration
    else:
        if duration >= 1:
            ret += ("%02ds" if ret else "%ds") % duration
        if ret == "":
            ret = "%.03fs" % duration

    return ret
