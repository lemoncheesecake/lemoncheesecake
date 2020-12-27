import * as React from 'react';
import TimeExtraInfoView from './TimeExtraInfoView';
import ResultRowView from './ResultRowView';

export interface SetupProps {
    result: Result,
    id: string,
    description: string
}

export class SetupView extends React.Component<SetupProps, {}> {
    render() {
        const result = this.props.result;

        return (
            <ResultRowView id={this.props.id} status={result.status} steps={result.steps}>
                <td>
                    <div className="extra-info-container">
                        <h5 className="special">
                            {this.props.description}&nbsp;
                            {/* eslint jsx-a11y/anchor-has-content: "off" */}
                            <a href={"#" + this.props.id} className="glyphicon glyphicon-link extra-info anchorlink" style={{fontSize: "90%"}}/>
                        </h5>
                        <TimeExtraInfoView start={result.start_time} end={result.end_time}/>
                    </div>
                </td>
                <td>
                </td>
                <td>
                </td>
            </ResultRowView>
        )
    }
}

export default SetupView;