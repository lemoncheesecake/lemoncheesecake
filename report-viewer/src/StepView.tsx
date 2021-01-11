import * as React from 'react';
import TimeExtraInfoView from './TimeExtraInfoView';
import CheckView from './CheckView';
import Log from './LogView';
import AttachmentView from './AttachmentView';
import UrlView from './UrlView';

function get_step_outcome(step: Step) {
    for (let entry of step.entries) {
        if (entry.type === "log" && entry.level === "error")
            return false;
        else if (entry.type === "check" && entry.is_successful === false)
            return false;
    }
    return true;
}

function StepOutcome(props: {step: Step}) {
    return (
        get_step_outcome(props.step) ?
        <span className="glyphicon glyphicon-ok text-success"></span> :
        <span className="glyphicon glyphicon-remove text-danger"></span>
    );
}

interface Props {
    step: Step,
    expanded: boolean
}

function StepView(props: Props) {
    const step = props.step;

    return (
        <tr className="step" style={{display: props.expanded ? "" : "none"}}>
            <td colSpan={4}>
                <h6 className="extra-info-container">
                    <span style={{fontSize: "120%"}}>
                        <StepOutcome step={step}/>
                        &nbsp;
                        <span className="multi-line-text"><strong>{step.description}</strong></span>
                    </span>
                    <TimeExtraInfoView start={step.start_time} end={step.end_time}/>
                </h6>
            </td>
        </tr>
    )
}

function render_step_entry(entry: StepEntry, expanded: boolean, index: number) {
    switch (entry.type) {
        case "check":
            return <CheckView check={entry} expanded={expanded} key={index}/>;
        case "log":
            return <Log log={entry} expanded={expanded} key={index}/>;
        case "attachment":
            return <AttachmentView attachment={entry} expanded={expanded} key={index}/>
        case "url":
            return <UrlView url={entry} expanded={expanded} key={index}/>
    }
}

export function render_steps(steps: Array<Step>, expanded: boolean) {
    let rows = [];
    let index = 0;

    for (let step of steps) {
        rows.push(<StepView step={step} expanded={expanded} key={index++}/>)
        for (let step_entry of step.entries) {
            rows.push(render_step_entry(step_entry, expanded, index++));
        }
    }

    return rows;
}
