import * as React from 'react';

interface Props {
    url: UrlData,
    expanded: boolean
}

class Attachment extends React.Component<Props, {}> {
    render() {
        const url = this.props.url;

        return (
            <tr className="step_entry attachment" style={{display: this.props.expanded ? "" : "none"}}>
                <td className="text-uppercase text-info">URL</td>
                <td colSpan={3}>
                    <a href={url.url} target="_blank">{url.description}</a>
                </td>
            </tr>
        )
    }
}

export default Attachment;
