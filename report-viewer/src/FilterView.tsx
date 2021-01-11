import * as React from 'react';

export interface Filter {
    onlyFailures: boolean
}

interface OnFilterChange {
    () : void
}

interface Props {
    onlyFailures: boolean,
    onOnlyFailuresChange: OnFilterChange
}

export function match_filter(filter: Filter, result: Result) {
    if (filter.onlyFailures && result.status !== "failed")
        return false;
    return true;
}

export class FilterView extends React.Component<Props, {}> {
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
