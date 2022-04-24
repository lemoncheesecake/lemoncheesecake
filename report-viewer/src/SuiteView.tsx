import * as React from 'react';
import TestView from './TestView';
import SetupView from './SetupView';
import ResultTableView from './ResultTableView';
import {FocusProps} from './ResultRowView';
import {DisplayOptions, is_result_to_be_displayed} from './NavbarView';
import {get_time_from_iso8601, humanize_duration} from './utils';

interface SuiteProps extends FocusProps {
    suite: Suite,
    display_options: DisplayOptions
}

function get_duration_from_time_interval(interval: TimeInterval) {
    if (interval.end_time) {
        return get_time_from_iso8601(interval.end_time) - get_time_from_iso8601(interval.start_time);
    } else {
        return 0;
    }
}

function get_suite_duration(suite: Suite) {
    let duration = suite.tests.map((t) => get_duration_from_time_interval(t)).reduce((x, y) => x + y, 0);

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

    const suite_description = [...suite.get_hierachy()].map((s) => s.description).join(" > ");
    const suite_id = [...suite.get_hierachy()].map((s) => s.name).join(".");

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
                                <a href={link.url} title={link.url} target="_blank">{link.name || link.url}</a>
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
    const display_options = props.display_options;
    const suite = props.suite;
    let results = [];

    if (suite.suite_setup && is_result_to_be_displayed(suite.suite_setup, display_options)) {
        results.push(
            <SetupView
                result={suite.suite_setup} description="- Setup suite -"
                id={suite.get_path() + ".setup_suite"} key={suite.get_path() + ".setup_suite"}
                focus={props.focus} onFocusChange={props.onFocusChange}
                display_options={display_options}/>
        );
    }

    for (let test of suite.tests) {
        if (is_result_to_be_displayed(test, display_options)) {
            let test_id = suite.get_path() + "." + test.name;
            results.push(
                <TestView
                    test={test} test_id={test_id}
                    focus={props.focus} onFocusChange={props.onFocusChange}
                    key={test_id}
                    display_options={display_options}/>
            );
        }
    }

    if (suite.suite_teardown && is_result_to_be_displayed(suite.suite_teardown, display_options)) {
        results.push(
            <SetupView
                result={suite.suite_teardown} description="- Teardown suite -"
                id={suite.get_path() + ".teardown_suite"} key={suite.get_path() + ".teardown_suite"}
                focus={props.focus} onFocusChange={props.onFocusChange}
                display_options={display_options}/>
        );
    }

    if (results.length > 0) {
        return (
            <ResultTableView
                heading={<Heading {...props}/>}
                extra_info={
                    <span className='extra-info time-extra-info visibility-slave'>
                        <i className="bi bi-clock-history"/> {humanize_duration(get_suite_duration(suite), true)}
                    </span>}>
                {results}
            </ResultTableView>
        );
    } else {
        return null;
    }
}

export default SuiteView;
