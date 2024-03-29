interface Props {
    attachment: Attachment
}

function AttachmentView(props: Props) {
    const attachment = props.attachment;
    let preview;

    if (attachment.as_image) {
        preview = <img src={attachment.filename} alt={attachment.description} title={attachment.description}/>;
    } else {
        preview = attachment.description;
    }

    return (
        <tr className="step_entry attachment table-active">
            <td className="text-uppercase text-info">ATTACHMENT</td>
            <td colSpan={3}>
                {/* eslint react/jsx-no-target-blank: "off" */}
                <a href={attachment.filename} target="_blank">{preview}</a>
            </td>
        </tr>
    )
}

export default AttachmentView;
