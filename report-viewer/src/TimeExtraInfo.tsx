import * as React from 'react';
import {get_time_from_datetime, get_duration_between_datetimes} from './utils';

interface Props {
    start: string,
    end?: string | null
}

class TimeExtraInfo extends React.Component<Props, {}> {
    render() {
        const start_time = get_time_from_datetime(this.props.start);
        
        if (this.props.end) {
            const duration = get_duration_between_datetimes(this.props.start, this.props.end);
            return <span className='extra-info'>{start_time} &rarr; {duration}</span>;
        } else {
            return <span className='extra-info'>{start_time}</span>;
        }
    }
}

export default TimeExtraInfo;
