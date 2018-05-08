# lemoncheesecake report viewer

## Develop

- copy a `report.js` produced by a test run in the `public` sub-directory, it will be used as input data 
  by the lemoncheesecake report viewer
- you'll need `npm` on your machine
- run `npm install` to install the report viewer dependencies
- run `npm start` to start a server that serves the report viewer: your changes on the code 
  will be taken into account in real time

## Build and integrate the report viewer into lemoncheesecake Python project

The HTML reporting backend (`lemoncheesecake.reporting.backends.html`) expects a file `report.js` in the 
`lemoncheesecake.resources.html` package (where are also lying HTML wrapper files, CSS and external dependencies
such as bootstrap and jquery for offline / standalone HTML report). That built file is also commited along the source
files in order to avoid having a required dependency on a JS stack for a project that is mainly a Python project and to make 
all of these things totally transparent for a pure-Python contributor.

Then, the `build.py` script is in charge of:
- making a production build of the report viewer
- copy the generated JS file in the lemoncheesecake resources directory

To run it:
```
$ ./build.py
```
