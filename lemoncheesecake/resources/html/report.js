function Report(data, node) {
	this.data = data;
	this.node = node;
};

Report.prototype = {
	constructor: Report,
	
	render_test: function(test) {
		var cols = [ ];
		cols.push($("<td>" + test.description + "</td>"));
		var status;
		var status_class;
		if (test.outcome == true) {
			status = "success";
			status_class = "success";
		} else if (test.outcome == false) {
			status = "failure";
			status_class = "danger";
		} else {
			status = "n/a";
		}
		cols.push($("<td>" + status + "</td>"));
		return $("<tr>", { "class": status_class }).append(cols)
	},
		
	render_test_suite: function (suite, parents=[]) {
		var panels = [ ]
		var description = parents.map(function(p) { return p.description }).concat(suite.description).join(" > ");
		var $panel = $("<div class='panel panel-default panel-primary' style='margin-left:" + (20 * parents.length) + "px'>")
			.append("<div class='panel-heading'>Suite: " + description + "</div>");
		panels.push($panel);

		if (suite.tests.length > 0) {
			var rows = [ ];
			for (i in suite.tests) {
			    test = suite.tests[i];
			    $row = this.render_test(test);
			    rows.push($row);
			}
			
			var $table = $("<table class='table table-hover table-bordered table-condensed'/>")
				.append($("<thead><tr><th>Test description</th><th>Outcome</th></tr></thead>"))
				.append($("<tbody>").append(rows));
			$panel.append($table);
		}
		
		for (i in suite.sub_suites) {
			sub_suite = suite.sub_suites[i];
			extra_panels = this.render_test_suite(sub_suite, parents.concat([ suite ]))
			panels = panels.concat(extra_panels);
		}
		
		return panels;
	},
	
	render: function () {
		for (suite in this.data.suites) {
			panels = this.render_test_suite(this.data.suites[suite]);
			for (i in panels) {
				$(panels[i]).appendTo(this.node);
			}
		}
	}	
};