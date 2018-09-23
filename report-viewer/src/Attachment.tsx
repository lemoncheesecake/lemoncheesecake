import * as React from 'react';

interface Props {
    attachment: AttachmentData,
    expanded: boolean
}

class Attachment extends React.Component<Props, {}> {
    render() {
        const attachment = this.props.attachment;
        let attached_file;

        if (attachment.as_image) {
            attached_file = <a href={attachment.filename} target="_blank">{attachment.description}</a>
        } else {
            attached_file = <a href={attachment.filename} target="_blank"><img src={attachment.filename} title={attachment.description}/></a>
        }

        return (
            <tr className="step_entry attachment" style={{display: this.props.expanded ? "" : "none"}}>
                <td className="text-uppercase text-info">ATTACHMENT</td>
                <td colSpan={3}>
                    {attached_file}
                </td>
            </tr>
        )
    }
}

export default Attachment;
