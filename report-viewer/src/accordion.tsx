import { useState, useEffect } from 'react';

export function useAccordionHandler(propagateOpeningChange: (opened: boolean) => void,
                                    forcedOpened: boolean) : [boolean, () => void] {
    // forcedOpened means that one sibling accordion has been double-clicked and
    // that all siblings must opened or closed accordingly
    const [opened, setOpened] = useState(true);
    const [lastClick, setLastClick] = useState(0);

    useEffect(() => {
        setOpened(forcedOpened);
    }, [forcedOpened]);

    // this handler handle both single and double click
    return [
        opened,
        () => {
            const now = Date.now();
            // handle the simple click or the first click of the double click
            if (now - lastClick > 300) {
                setOpened(!opened);
            // handle the second click of a double click
            } else {
                propagateOpeningChange(opened);
            }
            setLastClick(now);
        }
    ];
}

export function AccordionOpeningIndicator(props: {opened: boolean}) {
    if (props.opened) {
        return  (
            <span className="glyphicon glyphicon-resize-full visibility-slave" title="Collapse">
            </span>
        );
    } else {
        return  (
            <span className="glyphicon glyphicon-resize-small visibility-slave" title="Expand">
            </span>
        );
    }
}
