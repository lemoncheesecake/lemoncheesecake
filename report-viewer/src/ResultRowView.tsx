import * as React from 'react';
import {render_steps} from './StepView';
import { scroller } from 'react-scroll';

let all_rows = new Map<string, ResultRowView>();

export function get_result_row_by_id(id: string): ResultRowView {
    const ret = all_rows.get(id);
    if (ret === undefined) {
        throw new Error();
    }
    return ret;
}

function collapseIfExpanded() {
    for (let row of all_rows.values()) {
        if (row.isExpanded()) {
            row.collapse()
            break;
        }
    }
}

interface State {
    expanded: boolean
}

interface Props {
    id: string,
    status: Status | null,
    status_details?: string | null,
    steps: Array<Step>
}

function Status(props: any) {
    let text_class;
    switch (props.value) {
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
            {props.value ? props.value.toUpperCase() : "IN PROGRESS"}
        </span>
    );
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

    isExpanded() {
        return this.state.expanded;
    }

    expand() {
        this.setState({expanded: true})
    }

    collapse() {
        this.setState({expanded: false})
    }

    toggle() {
        if (this.isExpanded()) {
            this.collapse()
        } else {
            collapseIfExpanded();
            this.expand();
        }
    }

    scrollTo() {
        scroller.scrollTo(this.props.id, {
            duration: 1500,
            delay: 100,
            smooth: "easeInOutQuint",
          });
   }

    componentDidMount() {
        all_rows.set(this.props.id, this);
    }

    render() {
        return (
            <tbody>
                <tr id={this.props.id} className="test" key={this.props.id} ref={(re) => { this.domRef = re }}>
                    <td className="test_status" title={this.props.status_details || ""}
                        style={this.props.steps.length > 0 ? {cursor: "pointer"} : undefined}
                        onClick={this.props.steps.length > 0 ? this.toggle : undefined}>
                        <Status value={this.props.status}/>
                    </td>
                    {this.props.children}
                </tr>
                { render_steps(this.props.steps, this.state.expanded) }
            </tbody>
        )
    }
}

export default ResultRowView;