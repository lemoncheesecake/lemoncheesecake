import * as React from 'react';

export interface DisplayOptions {
    onlyFailures: boolean,
    showDebugLogs: boolean
}

interface OnOnlyFailuresChange {
    () : void
}

interface OnShowDebugLogsChange {
    () : void
}

interface Props {
    onlyFailures: boolean,
    onOnlyFailuresChange: OnOnlyFailuresChange,
    showDebugLogs: boolean,
    onShowDebugLogsChange: OnShowDebugLogsChange
}

export function is_result_to_be_displayed(result: Result, options: DisplayOptions) {
    return ! (options.onlyFailures && result.status !== "failed")
}

export function is_step_entry_to_be_displayed(entry: StepEntry, options: DisplayOptions) {
    return ! (entry.type === "log" && entry.level === "debug" && ! options.showDebugLogs);
}

export class DisplayOptionsView extends React.Component<Props, {}> {
    constructor(props: Props) {
        super(props);
        this.handleOnlyFailuresChange = this.handleOnlyFailuresChange.bind(this);
        this.handleShowDebugLogsChange = this.handleShowDebugLogsChange.bind(this);
    }

    handleOnlyFailuresChange(event: React.ChangeEvent<HTMLInputElement>) {
        this.props.onOnlyFailuresChange();
    }

    handleShowDebugLogsChange(event: React.ChangeEvent<HTMLInputElement>) {
        this.props.onShowDebugLogsChange();
    }
    
    render() {
        return (
            <span>
                <input type="checkbox" id="failures-only" checked={this.props.onlyFailures} onChange={this.handleOnlyFailuresChange}/>
                &nbsp;
                <label htmlFor="failures-only">Only show failures</label>
                &nbsp;|&nbsp;
                <input type="checkbox" id="show-debug-logs" checked={this.props.showDebugLogs} onChange={this.handleShowDebugLogsChange}/>
                &nbsp;
                <label htmlFor="show-debug-logs">Show debug logs</label>
                <br/>
            </span>
        );
    }
}
