interface Props {
    attachment: Attachment,
    expanded: boolean
}

function AttachmentView(props: Props) {
    const attachment = props.attachment;
    let preview;

    if (attachment.as_image) {
        preview = <img src={attachment.filename} alt={attachment.description}/>;
    } else {
        preview = attachment.description;
    }

    return (
        <tr className="step_entry attachment" style={{display: props.expanded ? "" : "none"}}>
            <td className="text-uppercase text-info">ATTACHMENT</td>
            <td colSpan={3}>
                {/* eslint react/jsx-no-target-blank: "off" */}
                <a href={attachment.filename} target="_blank">{preview}</a>
            </td>
        </tr>
    )
}

export default AttachmentView;
