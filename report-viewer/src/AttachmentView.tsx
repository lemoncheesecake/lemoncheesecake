import * as React from 'react';

interface Props {
    attachment: Attachment,
    expanded: boolean
}

class AttachmentView extends React.Component<Props, {}> {
    render() {
        const attachment = this.props.attachment;
        let preview;

        if (attachment.as_image) {
            preview = <img src={attachment.filename} title={attachment.description}/>;
        } else {
            preview = attachment.description;
        }

        return (
            <tr className="step_entry attachment" style={{display: this.props.expanded ? "" : "none"}}>
                <td className="text-uppercase text-info">ATTACHMENT</td>
                <td colSpan={3}>
                    <a href={attachment.filename} target="_blank">{preview}</a>
                </td>
            </tr>
        )
    }
}

export default AttachmentView;
