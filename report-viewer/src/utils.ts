export function humanize_duration(duration: number): string {
    return (duration / 1000) + "s";
}

export function normalize_datetime(dt: DateTime): string {
    return dt.replace(" ", "T");
}

export function get_timestamp_from_datetime(dt: DateTime): number {
    return new Date(normalize_datetime(dt)).getTime();
}

export function get_duration_between_datetimes(dt1: DateTime, dt2: DateTime): string {
    const duration = get_timestamp_from_datetime(dt2) - get_timestamp_from_datetime(dt1);
    return humanize_duration(duration);
}

export function get_time_from_datetime(dt: DateTime) {
    return dt.split(" ")[1];
}
