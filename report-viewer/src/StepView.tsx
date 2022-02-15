import TimeExtraInfoView from './TimeExtraInfoView';
import CheckView from './CheckView';
import Log from './LogView';
import AttachmentView from './AttachmentView';
import UrlView from './UrlView';
import { DisplayOptions, is_step_entry_to_be_displayed } from './DisplayOptionsView';
import { useAccordionHandler, AccordionOpeningIndicator } from './accordion';

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

interface Props {
    step: Step,
    display_options: DisplayOptions,
    opened: boolean,
    openingChange: (opened: boolean) => void
}

export function StepView(props: Props) {
    const step = props.step;
    let index = 0;
    let entries = [];
    const [opened, openingHandler] = useAccordionHandler(props.openingChange, props.opened);

    for (let step_entry of props.step.entries) {
        if (is_step_entry_to_be_displayed(step_entry, props.display_options)) {
            entries.push(<StepEntry entry={step_entry} key={index++}/>);
        }
    }

    if (entries.length > 0) {
        return (
            <>
                <tr className="step" style={{cursor: "pointer"}}
                    title={
                        opened ?
                        "Click to collapse step details.\nDouble-click to collapse ALL step details." :
                        "Click to expand step details.\nDouble-click to expand ALL step details."
                    }
                    onClick={openingHandler}
                    >
                    <td colSpan={4} className="visibility-master">
                        <h6 className="extra-info-container">
                            <span>
                                <StepOutcomeView step={step}/>
                                &nbsp;&nbsp;
                                <span className="multi-line-text"><strong>{step.description}</strong></span>
                                &nbsp;&nbsp;
                                <AccordionOpeningIndicator opened={opened}/>
                            </span>
                            <TimeExtraInfoView start={step.start_time} end={step.end_time}/>
                        </h6>
                    </td>
                </tr>
                {opened ? entries : undefined}
            </>
        );

    } else {
        return null;
    }
}
