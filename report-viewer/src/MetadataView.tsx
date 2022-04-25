function* resultToMetadata(result: TestTreeNode) : Generator<any> {
    let index = 0;

    for (let tag of result.tags) {
        yield <span key={index++}>{tag}</span>;
    }

    for (let prop of Object.keys(result.properties)) {
        yield <span key={index++}>{prop}: {result.properties[prop]}</span>;
    }

    for (let link of result.links) {
        /* eslint react/jsx-no-target-blank: "off" */
        yield <a href={link.url} title={link.url} target="_blank" key={index++}>
                {link.name || link.url}
              </a>;
    }
}

export function MetadataView(props: {result: TestTreeNode}) {
    return <>
        {
            [...resultToMetadata(props.result)].map((elem, index) => [index > 0 && ", ", elem])
        }
    </>;
}