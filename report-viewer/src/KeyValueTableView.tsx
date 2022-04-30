interface Props {
    title: String;
    rows: Array<Array<String>>;
}

function KeyValueTableView(props: Props) {
    if (props.rows.length === 0) {
        return null;
    }

    const rows = props.rows.map((row, index) =>
        <tr key={index}>
            <td>{row[0]}</td>
            <td>{row[1]}</td>
        </tr>
    );

    return (
        <div>
            <h2>{props.title}</h2>
            <table className="table table-hover table-bordered">
                <colgroup>
                    <col style={{width: '30%'}}/>
                    <col style={{width: '70%'}}/>
                </colgroup>
                <tbody>{rows}</tbody>
            </table>
        </div>
    );
}

export default KeyValueTableView;
