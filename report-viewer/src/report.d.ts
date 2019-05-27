type LogLevel = string;

declare interface LogData {
    type: "log",
    message: string,
    level: LogLevel,
    time: string
}

declare interface CheckData {
    type: "check",
    description: string,
    is_successful: Boolean,
    details: string | null
}

declare interface AttachmentData {
    type: "attachment",
    filename: string,
    description: string,
    as_image: boolean
}

declare interface UrlData {
    type: "url",
    url: string,
    description: string,
}

type StepEntryData = LogData | CheckData | AttachmentData | UrlData;

declare interface TimeInterval {
    start_time: string,
    end_time: string | null,
}

declare interface StepData extends TimeInterval {
    description: string,
    entries: Array<StepEntryData>;
}

declare interface HookData extends TimeInterval {
    status: string | null,
    steps: Array<StepData>
}

type Status = string;

declare interface Link {
    name: string,
    url: string
}

declare interface BaseTestData {
    name: string,
    description: string,
    tags: Array<string>,
    properties: Array<object>,
    links: Array<Link>
}

declare interface TestData extends BaseTestData, TimeInterval {
    steps: Array<StepData>,
    status: Status | null,
    status_details: string | null
}

declare interface SuiteData extends BaseTestData {
    tests: Array<TestData>,
    suites: Array<SuiteData>,
    suite_setup: HookData | undefined,
    suite_teardown: HookData | undefined
}

declare interface ReportData {
    title: string,
    start_time: string,
    end_time: string,
    generation_time: string,
    nb_threads: number,
    info: Array<Array<string>>,
    test_session_setup: HookData,
    test_session_teardown: HookData,
    suites: Array<SuiteData>
}