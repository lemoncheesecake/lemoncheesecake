function Report(data, node) {
	this.data = data;
	this.node = node;
};

Report.prototype = {
	constructor: Report,
	
	render_step: function(step) {
		var rows = [ ];
		$step = $("<tr style='display: none' class='step'><td colspan='3'><u>" + step.description + "</u></td></tr>");
		rows.push($step);
		for (i in step.entries) {
			var entry = step.entries[i];
			$row = $("<tr style='display: none'>");
			rows.push($row);
			if (entry.type == "check") {
				$row.addClass("check");
				$row.append($("<td>" + entry.description + "</td>"));
				$row.append($("<td>" + (entry.details ? entry.details : "") + "</td>"));
				if (entry.outcome) {
					$row.append($("<td class='text-success'><strong>success</strong></td>"));
				} else {
					$row.append($("<td><strong>success</strong></td>"));
					$row.addClass("danger");
				}
			} else if (entry.type == "log") {
				$row.addClass("log");
				$row.append($("<td colspan='2'>" + entry.message + "</td>"));
				$row.append($("<td class='text-uppercase'>" + entry.level + "</td>"));
				if (entry.level == "error") {
					$row.addClass("danger");
				}
			}
		}
		return rows;
	},
	
	render_test: function(test) {
		var cols = [ ];
		var $test_desc = $("<a href='#'>" + test.description + "</a>");
		cols.push($("<td>").append($test_desc));
		cols.push($("<td>" + test.id + "</td>"));
		var status;
		var status_class;
		if (test.outcome == true) {
			$status_col = $("<td class='text-success'><strong>success</strong></td>");
		} else if (test.outcome == false) {
			$status_col = $("<td><strong>failure</strong></td>");
			status_class = "danger";
		} else {
			$status_col = $("<td>n/a</td>");
		}
		cols.push($status_col);
		$test_row = $("<tr>", { "class": status_class }).append(cols);
		rows = [ $test_row ];
		var step_rows = [ ];
		for (i in test.steps) {
			step_rows = step_rows.concat(this.render_step(test.steps[i]));
		}
		rows = rows.concat(step_rows);
		$test_desc.click(function() {
			for (i in step_rows) {
				$row = step_rows[i];
				if ($row.css("display") == "none") {
					$row.css("display", "");
				} else {
					$row.css("display", "none");
				}
			}
		});
		return rows;
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
			    test_rows = this.render_test(test);
			    rows = rows.concat(test_rows);
			}
			
			var $table = $("<table class='table table-hover table-bordered table-condensed'/>")
				.append($("<colgroup><col width='70%'><col width='20%'><col width='10%'></colgroup>"))
				.append($("<thead><tr><th>Test description</th><th>Test id</th><th>Outcome</th></tr></thead>"))
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