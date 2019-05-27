import * as React from 'react';

interface Props {
    check: CheckData
    expanded: boolean
}

class Step extends React.Component<Props, {}> {
    render() {
        const check = this.props.check;

        return (
            <tr className="step_entry check" style={{display: this.props.expanded ? "" : "none"}}>
                <td className={check.is_successful ? "text-success" : "text-danger"}>CHECK</td>
                <td className="check_description">{check.description}</td>
                <td className="check_result" colSpan={2}>{check.details}</td>
            </tr>
        )
    }
}

export default Step;
