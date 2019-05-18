import * as React from 'react';
import {humanize_time_from_iso8601, humanize_duration, get_time_from_iso8601} from './utils';

interface Props {
    start: string,
    end?: string | null
}

class TimeExtraInfo extends React.Component<Props, {}> {
    render() {
        const start_time = humanize_time_from_iso8601(this.props.start);
        
        if (this.props.end) {
            const duration = humanize_duration(get_time_from_iso8601(this.props.end) - get_time_from_iso8601(this.props.start), true);
            return <span className='extra-info'>{start_time} &rarr; {duration}</span>;
        } else {
            return <span className='extra-info'>{start_time}</span>;
        }
    }
}

export default TimeExtraInfo;
