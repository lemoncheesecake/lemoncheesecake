import * as React from 'react';
import TimeExtraInfo from './TimeExtraInfo';

interface Props {
    log: LogData,
    expanded: boolean
}

function get_log_level_text_class(level: LogLevel) {
    switch (level) {
        case "error":
            return "text-danger";
        case "warn":
            return "text-warning";
        default:
            return "text-info";
    }
}

class Step extends React.Component<Props, {}> {
    render() {
        const log = this.props.log;

        return (
            <tr className="step_entry log" style={{display: this.props.expanded ? "" : "none"}}>
                <td className={"text-uppercase " + get_log_level_text_class(log.level)}>{log.level}</td>
                <td colSpan={3}>
                    <div className="extra-info-container">
                        <samp>{log.message}</samp>
                        <TimeExtraInfo start={log.time}/>
                    </div>
                </td>
            </tr>
        )
    }
}

export default Step;
