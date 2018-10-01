import * as React from 'react';
import KeyValueTable from './KeyValueTable';
import Suite from './Suite';
import { HookProps, Hook } from './Hook';
import ResultTable from './ResultTable';
import { get_result_row_by_id } from './ResultRow';
import TimeExtraInfo from './TimeExtraInfo';

class ReportHook extends React.Component<HookProps, {}> {
    render() {
        function Heading(props: {desc: string}) {
            return (
                <div>
                    <span>
                        <h4 className="special">{props.desc}</h4>
                    </span>
                </div>
            );
        }

        return (
            <ResultTable
                heading={<Heading desc={this.props.description}/>}
                extra_info={<TimeExtraInfo start={this.props.hook.start_time} end={this.props.hook.end_time}/>}>
                <Hook {...this.props}/>
            </ResultTable>
        );
    }
}

interface ReportProps {
    report: ReportData;
}

function walk_suites(suites: Array<SuiteData>, callback: (index: number, suite: SuiteData, parent_suites: Array<SuiteData>) => any) {
    let ret_values: Array<any> = [];
    let current_index = 0;

    function do_walk(suite: SuiteData, parent_suites: Array<SuiteData>): any {
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

class Report extends React.Component<ReportProps, {}> {
    render() {
        let report = this.props.report;

        return (
            <div>
                <h1>{report.title}</h1>

                <h2>Information</h2>
                <KeyValueTable rows={report.info}/>

                <h2>Statistics</h2>
                <KeyValueTable rows={report.stats}/>

                <p style={{textAlign: 'right'}}><a href="report.js" download="report.js">Download raw report data</a></p>

                {report.test_session_setup &&
                    <ReportHook hook={report.test_session_setup} description="- Setup test session -" id="setup_test_session"/>}

                {walk_suites(report.suites, ((index, suite, parent_suites) => <Suite suite={suite} parent_suites={parent_suites} key={index}/>))}

                {report.test_session_teardown &&
                    <ReportHook hook={report.test_session_teardown} description="- Teardown test session -" id="teardown_test_session"/>}
            </div>
        );
    }

    componentDidMount() {
        // set window title
        document.title = this.props.report.title;

        // focus on selected test, if any
        let splitted_url = document.location.href.split('#');
        if (splitted_url.length == 2) {
            const row = get_result_row_by_id(splitted_url[1]);
            if (row) {
                row.expand();
                row.scrollTo();
            }
        }
    }
}

export default Report;
