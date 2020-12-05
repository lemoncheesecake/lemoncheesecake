type LogLevel = string;

declare interface Log {
    type: "log",
    message: string,
    level: LogLevel,
    time: string
}

declare interface Check {
    type: "check",
    description: string,
    is_successful: Boolean,
    details: string | null
}

declare interface Attachment {
    type: "attachment",
    filename: string,
    description: string,
    as_image: boolean
}

declare interface Url {
    type: "url",
    url: string,
    description: string,
}

type StepEntry = Log | Check | Attachment | Url;

declare interface TimeInterval {
    start_time: string,
    end_time: string | null,
}

declare interface Step extends TimeInterval {
    description: string,
    entries: Array<StepEntry>;
}

declare interface Result extends TimeInterval {
    steps: Array<Step>,
    status: string | null,
    status_details: string | null
}

type Status = string;

declare interface Link {
    name: string,
    url: string
}

declare interface Metadata {
    name: string,
    description: string,
    tags: Array<string>,
    properties: { [key: string]: string },
    links: Array<Link>
}

declare interface Test extends Result, Metadata {
}

declare interface Suite extends Metadata {
    tests: Array<Test>,
    suites: Array<Suite>,
    suite_setup: Result | undefined,
    suite_teardown: Result | undefined
}

declare interface Report {
    title: string,
    start_time: string,
    end_time: string,
    generation_time: string,
    nb_threads: number,
    info: Array<Array<string>>,
    test_session_setup: Result,
    test_session_teardown: Result,
    suites: Array<Suite>
}