import * as React from 'react';

interface KeyValueTableProps {
    rows: Array<Array<String>>;
}

class KeyValueTable extends React.Component<KeyValueTableProps, {}> {
    render() {
        const rows = this.props.rows.map((row, index) =>
            <tr key={index}>
                <td>{row[0]}</td>
                <td>{row[1]}</td>
            </tr>
        );

        return (
            <table className="table table-hover table-bordered table-condensed">
                <colgroup>
                    <col style={{width: '30%'}}/>
                    <col style={{width: '70%'}}/>
                </colgroup>
                <tbody>{rows}</tbody>
            </table>
        );
    }
}

export default KeyValueTable;
