
function* get_hierarchy(this: Suite) {
    if (this.parent_suite) {
        for (let node of this.parent_suite.get_hierachy()) {
            yield node;
        }
    }
    yield this;
}

function get_path(this: Suite) {
    return [...this.get_hierachy()].map((s) => s.name).join(".");
}

function upgrade_suites(suites: Array<Suite>, parent_suite?: Suite) {
    for (let suite of suites) {
        suite.parent_suite = parent_suite;
        suite.get_hierachy = get_hierarchy;
        suite.get_path = get_path;
        upgrade_suites(suite.suites, suite);
    }
}

export function upgrade_report(report: Report) {
    upgrade_suites(report.suites);
}