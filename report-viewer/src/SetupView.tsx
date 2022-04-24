import TimeExtraInfoView from './TimeExtraInfoView';
import ResultRowView from './ResultRowView';
import {FocusProps} from './ResultRowView';
import { DisplayOptions } from './NavbarView';

export interface SetupProps extends FocusProps {
    result: Result,
    id: string,
    description: string,
    display_options: DisplayOptions
}

export function SetupView(props: SetupProps) {
    return (
        <ResultRowView
            id={props.id} status={props.result.status} steps={props.result.steps}
            focus={props.focus} onFocusChange={props.onFocusChange}
            display_options={props.display_options}>
            <td>
                <div className="extra-info-container">
                    <h5 className="special">
                        {props.description}&nbsp;
                        {/* eslint jsx-a11y/anchor-has-content: "off" */}
                        <a
                            href={"#" + props.id}
                            className="bi bi-link-45deg anchorlink extra-info visibility-slave"
                            style={{fontSize: "120%"}}/>
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
