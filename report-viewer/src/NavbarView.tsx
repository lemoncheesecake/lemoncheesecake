import * as React from 'react';

export interface DisplayOptions {
    onlyFailures: boolean,
    showDebugLogs: boolean,
    testFilter: string
}

interface OnDisplayOptionsChange {
    (options: DisplayOptions): void
}

interface Props {
    displayOptionsChange: OnDisplayOptionsChange
}

interface State {
    options: DisplayOptions,
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

export class NavbarView extends React.Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = {
            options: {onlyFailures: false, showDebugLogs: false, testFilter: ""},
            timeoutId: null
        };
    }

    updateOptions = (updated: object) => {
        this.setState({
            options: {...this.state.options, ...updated}
        }, () => this.props.displayOptionsChange(this.state.options));
    }

    handleOnlyFailuresChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        this.updateOptions({onlyFailures: ! this.state.options.onlyFailures});
    }

    handleShowDebugLogsChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        this.updateOptions({showDebugLogs: ! this.state.options.showDebugLogs});
    }

    handleTestFilterChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        if (this.state.timeoutId)
            clearTimeout(this.state.timeoutId);

        this.setState({
            options: {...this.state.options, testFilter: event.target.value},
            timeoutId: setTimeout(() => this.updateOptions({}), 500)
        });
    }

    handleTestFilterKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
        if (event.key === "Enter") {
            this.updateOptions({});
        }
    }

    handleReset = (event: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
        this.updateOptions({onlyFailures: false, showDebugLogs: false, testFilter: ""})
    }

    render = () => {
        return (
            <div className="navbar navbar-expand fixed-top navbar-dark bg-dark" id="navbar">
                <div className="container">
                    <div className="collapse navbar-collapse py-1">
                        <div className="d-flex">
                            <input type="text" id="text-filter" placeholder="Filter on test path &amp; description"
                                className="form-control me-sm-4"
                                size={40} autoFocus
                                value={this.state.options.testFilter}
                                onChange={this.handleTestFilterChange} onKeyDown={this.handleTestFilterKeyDown}/>
                        </div>
                        <div className="form-check form-check-inline">
                            <input type="checkbox" id="failures-only" className="form-check-input"
                                checked={this.state.options.onlyFailures} onChange={this.handleOnlyFailuresChange}/>
                            <label htmlFor="failures-only" className="form-check-label">Failed tests only</label>
                        </div>
                        <div className="form-check form-check-inline">
                            <input type="checkbox" id="show-debug-logs" className="form-check-input"
                                checked={this.state.options.showDebugLogs} onChange={this.handleShowDebugLogsChange}/>
                            <label htmlFor="show-debug-logs" className="form-check-label">Debug logs</label>
                        </div>
                        <div className="d-flex">
                            <button title="Reset all display options" type="submit"
                                className="btn btn-secondary my-2 my-sm-0 me-sm-4"
                                onClick={this.handleReset}>
                                Reset
                            </button>
                            <a href="report.js" download="report.js" className="btn btn-secondary my-2 my-sm-0"
                                title="Download raw report data">
                                <i className="bi bi-download"></i>
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        );
    }
}
