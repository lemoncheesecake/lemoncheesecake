import * as React from 'react';
import TimeExtraInfoView from './TimeExtraInfoView';

interface Props {
    log: Log,
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

class LogView extends React.Component<Props, {}> {
    render() {
        const log = this.props.log;

        return (
            <tr className="step_entry log" style={{display: this.props.expanded ? "" : "none"}}>
                <td className={"text-uppercase " + get_log_level_text_class(log.level)}>{log.level}</td>
                <td colSpan={3}>
                    <div className="extra-info-container visibility-master">
                        <samp>{log.message}</samp>
                        <TimeExtraInfoView start={log.time}/>
                    </div>
                </td>
            </tr>
        )
    }
}

export default LogView;
