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
		
	render_test_suite: function (suite) {
		var rows = [ ];
		for (i in suite.tests) {
		    test = suite.tests[i];
		    $row = this.render_test(test);
		    rows.push($row);
		}
		
		var $panel = $("<div class='panel panel-default panel-primary'>")
			.append("<div class='panel-heading'>Suite: " + suite.description + "</div>");
		var $panel_body = $("<div class='panel-body'>");
		$panel.append($panel_body);
		var $table = $("<table class='table table-hover table-bordered table-condensed'/>")
			.append($("<thead><tr><th>Test description</th><th>Outcome</th></tr></thead>"))
			.append($("<tbody>").append(rows));
		$panel_body.append($table);

		for (i in suite.sub_suites) {
			sub_suite = suite.sub_suites[i];
			$panel_body.append(this.render_test_suite(sub_suite));
		}
		
		return $panel;
	},
	
	render: function () {
		for (suite in this.data.suites) {
			$(this.render_test_suite(this.data.suites[suite])).appendTo(this.node);
		}
	}	
};