import * as React from 'react';
import {render_steps} from './Step';
import { scroller } from 'react-scroll';

let all_rows = {};

export function get_result_row_by_id(id: string): ResultRow {
    return all_rows[id];
}

function collapseIfExpanded() {
    for (let row_id in all_rows) {
        let row = all_rows[row_id];
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
    steps: Array<StepData>
}

function get_text_class_from_test_status(status: Status | null) {
    if (status == null)
        return ""
    
    if (status == "passed")
        return "text-success";
    
    if (status == "failed")
        return "text-danger";

    if (status == "disabled")
        return "text-default";

    return "text-warning";
}

class ResultRow extends React.Component<Props, State> {
    domRef: any;

    constructor() {
        super();
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
        all_rows[this.props.id] = this;
    }

    render() {
        return (
            <tbody>
                <tr id={this.props.id} className="test" key={this.props.id} ref={(re) => { this.domRef = re }}>
                    <td className="test_status" title={this.props.status_details || ""}
                        style={this.props.steps.length > 0 ? {cursor: "pointer"} : undefined}
                        onClick={this.props.steps.length > 0 ? this.toggle : undefined}>
                        <span className={get_text_class_from_test_status(this.props.status)} style={{fontSize: "120%"}}>
                            {this.props.status ? this.props.status.toUpperCase() : "IN PROGRESS"}
                        </span>
                    </td>
                    {this.props.children}
                </tr>
                { render_steps(this.props.steps, this.state.expanded) }
            </tbody>
        )
    }
}

export default ResultRow;