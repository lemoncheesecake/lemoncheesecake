import * as React from 'react';
import {sprintf} from 'sprintf-js';
import KeyValueTableView from './KeyValueTableView';
import SuiteView from './SuiteView';
import { SetupProps, SetupView } from './SetupView';
import ResultTableView from './ResultTableView';
import { Focus } from './ResultRowView';
import TimeExtraInfoView from './TimeExtraInfoView';
import {FilterView, Filter, match_filter} from './FilterView';
import { get_time_from_iso8601, humanize_datetime_from_iso8601, humanize_duration } from './utils';

interface SessionSetupProps extends SetupProps {
    filter: Filter
}

function SessionSetupHeading(props: {desc: string}) {
    return (
        <div>
            <span>
                <h4 className="special">{props.desc}</h4>
            </span>
        </div>
    );
}

function SessionSetup(props: SessionSetupProps) {
    if (match_filter(props.filter, props.result)) {
        return (
            <ResultTableView
                heading={<SessionSetupHeading desc={props.description}/>}
                extra_info={<TimeExtraInfoView start={props.result.start_time} end={props.result.end_time}/>}>
                <SetupView {...props}/>
            </ResultTableView>
        );
    } else {
        return null;
    }
}

interface ReportProps {
    report: Report
}

interface ReportState {
    focus: Focus,
    filter: Filter
}

function walk_suites(suites: Array<Suite>, callback: (index: number, suite: Suite, parent_suites: Array<Suite>) => any) {
    let ret_values: Array<any> = [];
    let current_index = 0;

    function do_walk(suite: Suite, parent_suites: Array<Suite>): any {
        if (suite.tests.length > 0) {
            const ret_value = callback(current_index++, suite, parent_suites);
            ret_values.push(ret_value);
        }
        for (let sub_suite of suite.suites) {
            do_walk(sub_suite, parent_suites.concat(suite));
        }
    }

    for (let suite of suites) {
        do_walk(suite, []);
    }

    return ret_values;
}

function walk_tests(suites: Array<Suite>, callback: (index: number, suite: Test, parent_suites: Array<Suite>) => any) {
    let ret_values: Array<any> = [];
    let current_index = 0;

    walk_suites(
        suites,
        (suite_index: number, suite: Suite, parent_suites: Array<Suite>) => {
            for (let test of suite.tests) {
                const ret_value = callback(current_index++, test, Array.of(suite).concat(parent_suites));
                ret_values.push(ret_value);
            }
        }
    );

    return ret_values;
}

function walk_results(report: Report, callback: (result: Test | Result) => any) {
    let ret_values: Array<any> = [];

    if (report.test_session_setup) {
        ret_values.push(callback(report.test_session_setup));
    }

    walk_suites(
        report.suites,
        (suite_index: number, suite: Suite, parent_suites: Array<Suite>) => {
            if (suite.suite_setup) {
                ret_values.push(callback(suite.suite_setup));
            }
            for (let test of suite.tests) {
                ret_values.push(callback(test));
            }
            if (suite.suite_teardown) {
                ret_values.push(callback(suite.suite_teardown));
            }
        }
    );

    if (report.test_session_teardown) {
        ret_values.push(callback(report.test_session_teardown));
    }
}

function build_report_stats(report: Report): Array<Array<string>> {
    let stats: Array<Array<string>> = [];

    ////
    // Start time
    ////
    stats.push(Array.of("Start time", humanize_datetime_from_iso8601(report.start_time)));

    ////
    // Duration
    ////
    let duration = null;
    if (report.end_time) {
        stats.push(Array.of("End time", humanize_datetime_from_iso8601(report.end_time)));
        duration = get_time_from_iso8601(report.end_time) - get_time_from_iso8601(report.start_time);
        stats.push(Array.of("Duration", humanize_duration(duration)));
    } else {
        stats.push(Array.of("End time", "n/a"));
        stats.push(Array.of("Duration", "n/a"));
    }

    /////
    // Cumulative duration
    ////
    if (report.nb_threads > 1) {
        let duration_cumulative = 0;
        walk_results(report, (result: Test | Result) => {
            if (result.end_time) {
                duration_cumulative += get_time_from_iso8601(result.end_time) - get_time_from_iso8601(result.start_time);
            }
        });
        let duration_cumulative_description = humanize_duration(duration_cumulative);
        if (duration) {
            duration_cumulative_description += sprintf(" (parallelization speedup factor is %.1f)", duration_cumulative / duration);
        }
        stats.push(Array.of("Cumulative duration", duration_cumulative_description));
    }

    ////
    // Tests by status
    ////
    let tests_nb = 0;
    let successful_tests_nb = 0;
    let failed_tests_nb = 0;
    let skipped_tests_nb = 0;
    let disabled_tests_nb = 0;

    walk_tests(
        report.suites,
        (index: number, test: Test, suites: Array<Suite>) => {
            tests_nb++;
            switch (test.status) {
                case 'passed':
                    successful_tests_nb++;
                    break;
                case 'failed':
                    failed_tests_nb++;
                    break;
                case 'skipped':
                    skipped_tests_nb++;
                    break;
                case 'disabled':
                    disabled_tests_nb++;
                    break;
            }
        }
    );

    stats.push(Array.of("Tests", tests_nb.toString()));

    stats.push(Array.of("Successful tests", successful_tests_nb.toString()));

    let enabled_tests = successful_tests_nb + failed_tests_nb + skipped_tests_nb;
    let successful_tests_pct = enabled_tests ? (successful_tests_nb / enabled_tests * 100) : 0;
    stats.push(Array.of("Successful tests in %", sprintf("%d%%", successful_tests_pct)));

    stats.push(Array.of("Failed tests", failed_tests_nb.toString()));

    stats.push(Array.of("Skipped tests", skipped_tests_nb.toString()));

    stats.push(Array.of("Disabled tests", disabled_tests_nb.toString()));

    return stats;
}

function MadeBy(props: {version: string}) {
    return (
        <span style={{float: 'right', paddingBottom: '10px', fontSize: '90%'}}>
            Made by&nbsp;
            <a href='http://lemoncheesecake.io' target="_blank" rel="noopener noreferrer">
                lemoncheesecake {props.version}
            </a>
        </span>
    );
}

class ReportView extends React.Component<ReportProps, ReportState> {
    constructor(props: ReportProps) {
        super(props);
        this.state = {
            focus: {id: "", scrollTo: false},
            filter: {onlyFailures: false}
        };
        this.handleFocusChange = this.handleFocusChange.bind(this);
        this.handleOnlyFailuresChange = this.handleOnlyFailuresChange.bind(this);
    }

    handleFocusChange(id: string, scrollTo: boolean = false) {
        this.setState({focus : {id, scrollTo}});
    }

    handleOnlyFailuresChange() {
        this.setState(
            {
                filter: {onlyFailures: ! this.state.filter.onlyFailures},
                // ensure we don't trigger an undesired scroll:
                focus: {id: this.state.focus.id, scrollTo: false}
            }
        )
    }

    render() {
        let report = this.props.report;

        return (
            <div>
                <h1>{report.title}</h1>

                <KeyValueTableView title="Information" rows={report.info}/>

                <KeyValueTableView title="Statistics" rows={build_report_stats(report)}/>

                <FilterView onlyFailures={this.state.filter.onlyFailures} onOnlyFailuresChange={this.handleOnlyFailuresChange}/>

                <p style={{textAlign: 'right'}}><a href="report.js" download="report.js">Download raw report data</a></p>

                {
                    report.test_session_setup
                    && <SessionSetup
                            result={report.test_session_setup}
                            description="- Setup test session -" id="setup_test_session"
                            focus={this.state.focus} onFocusChange={this.handleFocusChange}
                            filter={this.state.filter}/>
                }
                {
                    walk_suites(
                        report.suites,
                        ((index, suite, parent_suites) => 
                            <SuiteView
                                suite={suite} parent_suites={parent_suites}
                                focus={this.state.focus} onFocusChange={this.handleFocusChange}
                                filter={this.state.filter}
                                key={index}/>
                        )
                    )
                }

                {
                    report.test_session_teardown
                    && <SessionSetup
                            result={report.test_session_teardown}
                            description="- Teardown test session -" id="teardown_test_session"
                            focus={this.state.focus} onFocusChange={this.handleFocusChange}
                            filter={this.state.filter}/>
                }

                <MadeBy version={report.lemoncheesecake_version}/>
            </div>
        );
    }

    componentDidMount() {
        // set window title
        document.title = this.props.report.title;

        // focus on selected test, if any
        let splitted_url = document.location.href.split('#');
        if (splitted_url.length === 2)
            this.handleFocusChange(splitted_url[1], true);
    }
}

export default ReportView;
