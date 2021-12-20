import { useState, useEffect } from 'react';
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

export function useDoubleExpander(propagateExpandedChange: (expanded: boolean) => void,
                                  externalExpanded: boolean) : [boolean, () => void] { 
    const [expanded, setExpanded] = useState(true);
    const [lastClick, setLastClick] = useState(0);

    useEffect(() => {
        setExpanded(externalExpanded);
    }, [externalExpanded]);

    // this handler handle both single and double click
    return [
        expanded,
        () => {
            const now = Date.now();
            // handle the simple click or the first click of the double click
            if (now - lastClick > 300) {
                setExpanded(!expanded);
            // handle the second click of a double click
            } else {
                propagateExpandedChange(expanded);
            }
            setLastClick(now);
        }
    ];
}


export function ExpanderIndicator(props: {expanded: boolean}) {
    if (props.expanded) {
        return  (
            <span className="glyphicon glyphicon-resize-full visibility-slave" title="Collapse">
            </span>
        );
    } else {
        return  (
            <span className="glyphicon glyphicon-resize-small visibility-slave" title="Expand">
            </span>
        );
    }
}
