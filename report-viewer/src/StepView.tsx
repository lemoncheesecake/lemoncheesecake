import * as React from 'react';
import TimeExtraInfoView from './TimeExtraInfoView';
import CheckView from './CheckView';
import Log from './LogView';
import AttachmentView from './AttachmentView';
import UrlView from './UrlView';
import { DisplayOptions, is_step_entry_to_be_displayed } from './DisplayOptionsView';

function get_step_outcome(step: Step) {
    for (let entry of step.entries) {
        if (entry.type === "log" && entry.level === "error")
            return false;
        else if (entry.type === "check" && entry.is_successful === false)
            return false;
    }
    return true;
}

function StepOutcomeView(props: {step: Step}) {
    return (
        get_step_outcome(props.step) ?
        <span className="glyphicon glyphicon-ok text-success"></span> :
        <span className="glyphicon glyphicon-remove text-danger"></span>
    );
}

interface Props {
    step: Step
}

function StepView(props: Props) {
    const step = props.step;

    return (
        <tr className="step">
            <td colSpan={4} className="visibility-master">
                <h6 className="extra-info-container">
                    <span style={{fontSize: "120%"}}>
                        <StepOutcomeView step={step}/>
                        &nbsp;
                        <span className="multi-line-text"><strong>{step.description}</strong></span>
                    </span>
                    <TimeExtraInfoView start={step.start_time} end={step.end_time}/>
                </h6>
            </td>
        </tr>
    )
}

function render_step_entry(entry: StepEntry, index: number) {
    switch (entry.type) {
        case "check":
            return <CheckView check={entry} key={index}/>;
        case "log":
            return <Log log={entry} key={index}/>;
        case "attachment":
            return <AttachmentView attachment={entry} key={index}/>
        case "url":
            return <UrlView url={entry} key={index}/>
    }
}

export function render_steps(steps: Array<Step>, display_option: DisplayOptions) {
    let rows = [];
    let index = 0;

    for (let step of steps) {
        let step_entry_rows = [];
        for (let step_entry of step.entries) {
            if (is_step_entry_to_be_displayed(step_entry, display_option)) {
                step_entry_rows.push(render_step_entry(step_entry, index++));
            }
        }
        if (step_entry_rows.length > 0) {
            rows.push(<StepView step={step} key={index++}/>);
            for (let row of step_entry_rows)
                rows.push(row);
        }
    }

    return rows;
}
