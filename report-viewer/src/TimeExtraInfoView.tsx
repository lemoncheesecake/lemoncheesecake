import {humanize_time_from_iso8601, humanize_duration, get_time_from_iso8601} from './utils';

interface Props {
    start: string,
    end?: string | null
}

function TimeExtraInfoView(props: Props) {
    const start_time = humanize_time_from_iso8601(props.start);

    if (props.end) {
        const duration = humanize_duration(get_time_from_iso8601(props.end) - get_time_from_iso8601(props.start), true);
        return (
            <span className='extra-info time-extra-info visibility-slave'>
                {start_time} <i className="bi bi-clock-history"/> {duration}
            </span>
        );
    } else {
        return <span className='extra-info time-extra-info visibility-slave'>{start_time}</span>;
    }
}

export default TimeExtraInfoView;
