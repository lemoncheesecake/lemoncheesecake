import * as moment from 'moment';

export function humanize_duration(duration: number): string {
    return (duration / 1000) + "s";
}

export function get_timestamp_from_datetime(dt: string): number {
    return new Date(dt).getTime();
}

export function get_duration_between_datetimes(dt1: string, dt2: string): string {
    const duration = get_timestamp_from_datetime(dt2) - get_timestamp_from_datetime(dt1);
    return humanize_duration(duration);
}

export function get_time_from_datetime(dt: string) {
    return moment(dt).format("HH:mm:ss.SSS");
}
