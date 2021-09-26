function* flatten_suites(suites: Array<Suite>): Generator<Suite> {
    for (let suite of suites) {
        yield suite;
        yield * flatten_suites(suite.suites);
    }
}

function* flatten_tests(suites: Array<Suite>): Generator<Test> {
    for (let suite of flatten_suites(suites)) {
        for (let test of suite.tests) {
            yield test;
        }
    }
}

function* flatten_results(suites: Array<Suite>) : Generator<Result> {
    for (let suite of flatten_suites(suites)) {
        if (suite.suite_setup) {
            yield suite.suite_setup;
        }
        for (let test of suite.tests) {
            yield test;
        }
        if (suite.suite_teardown) {
            yield suite.suite_teardown;
        }
    }
}

function upgrade_test(test: Test, parent_suite: Suite) {
    test.parent_suite = parent_suite;
    test.get_path = function(this: Test) {
        return this.parent_suite?.get_path() + "." + this.name;
    };
}

function upgrade_suites(suites: Array<Suite>, parent_suite?: Suite) {
    for (let suite of suites) {
        suite.parent_suite = parent_suite;

        suite.get_hierachy = function*() {
            if (suite.parent_suite) {
                for (let node of suite.parent_suite.get_hierachy()) {
                    yield node;
                }
            }
            yield this;
        };

        suite.get_path = function() {
            return [...suite.get_hierachy()].map((s) => s.name).join(".");
        };

        for (let test of suite.tests) {
            upgrade_test(test, suite);
        }

        upgrade_suites(suite.suites, suite);
    }
}

export function upgrade_report(report: Report) {
    upgrade_suites(report.suites);

    report.get_all_suites = function(this: Report) {
        return flatten_suites(this.suites);
    };

    report.get_all_results = function*(this: Report) {
        if (report.test_session_setup) {
            yield report.test_session_setup;
        }
        for (let result of flatten_results(report.suites)) {
            yield result;
        }
        if (report.test_session_teardown) {
            yield report.test_session_teardown;
        }
    };

    report.get_all_tests = function*(this: Report) {
        yield * flatten_tests(report.suites);
    }
}