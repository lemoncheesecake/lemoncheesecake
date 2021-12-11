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

function StepExpanderView(props: {expanded: boolean}) {
    if (props.expanded) {
        return  (
            <span className="glyphicon glyphicon-resize-full visibility-slave" title="Collapse">
            </span>
        );
    } else {
        return  (
            <span className="glyphicon glyphicon-resize-small visibility-slave" title="Expand">
            </span>
        );
    }
}

function StepOutcomeView(props: {step: Step}) {
    return (
        get_step_outcome(props.step) ?
        <span className="glyphicon glyphicon-ok text-success"></span> :
        <span className="glyphicon glyphicon-remove text-danger"></span>
    );
}

function StepEntry(props: {entry: StepEntry}) {
    switch (props.entry.type) {
        case "check":
            return <CheckView check={props.entry}/>;
        case "log":
            return <Log log={props.entry}/>;
        case "attachment":
            return <AttachmentView attachment={props.entry}/>
        case "url":
            return <UrlView url={props.entry}/>
    }
}

export function StepView(props: {step: Step, display_options: DisplayOptions}) {
    const step = props.step;
    let index = 0;
    let entries = [];
    const [expanded, setExpanded] = React.useState(true);

    for (let step_entry of props.step.entries) {
        if (is_step_entry_to_be_displayed(step_entry, props.display_options)) {
            entries.push(<StepEntry entry={step_entry} key={index++}/>);
        }
    }

    if (entries.length > 0) {
        return (
            <>
                <tr className="step" style={{cursor: "pointer"}}
                    title={expanded ? "Click to collapse step details" : "Click to expand step details"}
                    onClick={() => setExpanded(!expanded)}>
                    <td colSpan={4} className="visibility-master">
                        <h6 className="extra-info-container">
                            <span style={{fontSize: "120%"}}>
                                <StepOutcomeView step={step}/>
                                &nbsp;&nbsp;
                                <span className="multi-line-text"><strong>{step.description}</strong></span>
                                &nbsp;&nbsp;
                                <StepExpanderView expanded={expanded}/>
                            </span>
                            <TimeExtraInfoView start={step.start_time} end={step.end_time}/>
                        </h6>
                    </td>
                </tr>
                {expanded ? entries : undefined}
            </>
        );

    } else {
        return null;
    }
}
