function Step(step) {
	this.step = step;
};

Step.prototype = {
	constructor: Step,
	
	render: function () {
		this.step_row = $("<tr style='display: none' class='step'><td colspan='3'><u>" + this.step.description + "</u></td></tr>");
		this.entry_rows = [ ];
		
		for (i in this.step.entries) {
			var entry = this.step.entries[i];
			$row = $("<tr style='display: none'>");
			this.entry_rows.push($row);
			if (entry.type == "check") {
				$row.addClass("check");
				$row.append($("<td>" + entry.description + "</td>"));
				$row.append($("<td>" + (entry.details ? entry.details : "") + "</td>"));
				if (entry.outcome) {
					$row.append($("<td class='text-success'><strong>success</strong></td>"));
				} else {
					$row.append($("<td><strong>failure</strong></td>"));
					$row.addClass("danger");
				}
			} else if (entry.type == "log") {
				$row.addClass("log");
				$row.append($("<td colspan='2'><samp>" + entry.message + "</samp></td>"));
				$row.append($("<td class='text-uppercase'>" + entry.level + "</td>"));
				if (entry.level == "error") {
					$row.addClass("danger");
				}
			} else if (entry.type == "attachment") {
				$row.addClass("attachment");
				$row.append("<td colspan='3'>Attachment: <a target='_blank' href='" + entry.filename + "'>" + entry.description + "</a></td>")
			}
		}
		
		return [ this.step_row ].concat(this.entry_rows);
	},
	
	show: function() {
		this.step_row.show();
		for (var i = 0; i < this.entry_rows.length; i++) {
			this.entry_rows[i].show();
		}
	},
	
	hide: function() {
		this.step_row.hide();
		for (var i = 0; i < this.entry_rows.length; i++) {
			this.entry_rows[i].hide();
		}
	}
};

function Test(id, description, outcome, steps) {
	this.id = id;
	this.description = description;
	this.outcome = outcome;
	this.steps = [];
	for (var i = 0; i < steps.length; i++) {
		this.steps.push(new Step(steps[i]));
	}
	this.is_displayed = false;
};

Test.prototype = {
	constructor: Test,
	
	render: function() {
		var cols = [ ];
		var $test_desc = $("<a name='" + this.id + "' href='#" + this.id + "'>" + this.description + "</a>");
		cols.push($("<td>").append($test_desc));
		cols.push($("<td>" + this.id + "</td>"));
		var status;
		var status_class;
		if (this.outcome == true) {
			$status_col = $("<td class='text-success'><strong>success</strong></td>");
		} else if (this.outcome == false) {
			$status_col = $("<td><strong>failure</strong></td>");
			status_class = "danger";
		} else {
			$status_col = $("<td>n/a</td>");
		}
		cols.push($status_col);
		$test_row = $("<tr>", { "class": status_class }).append(cols);
		rows = [ $test_row ];
		var step_rows = [ ];
		for (i in this.steps) {
			step_rows = step_rows.concat(this.steps[i].render());
		}
		rows = rows.concat(step_rows);
		$test_desc.click(this.toggle.bind(this));
		return rows;
	},
	
	current_displayed_test: null,
	
	show: function() {
		if (Test.prototype.current_displayed_test) {
			Test.prototype.current_displayed_test.hide();
			Test.prototype.current_displayed_test = null;
		}
		
		for (var i = 0; i < this.steps.length; i++) {
			this.steps[i].show();
		}
		this.is_displayed = true;
		Test.prototype.current_displayed_test = this;
	},
	
	hide: function() {
		for (var i = 0; i < this.steps.length; i++) {
			this.steps[i].hide();
		}
		this.is_displayed = false;
	},
	
	toggle: function() {
		if (this.is_displayed) {
			this.hide();
		} else {
			this.show();
		}
	}
}

function TestSuite(data, parents=[]) {
    this.parents = parents;
    this.id = data.id;
    this.description = data.description;
    this.before_suite = null;
    this.after_suite = null;
    this.tests = [ ];
    this.sub_suites = [ ];

    if (data.before_suite) {
    	this.before_suite = new Test("n/a", " - Before suite -", "n/a", data.before_suite.steps);
    }

    if (data.after_suite) {
    	this.after_suite = new Test("n/a", " - After suite -", "n/a", data.after_suite.steps)
    }

    for (var i = 0; i < data.tests.length; i++) {
    	this.tests.push(new Test(data.tests[i].id, data.tests[i].description, data.tests[i].outcome, data.tests[i].steps));
    }

    for (var i = 0; i < data.sub_suites.length; i++) {
    	this.sub_suites.push(new TestSuite(data.sub_suites[i], parents.concat(this)));
    }
}

TestSuite.prototype = {
	constructor: TestSuite,
	
	render: function() {
		var panels = [ ]
		var description = this.parents.map(function(p) { return p.description }).concat(this.description).join(" > ");
		var $panel = $("<div class='panel panel-default panel-primary' style='margin-left:" + (20 * this.parents.length) + "px'>")
			.append("<div class='panel-heading'>Suite: " + description + "</div>");
		panels.push($panel);

		if (this.tests.length > 0) {
			var rows = [ ];
			if (this.before_suite) {
				rows = rows.concat(this.before_suite.render());
			}
			for (var i = 0; i < this.tests.length; i++) {
			    rows = rows.concat(this.tests[i].render());
			}
			if (this.after_suite) {
				rows = rows.concat(this.after_suite.render());
			}
			
			var $table = $("<table class='table table-hover table-bordered table-condensed'/>")
				.append($("<colgroup><col width='70%'><col width='20%'><col width='10%'></colgroup>"))
				.append($("<thead><tr><th>Test description</th><th>Test id</th><th>Outcome</th></tr></thead>"))
				.append($("<tbody>").append(rows));
			$panel.append($table);
		}
		
		for (var i = 0; i < this.sub_suites.length; i++) {
			panels = panels.concat(this.sub_suites[i].render());
		}
		
		return panels;
	}
};

function Report(data, node) {
	this.data = data;
	this.suites = [];
	this.node = node;
	
	for (var i = 0; i < data.suites.length; i++) {
		this.suites.push(new TestSuite(data.suites[i]));
	}
};

Report.prototype = {
	constructor: Report,
	
	render_key_value_table: function (data) {
		var $table = $("<table class='table table-hover table-bordered table-condensed'>");
		$table.append($("<colgroup><col width='30%'><col width='70%'></colgroup>"));
		for (var i = 0; i < data.length; i++) {
			$row = $("<tr>")
				.append("<td>" + data[i][0] + "</td>")
				.append("<td>" + data[i][1] + "</td>");
			$table.append($row);
		}
		return $table;
	},
	
	render: function () {
		$("<h1>Information</h1>").appendTo(this.node);
		this.render_key_value_table(this.data.info).appendTo(this.node);
		
		$("<h1>Statistics</h1>").appendTo(this.node);
		this.render_key_value_table(this.data.stats).appendTo(this.node);
		
		$("<h1>Test results</h1>").appendTo(this.node);
		for (var i = 0; i < this.suites.length; i++) {
			panels = this.suites[i].render();
			for (var j = 0; j < panels.length; j++) {
				$(panels[j]).appendTo(this.node);
			}
		}
	}	
};