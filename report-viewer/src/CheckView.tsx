interface Props {
    check: Check
}

function StepView(props: Props) {
    const check = props.check;

    return (
        <tr className="step_entry check">
            <td className={check.is_successful ? "text-success" : "text-danger"}>CHECK</td>
            <td className="check_description">{check.description}</td>
            <td className="check_result" colSpan={2}>{check.details}</td>
        </tr>
    )
}

export default StepView;
