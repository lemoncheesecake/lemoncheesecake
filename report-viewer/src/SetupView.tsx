import TimeExtraInfoView from './TimeExtraInfoView';
import ResultRowView from './ResultRowView';
import {FocusProps} from './ResultRowView';

export interface SetupProps extends FocusProps {
    result: Result,
    id: string,
    description: string,
}

export function SetupView(props: SetupProps) {
    return (
        <ResultRowView
            id={props.id} status={props.result.status} steps={props.result.steps}
            focus={props.focus} onFocusChange={props.onFocusChange}>
            <td>
                <div className="extra-info-container">
                    <h5 className="special">
                        {props.description}&nbsp;
                        {/* eslint jsx-a11y/anchor-has-content: "off" */}
                        <a
                            href={"#" + props.id}
                            className="glyphicon glyphicon-link anchorlink extra-info visibility-slave"
                            style={{fontSize: "90%"}}/>
                    </h5>
                    <TimeExtraInfoView start={props.result.start_time} end={props.result.end_time}/>
                </div>
            </td>
            <td>
            </td>
            <td>
            </td>
        </ResultRowView>
    )
}

export default SetupView;
