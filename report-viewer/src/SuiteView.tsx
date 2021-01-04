import * as React from 'react';
import TestView from './TestView';
import SetupView from './SetupView';
import ResultTableView from './ResultTableView';
import {FocusProps} from './ResultRowView';
import {Filter, match_filter} from './FilterView';
import {get_time_from_iso8601, humanize_duration} from './utils';

interface SuiteProps extends FocusProps {
    suite: Suite,
    parent_suites: Array<Suite>,
    filter: Filter
}

function get_duration_from_time_interval(interval: TimeInterval) {
    if (interval.end_time) {
        return get_time_from_iso8601(interval.end_time) - get_time_from_iso8601(interval.start_time);
    } else {
        return 0;
    }
}

function get_suite_duration(suite: Suite) {
    let duration = suite.tests.map((t) => get_duration_from_time_interval(t)).reduce((x, y) => x + y);

    if (suite.suite_setup) {
        duration += get_duration_from_time_interval(suite.suite_setup);
    }

    if (suite.suite_teardown) {
        duration += get_duration_from_time_interval(suite.suite_teardown);
    }

    return duration;
}

function Heading(props: SuiteProps) {
    const suite = props.suite;
    const parent_suites = props.parent_suites;

    const suite_description = parent_suites.map((p) => p.description).concat(suite.description).join(" > ");
    const suite_id = parent_suites.map((p) => p.name).concat(suite.name).join(".");

    const properties = Object.keys(suite.properties).map((prop) => prop + ": " + suite.properties[prop]);
    const tags_and_properties = suite.tags.concat(properties).join(", ");

    return (
        <div>
            <span>
                <h4 className="multi-line-text">{suite_description}<br/><small>{suite_id}</small></h4>
            </span>
            <div>{tags_and_properties}</div>
            <div>
                {
                    /* eslint react/jsx-no-target-blank: "off" */
                    suite.links
                        .map(
                            (link, index) =>
                            <div key={index}>
                                <a href={link.url} title={link.name || link.url} target="_blank">{link.name || link.url}</a>
                            </div>
                        )
                        .reduce((accu, elem) => {
                            return accu.length === 0 ? [elem] : [...accu, <span>,</span>, elem]
                        }, Array.of<JSX.Element>())
                }
            </div>
        </div>
    );
}

function SuiteView(props: SuiteProps) {
    const filter = props.filter;
    const suite = props.suite;
    const parent_suites = props.parent_suites;
    const suite_id = parent_suites.map((p) => p.name).concat(suite.name).join(".");
    let results = [];

    if (suite.suite_setup && match_filter(filter, suite.suite_setup)) {
        results.push(
            <SetupView
                result={suite.suite_setup} description="- Setup suite -"
                id={suite_id + ".setup_suite"} key={suite_id + ".setup_suite"}
                focus={props.focus} onFocusChange={props.onFocusChange}/>
        );
    }

    for (let test of suite.tests) {
        if (match_filter(filter, test)) {
            let test_id = suite_id + "." + test.name;
            results.push(
                <TestView
                    test={test} test_id={test_id}
                    focus={props.focus} onFocusChange={props.onFocusChange}
                    key={test_id}/>
            );
        }
    }

    if (suite.suite_teardown && match_filter(filter, suite.suite_teardown)) {
        results.push(
            <SetupView
                result={suite.suite_teardown} description="- Teardown suite -"
                id={suite_id + ".teardown_suite"} key={suite_id + ".teardown_suite"}
                focus={props.focus} onFocusChange={props.onFocusChange}/>
        );
    }

    if (results.length > 0) {
        return (
            <ResultTableView
                heading={<Heading {...props}/>}
                extra_info={
                    <span className='extra-info visibility-slave'>
                        {humanize_duration(get_suite_duration(suite), true)}
                    </span>}>
                {results}
            </ResultTableView>
        );
    } else {
        return null;
    }
}

export default SuiteView;
