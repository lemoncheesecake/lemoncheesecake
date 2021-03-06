import * as React from 'react';
import {render_steps} from './StepView';
import { scroller } from 'react-scroll';

export interface Focus {
    id: string,
    scrollTo: boolean
}

export interface OnFocusChange {
    (id: string, scrollTo?: boolean) : void
}

export interface FocusProps {
    focus: Focus,
    onFocusChange: OnFocusChange
}

interface State {
    expanded: boolean
}

interface Props extends FocusProps {
    id: string,
    status: Status | null,
    status_details?: string | null,
    steps: Array<Step>
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
        <span className={text_class} style={{fontSize: "120%"}}>
            {props.status ? props.status.toUpperCase() : "IN PROGRESS"}
        </span>
    );
}

function ExpandIndicator(props: {expanded: boolean, hasSteps: boolean}) {
    if (props.hasSteps) {
        if (props.expanded) {
            return  (
                <span className="glyphicon glyphicon-chevron-down" title="Collapse">
                </span>
            );
        } else {
            return  (
                <span className="visibility-slave glyphicon glyphicon-chevron-right" title="Expand">
                </span>
            );
        }
    } else {
        // keep an always invisible glyphicon to keep a consistent alignment with other result rows
        return  (
            <span className="glyphicon glyphicon-chevron-right" style={{visibility: "hidden"}}>
            </span>
        );
    }
}

class ResultRowView extends React.Component<Props, State> {
    domRef: any;

    constructor(props: Props) {
        super(props);
        this.state = {
            expanded: false
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
          });
    }

    componentDidMount() {
        if (this.isFocused() && this.props.focus.scrollTo) {
            this.scrollTo();
        }
    }
    componentDidUpdate = this.componentDidMount

    render() {
        const hasSteps = this.props.steps.length > 0;

        return (
            <tbody>
                <tr id={this.props.id} className="test visibility-master" key={this.props.id} ref={(re) => { this.domRef = re }}>
                    <td className="test_status" title={this.props.status_details || ""}
                        style={hasSteps ? {cursor: "pointer"} : undefined}
                        onClick={hasSteps ? this.toggle : undefined}>
                        <ExpandIndicator expanded={this.isFocused()} hasSteps={hasSteps}/>
                        &nbsp;
                        <Status status={this.props.status}/>
                    </td>
                    {this.props.children}
                </tr>
                { render_steps(this.props.steps, this.isFocused()) }
            </tbody>
        )
    }
}

export default ResultRowView;
