import * as React from 'react';
import {StepView} from './StepView';
import {scroller} from 'react-scroll';
import {DisplayOptions} from './NavbarView';

export interface Focus {
    id: string,
    scrollTo: boolean
}

export interface OnFocusChange {
    (id: string) : void
}

export interface FocusProps {
    focus: Focus,
    onFocusChange: OnFocusChange
}

interface State {
    opened: boolean,
    stepsOpened: boolean
}

interface Props extends FocusProps {
    id: string,
    status: Status | null,
    status_details?: string | null,
    steps: Array<Step>,
    display_options: DisplayOptions
}

function Status(props: {status: string | null}) {
    let text_class;
    switch (props.status) {
        case null:
            text_class = "";
            break;
        case "passed":
            text_class = "text-success";
            break;
        case "failed":
            text_class = "text-danger";
            break;
        case "disabled":
            text_class = "text-default";
            break;
        default:
            text_class = "text-warning";

    }

    return (
        <span className={text_class}>
            {props.status ? props.status.toUpperCase() : "IN PROGRESS"}
        </span>
    );
}

function HiddenOpeningIndicator() {
    // keep an always invisible icon to keep a consistent alignment with other result rows
    return  (
        <span className="bi bi-caret-right-fill" style={{visibility: "hidden"}}>
        </span>
    );
}

function OpeningIndicator(props: {opened: boolean, hasSteps: boolean}) {
    if (props.hasSteps) {
        if (props.opened) {
            return  (
                <span className="bi bi-caret-down-fill">
                </span>
            );
        } else {
            return  (
                <span className="visibility-slave bi bi-caret-right-fill">
                </span>
            );
        }
    } else {
        return <HiddenOpeningIndicator/>;
    }
}

class ResultRowView extends React.Component<Props, State> {
    domRef: any;

    constructor(props: Props) {
        super(props);
        this.state = {
            opened: false,
            stepsOpened: true
        };
        this.toggle = this.toggle.bind(this);
        this.domRef = null;
    }

    isFocused() {
        return this.props.id === this.props.focus.id;
    }

    toggle() {
        this.props.onFocusChange(this.isFocused() ? "" : this.props.id)
    }

    scrollTo() {
        scroller.scrollTo(this.props.id, {
            duration: 1500,
            delay: 100,
            smooth: "easeInOutQuint",
            offset: -60 // add an offset to take the top-fixed navbar height into account
          });
    }

    componentDidMount() {
        if (this.isFocused() && this.props.focus.scrollTo) {
            this.setState({stepsOpened: true});
            this.scrollTo();
        }
    }
    componentDidUpdate = this.componentDidMount

    render() {
        const hasSteps = this.props.steps.length > 0;
        let index = 0;

        return (
            <tbody>
                <tr id={this.props.id} className="test visibility-master"
                    key={this.props.id} ref={(re) => { this.domRef = re }}
                    style={hasSteps ? {cursor: "pointer"} : undefined}
                    onClick={hasSteps ? this.toggle : undefined}
                    title={hasSteps ? (this.isFocused() ? "Click to collapse test details." : "Click to expand test details.") : undefined}>
                    <td className="test_status" title={this.props.status_details || ""}>
                        <OpeningIndicator opened={this.isFocused()} hasSteps={hasSteps}/>
                        &nbsp;
                        <Status status={this.props.status}/>
                        <HiddenOpeningIndicator/> { /* quick & dirty trick to have a centered status */ }
                    </td>
                    {this.props.children}
                </tr>
                {
                    this.isFocused() ?
                        this.props.steps.map(s => (
                            <StepView step={s} display_options={this.props.display_options}
                                opened={this.state.stepsOpened}
                                openingChange={(opened: boolean) => this.setState({stepsOpened: opened})}
                                key={index++}/>)
                        ) : []
                }
            </tbody>
        )
    }
}

export default ResultRowView;
