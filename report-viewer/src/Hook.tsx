import * as React from 'react';
import TimeExtraInfo from './TimeExtraInfo';
import ResultRow from './ResultRow';

export interface HookProps {
    hook: HookData,
    id: string,
    description: string
}

export class Hook extends React.Component<HookProps, {}> {
    render() {
        const hook = this.props.hook;

        return (
            <ResultRow id={this.props.id} status={hook.outcome ? "passed" : "failed"} steps={hook.steps}>
                <td>
                    <div className="extra-info-container">
                        <h5 className="special">
                            {this.props.description}&nbsp;
                            <a href={"#" + this.props.id} className="glyphicon glyphicon-link extra-info anchorlink" style={{fontSize: "90%"}}/>
                        </h5>
                        <TimeExtraInfo start={hook.start_time} end={hook.end_time}/>
                    </div>
                </td>
                <td>
                </td>
                <td>
                </td>
            </ResultRow>
        )
    }
}

export default Hook;