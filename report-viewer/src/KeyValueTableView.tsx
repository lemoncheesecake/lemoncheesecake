import * as React from 'react';

interface KeyValueTableProps {
    title: String;
    rows: Array<Array<String>>;
}

class KeyValueTableView extends React.Component<KeyValueTableProps, {}> {
    render() {
        if (this.props.rows.length === 0) {
            return (null);
        }

        const rows = this.props.rows.map((row, index) =>
            <tr key={index}>
                <td>{row[0]}</td>
                <td>{row[1]}</td>
            </tr>
        );

        return (
            <div>
                <h2>{this.props.title}</h2>
                <table className="table table-hover table-bordered table-condensed">
                    <colgroup>
                        <col style={{width: '30%'}}/>
                        <col style={{width: '70%'}}/>
                    </colgroup>
                    <tbody>{rows}</tbody>
                </table>
            </div>
        );
    }
}

export default KeyValueTableView;
