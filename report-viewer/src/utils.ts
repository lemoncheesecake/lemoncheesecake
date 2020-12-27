// import * as moment from 'moment';
import moment from 'moment';
import {sprintf} from 'sprintf-js';

export function get_time_from_iso8601(val: string) {
    return new Date(val).getTime() / 1000;
}

export function humanize_time_from_iso8601(dt: string) {
    return moment(dt).format("HH:mm:ss.SSS");
}

export function humanize_datetime_from_iso8601(dt: string) {
    return moment(dt).locale("en").format("ddd MMM D HH:mm:ss YYYY")
}

export function humanize_duration(duration: number, show_milliseconds=false) {
    let ret = "";

    if (duration / 3600 >= 1) {
        ret += sprintf("%dh", duration / 3600);
        duration %= 3600;
    }

    if (duration / 60 >= 1) {
        ret += sprintf(ret ? "%02dm" : "%dm", duration / 60);
        duration %= 60;
    }

    if (show_milliseconds) {
        if (duration >= 0) {
            ret += sprintf(ret ? "%06.03fs" : "%.03fs", duration);
        }
    } else {
        if (duration >= 1) {
            ret += sprintf(ret ? "%02ds" : "%ds", duration);
        }
        if (ret === "") {
            ret = sprintf("%.03fs", duration);
        }
    }

    return ret;
}