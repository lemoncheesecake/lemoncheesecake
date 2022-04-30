import * as React from 'react';
import TimeExtraInfoView from './TimeExtraInfoView';
import ResultRowView from './ResultRowView';
import { FocusProps } from './ResultRowView';
import { DisplayOptions } from './NavbarView';
import { MetadataView } from './MetadataView';

interface Props extends FocusProps {
    test: Test,
    test_id: string,
    display_options: DisplayOptions
}

function TestView(props: Props) {
    const test = props.test;
    const test_id = props.test_id;

    return (
        <ResultRowView
            id={test_id} status={test.status} status_details={test.status_details} steps={test.steps}
            focus={props.focus} onFocusChange={props.onFocusChange}
            display_options={props.display_options}>
            <td>
                <div className="extra-info-container">
                    <h5>
                        <span className="multi-line-text">{test.description}</span>&nbsp;
                        {/* eslint jsx-a11y/anchor-has-content: "off" */}
                        <a
                            href={"#" + test_id}
                            className="bi bi-link-45deg anchorlink extra-info visibility-slave"
                            style={{fontSize: "120%"}}
                        />
                        <br/>
                        <small>{test_id}</small>
                    </h5>
                    <TimeExtraInfoView start={test.start_time} end={test.end_time}/>
                </div>
            </td>
            <td colSpan={2}>
                <MetadataView result={test}/>
            </td>
        </ResultRowView>
    )
}

export default TestView;
