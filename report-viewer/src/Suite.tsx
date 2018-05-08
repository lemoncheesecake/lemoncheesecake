import * as React from 'react';
import Test from './Test';
import Hook from './Hook';
import ResultTable from './ResultTable';
import TimeExtraInfo from './TimeExtraInfo';

interface SuiteProps {
    suite: SuiteData,
    parent_suites: Array<SuiteData>
}

class Suite extends React.Component<SuiteProps, {}> {
    render() {
        const suite = this.props.suite;
        const parent_suites = this.props.parent_suites;

        const suite_description = parent_suites.map((p) => p.description).concat(suite.description).join(" > ");
        const suite_id = parent_suites.map((p) => p.name).concat(suite.name).join(".");

        let start_time: DateTime | null = null;
        let end_time: DateTime | null = null;
        if (suite.tests.length > 0) {
            start_time = suite.tests[0].start_time;
            end_time = suite.tests[suite.tests.length-1].end_time;
        }

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
            <ResultTable heading={<Heading/>} extra_info={start_time && <TimeExtraInfo start={start_time} end={end_time}/>}>
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
