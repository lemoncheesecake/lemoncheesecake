import * as React from 'react';

interface Props {
    url: Url,
    expanded: boolean
}

function UrlView(props: Props) {
    return (
        <tr className="step_entry attachment" style={{display: props.expanded ? "" : "none"}}>
            <td className="text-uppercase text-info">URL</td>
            <td colSpan={3}>
                <a href={props.url.url} target="_blank" rel="noopener noreferrer">
                    {props.url.description}
                </a>
            </td>
        </tr>
    )
}

export default UrlView;
