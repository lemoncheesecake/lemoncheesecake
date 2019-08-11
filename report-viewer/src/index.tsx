import * as React from 'react';
import * as ReactDOM from 'react-dom';
import ReportView from './ReportView';
import registerServiceWorker from './registerServiceWorker';
import './index.css';

declare var reporting_data: Report;

window.addEventListener('load', () => {
    ReactDOM.render(
      typeof reporting_data !== "undefined" ? <ReportView report={reporting_data} /> : <h1>No report data is yet available.</h1>,
      document.getElementById('root') as HTMLElement
    );
    registerServiceWorker();
});

// IE11 does not provide Array.of
// Create a polyfill as indicated in
// https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/of#Polyfill
if (!Array.of) {
  Array.of = function() {
      return Array.prototype.slice.call(arguments);
  };
}