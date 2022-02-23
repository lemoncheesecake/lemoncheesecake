function CheckView(props: {check: Check}) {
    return (
        <tr className="step_entry check table-active">
            <td className={props.check.is_successful ? "text-success" : "text-danger"}>CHECK</td>
            <td className="check_description">{props.check.description}</td>
            <td className="check_result" colSpan={2}>{props.check.details}</td>
        </tr>
    )
}

export default CheckView;
