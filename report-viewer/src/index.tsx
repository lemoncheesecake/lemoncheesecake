import * as ReactDOM from 'react-dom';
import ReportView from './ReportView';
import registerServiceWorker from './registerServiceWorker';
import "bootswatch/dist/slate/bootstrap.min.css";
import './custom.scss';

declare var reporting_data: Report;

window.addEventListener('load', () => {
    ReactDOM.render(
      typeof reporting_data !== "undefined" ? <ReportView report={reporting_data} /> : <h1>No report data is yet available.</h1>,
      document.getElementById('root') as HTMLElement
    );
    registerServiceWorker();
});
