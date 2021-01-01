import * as React from 'react';
import {humanize_time_from_iso8601, humanize_duration, get_time_from_iso8601} from './utils';

interface Props {
    start: string,
    end?: string | null
}

class TimeExtraInfoView extends React.Component<Props, {}> {
    render() {
        const start_time = humanize_time_from_iso8601(this.props.start);
        
        if (this.props.end) {
            const duration = humanize_duration(get_time_from_iso8601(this.props.end) - get_time_from_iso8601(this.props.start), true);
            return (
                <span className='extra-info visibility-slave'>
                    {start_time} <span className="glyphicon glyphicon-arrow-right"/> {duration}
                </span>
            );
        } else {
            return <span className='extra-info visibility-slave'>{start_time}</span>;
        }
    }
}

export default TimeExtraInfoView;
