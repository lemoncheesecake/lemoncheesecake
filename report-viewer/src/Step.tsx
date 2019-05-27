import * as React from 'react';
import TimeExtraInfo from './TimeExtraInfo';
import Check from './Check';
import Log from './Log';
import Attachment from './Attachment';
import Url from './Url';

interface Props {
    step: StepData,
    expanded: boolean
}

function get_step_outcome(step: StepData) {
    for (let entry of step.entries) {
        if (entry.type == "log" && entry.level == "error")
            return false;
        else if (entry.type == "check" && entry.is_successful == false)
            return false;
    }
    return true;
}

class Step extends React.Component<Props, {}> {
    render() {
        const step = this.props.step;

        return (
            <tr className="step" style={{display: this.props.expanded ? "" : "none"}}>
                <td colSpan={4}>
                    <h6 className="extra-info-container">
                        <span style={{fontSize: "120%"}}>
                            {
                                get_step_outcome(step) ?
                                    <span className="glyphicon glyphicon-ok text-success"></span> :
                                    <span className="glyphicon glyphicon-remove text-danger"></span>
                            }
                            &nbsp;
                            <span className="multi-line-text"><strong>{step.description}</strong></span>
                        </span>
                        <TimeExtraInfo start={step.start_time} end={step.end_time}/>
                    </h6>
                </td>
            </tr>
        )
    }
}

function render_step_entry(entry: StepEntryData, expanded: boolean, index: number) {
    switch (entry.type) {
        case "check":
            return <Check check={entry} expanded={expanded} key={index}/>;
        case "log":
            return <Log log={entry} expanded={expanded} key={index}/>;
        case "attachment":
            return <Attachment attachment={entry} expanded={expanded} key={index}/>
        case "url":
            return <Url url={entry} expanded={expanded} key={index}/>
    }
}

export function render_steps(steps: Array<StepData>, expanded: boolean) {
    let rows = [];
    let index = 0;

    for (let step of steps) {
        rows.push(<Step step={step} expanded={expanded} key={index++}/>)
        for (let step_entry of step.entries) {
            rows.push(render_step_entry(step_entry, expanded, index++));
        }
    }

    return rows;
}