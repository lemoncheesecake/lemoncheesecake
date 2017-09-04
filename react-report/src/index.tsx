import * as React from 'react';
import * as ReactDOM from 'react-dom';
import Report from './Report';
import registerServiceWorker from './registerServiceWorker';
import './index.css';

declare var reporting_data: ReportData;

window.addEventListener('load', () => {
    ReactDOM.render(
      <Report report={reporting_data} />,
      document.getElementById('root') as HTMLElement
    );
    registerServiceWorker();
});