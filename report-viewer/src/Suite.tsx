import * as React from 'react';
import Test from './Test';
import Hook from './Hook';
import ResultTable from './ResultTable';
import {get_timestamp_from_datetime, humanize_duration} from './utils';

interface SuiteProps {
    suite: SuiteData,
    parent_suites: Array<SuiteData>
}

function get_duration_from_time_interval(interval: TimeInterval) {
    if (interval.end_time) {
        return get_timestamp_from_datetime(interval.end_time) - get_timestamp_from_datetime(interval.start_time);
    } else {
        return 0;
    }
}

function get_suite_duration(suite: SuiteData) {
    let duration = suite.tests.map((t) => get_duration_from_time_interval(t)).reduce((x, y) => x + y);

    if (suite.suite_setup) {
        duration += get_duration_from_time_interval(suite.suite_setup);
    }

    if (suite.suite_teardown) {
        duration += get_duration_from_time_interval(suite.suite_teardown);
    }

    return duration;
}

class Suite extends React.Component<SuiteProps, {}> {
    render() {
        const suite = this.props.suite;
        const parent_suites = this.props.parent_suites;

        const suite_description = parent_suites.map((p) => p.description).concat(suite.description).join(" > ");
        const suite_id = parent_suites.map((p) => p.name).concat(suite.name).join(".");

        const props = Object.keys(suite.properties).map((prop) => prop + ": " + suite.properties[prop]);
        const tags_and_properties = suite.tags.concat(props).join(", ");

        function Heading(props: {} = {}) {
            return (
                <div>
                    <span>
                        <h4>{suite_description}<br/><small>{suite_id}</small></h4>
                    </span>
                    <div>{tags_and_properties}</div>
                    <div>
                        {
                            suite.links.
                                map((link, index) => <div key={index}><a href={link.url} title={link.name || link.url} target="_blank">{link.name || link.url}</a></div>).
                                reduce((accu, elem) => {
                                    return accu.length == 0 ? [elem] : [...accu, ',', elem]
                                }, [])
                        }
                    </div>
                </div>
            );
        }

        let tests = [];
        for (let test of suite.tests) {
            let test_id = suite_id + "." + test.name;
            tests.push(<Test test={test} test_id={test_id} key={test_id}/>);
        }

        return (
            <ResultTable
                heading={<Heading/>}
                extra_info={<span className='extra-info'>{humanize_duration(get_suite_duration(suite))}</span>}>
                {
                    suite.suite_setup && <Hook hook={suite.suite_setup} description="- Setup suite -" id={suite_id + ".setup_suite"}/>
                }
                { tests }
                {
                    suite.suite_teardown && <Hook hook={suite.suite_teardown} description="- Teardown suite -" id={suite_id + ".teardown_suite"}/>
                }
            </ResultTable>
        );
    }
}

export default Suite;
