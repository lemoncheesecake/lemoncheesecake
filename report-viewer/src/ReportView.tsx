import * as React from 'react';
import {sprintf} from 'sprintf-js';
import KeyValueTableView from './KeyValueTableView';
import SuiteView from './SuiteView';
import { SetupProps, SetupView } from './SetupView';
import ResultTableView from './ResultTableView';
import { Focus } from './ResultRowView';
import TimeExtraInfoView from './TimeExtraInfoView';
import {DisplayOptionsView, DisplayOptions, is_result_to_be_displayed} from './DisplayOptionsView';
import { get_time_from_iso8601, humanize_datetime_from_iso8601, humanize_duration } from './utils';
import {upgrade_report} from './report-upgrader';

interface SessionSetupProps extends SetupProps {
    display_options: DisplayOptions
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
    if (is_result_to_be_displayed(props.result, props.display_options)) {
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
    options: DisplayOptions
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
        for (let result of report.get_all_results()) {
            if (result.end_time) {
                duration_cumulative += get_time_from_iso8601(result.end_time) - get_time_from_iso8601(result.start_time);
            }
        }
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

    for (let test of report.get_all_tests()) {
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
        <a href='http://lemoncheesecake.io' target="_blank" rel="noopener noreferrer">
            <span style={{float: 'right', paddingTop: '10px', paddingBottom: '10px', fontSize: '90%'}}>
                <img src=".html/logo.png" style={{display: "block", marginLeft: "auto", marginRight: "auto"}} alt=""/>
                <br/>
                Made by lemoncheesecake {props.version}
            </span>
        </a>
    );
}

class ReportView extends React.Component<ReportProps, ReportState> {
    constructor(props: ReportProps) {
        super(props);
        this.state = {
            focus: {id: "", scrollTo: false},
            options: {onlyFailures: false, showDebugLogs: false, testFilter: ""}
        };
        this.handleFocusChange = this.handleFocusChange.bind(this);
        this.handleOnlyFailuresChange = this.handleOnlyFailuresChange.bind(this);
        this.handleShowDebugLogsChange = this.handleShowDebugLogsChange.bind(this);
        this.handleTestFilterChange = this.handleTestFilterChange.bind(this);
        upgrade_report(props.report);
    }

    handleFocusChange(id: string) {
        this.setState({focus : {id, scrollTo: true}});
    }

    handleOnlyFailuresChange() {
        this.setState(
            {
                options: {
                    onlyFailures: ! this.state.options.onlyFailures,
                    showDebugLogs: this.state.options.showDebugLogs,
                    testFilter: this.state.options.testFilter
                },
                // ensure we don't trigger an undesired scroll:
                focus: {id: this.state.focus.id, scrollTo: false}
            }
        )
    }

    handleShowDebugLogsChange() {
        this.setState(
            {
                options: {
                    onlyFailures: this.state.options.onlyFailures,
                    showDebugLogs: ! this.state.options.showDebugLogs,
                    testFilter: this.state.options.testFilter
                },
                // ensure we don't trigger an undesired scroll:
                focus: {id: this.state.focus.id, scrollTo: false}
            }
        )
    }

    handleTestFilterChange(filter: string) {
        this.setState(
            {
                options: {
                    onlyFailures: this.state.options.onlyFailures,
                    showDebugLogs: this.state.options.showDebugLogs,
                    testFilter: filter
                },
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

                <DisplayOptionsView
                    onlyFailures={this.state.options.onlyFailures}
                    onOnlyFailuresChange={this.handleOnlyFailuresChange}
                    showDebugLogs={this.state.options.showDebugLogs}
                    onShowDebugLogsChange={this.handleShowDebugLogsChange}
                    testFilter=""
                    onTestFilterChange={this.handleTestFilterChange}
                    />

                <p style={{textAlign: 'right'}}><a href="report.js" download="report.js">Download raw report data</a></p>

                {
                    report.test_session_setup
                    && <SessionSetup
                            result={report.test_session_setup}
                            description="- Setup test session -" id="setup_test_session"
                            focus={this.state.focus} onFocusChange={this.handleFocusChange}
                            display_options={this.state.options}/>
                }
                {
                    [...[...report.get_all_suites()].entries()].map(([index, suite]) =>
                        <SuiteView
                            suite={suite}
                            focus={this.state.focus} onFocusChange={this.handleFocusChange}
                            display_options={this.state.options}
                            key={index}/>

                    )
                }

                {
                    report.test_session_teardown
                    && <SessionSetup
                            result={report.test_session_teardown}
                            description="- Teardown test session -" id="teardown_test_session"
                            focus={this.state.focus} onFocusChange={this.handleFocusChange}
                            display_options={this.state.options}/>
                }

                <MadeBy version={report.lemoncheesecake_version}/>
            </div>
        );
    }

    componentDidMount() {
        // set window title
        document.title = this.props.report.title;

        // focus on selected test (through URL anchor), if any
        let splitted_url = document.location.href.split('#');
        if (splitted_url.length === 2) {
            this.handleFocusChange(splitted_url[1]);
        // when the report contains only one test, focus on that test
        } else {
            let tests = [...this.props.report.get_all_tests()]
            if (tests.length === 1) {
                this.handleFocusChange(tests[0].get_path());
            }
        }
    }
}

export default ReportView;
