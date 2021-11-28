import * as React from 'react';

export interface DisplayOptions {
    onlyFailures: boolean,
    showDebugLogs: boolean,
    testFilter: string
}

interface OnOnlyFailuresChange {
    () : void
}

interface OnShowDebugLogsChange {
    () : void
}

interface OnTestFilterChange {
    (value: string) : void
}

interface Props extends DisplayOptions {
    onOnlyFailuresChange: OnOnlyFailuresChange,
    onShowDebugLogsChange: OnShowDebugLogsChange,
    onTestFilterChange: OnTestFilterChange
}

interface State {
    testFilter: string,
    timeoutId: any | null
}

export function is_result_to_be_displayed(result: Result | Test, options: DisplayOptions) {
    if (options.onlyFailures && result.status !== "failed")
        return false;

    if (options.testFilter) {
        if ("get_path" in (result as any)) {
            var keywords = options.testFilter
                .split(" ")
                .map(value => value.trim().toLowerCase())
                .filter(value => value.length > 0);
            var normalized_path = (result as Test).get_path().toLowerCase();
            var normalized_description = (result as Test).description.toLowerCase();
            return keywords.every(keyword => normalized_path.includes(keyword))
                || keywords.every(keyword => normalized_description.includes(keyword));
        } else {
            return false;
        }
    }

    return true;
}

export function is_step_entry_to_be_displayed(entry: StepEntry, options: DisplayOptions) {
    return ! (entry.type === "log" && entry.level === "debug" && ! options.showDebugLogs);
}

export class DisplayOptionsView extends React.Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = {testFilter: props.testFilter, timeoutId: null};
        this.handleOnlyFailuresChange = this.handleOnlyFailuresChange.bind(this);
        this.handleShowDebugLogsChange = this.handleShowDebugLogsChange.bind(this);
        this.handleTestFilterChange = this.handleTestFilterChange.bind(this);
        this.handleTestFilterKeyDown = this.handleTestFilterKeyDown.bind(this);
    }

    handleOnlyFailuresChange(event: React.ChangeEvent<HTMLInputElement>) {
        this.props.onOnlyFailuresChange();
    }

    handleShowDebugLogsChange(event: React.ChangeEvent<HTMLInputElement>) {
        this.props.onShowDebugLogsChange();
    }

    handleTestFilterChange(event: React.ChangeEvent<HTMLInputElement>) {
        if (this.state.timeoutId)
            clearTimeout(this.state.timeoutId);
        this.setState({testFilter: event.target.value});
        this.setState({
            timeoutId: setTimeout(() => this.props.onTestFilterChange(this.state.testFilter), 500)
        });
    }

    handleTestFilterKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
        if (event.key === "Enter") {
            this.props.onTestFilterChange(this.state.testFilter);
        }
    }
    
    render() {
        return (
            <span>
                <input type="checkbox" id="failures-only" checked={this.props.onlyFailures} onChange={this.handleOnlyFailuresChange}/>
                &nbsp;
                <label htmlFor="failures-only">Failed tests only</label>

                &nbsp;|&nbsp;

                <input type="checkbox" id="show-debug-logs" checked={this.props.showDebugLogs} onChange={this.handleShowDebugLogsChange}/>
                &nbsp;
                <label htmlFor="show-debug-logs">Debug logs</label>

                &nbsp;|&nbsp;

                <input type="text" id="text-filter" placeholder="Filter on test path &amp; description"
                    size={40} autoFocus
                    value={this.state.testFilter} onChange={this.handleTestFilterChange} onKeyDown={this.handleTestFilterKeyDown}/>
            </span>
        );
    }
}
