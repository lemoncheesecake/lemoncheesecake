import * as React from 'react';

export interface DisplayOptions {
    onlyFailures: boolean
}

interface OnOnlyFailuresChange {
    () : void
}

interface Props {
    onlyFailures: boolean,
    onOnlyFailuresChange: OnOnlyFailuresChange
}

export function is_result_to_be_displayed(options: DisplayOptions, result: Result) {
    if (options.onlyFailures && result.status !== "failed")
        return false;
    return true;
}

export class DisplayOptionsView extends React.Component<Props, {}> {
    constructor(props: Props) {
        super(props);
        this.handleChange = this.handleChange.bind(this);
    }

    handleChange(event: React.ChangeEvent<HTMLInputElement>) {
        this.props.onOnlyFailuresChange();
    }
    
    render() {
        return (
            <span>
                <input type="checkbox" id="failures-only" checked={this.props.onlyFailures} onChange={this.handleChange}/>
                &nbsp;
                <label htmlFor="failures-only">Only show failures</label>
            </span>
        );
    }
}
