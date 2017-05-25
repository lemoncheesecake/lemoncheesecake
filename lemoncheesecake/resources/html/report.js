// borrowed from http://stackoverflow.com/questions/6234773/can-i-escape-html-special-chars-in-javascript
function escapeHtml(unsafe) {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}

function Step(step, nb) {
	this.step = step;
	this.nb = nb;
};

Step.prototype = {
	constructor: Step,
	
	render: function () {
		this.step_row = $("<tr style='display: none' class='step'>")
			.append($("<td>"))
				.append($("<td colspan='3'>")
					.append($("<h6>")
						.text(this.nb + ". " + this.step.description)));
		this.entry_rows = [ ];
		
		for (i in this.step.entries) {
			var entry = this.step.entries[i];
			$row = $("<tr style='display: none'>");
			this.entry_rows.push($row);
			if (entry.type == "check") {
				$row.addClass("check");
				$row.append($("<td>", {"class": entry.outcome ? 'text-success' : 'text-danger'}).text("CHECK"));
				$row.append($("<td>").text(entry.description));
				$row.append($("<td colspan='2'>").text(entry.details ? entry.details : ""));
			} else if (entry.type == "log") {
				$row.addClass("log");
				$row.append($("<td class='text-uppercase'>").text(entry.level));
				$row.append($("<td colspan='3'>").append($("<samp>").text(entry.message)));
				if (entry.level == "error") {
					$row.addClass("danger");
				}
			} else if (entry.type == "attachment") {
				$row.addClass("attachment");
				$row.append($("<td class='text-uppercase'>").text("ATTACHMENT"));
				$row.append($("<td colspan='3'>").append($("<a>", { "target": "_blank", "href": entry.filename }).text(entry.description)));
			} else if (entry.type == "url") {
				$row.addClass("url");
				$row.append($("<td class='text-uppercase'>").text("URL"));
				$row.append($("<td colspan='3'>").append($("<a>", { "target": "_blank", "href": entry.url }).text(entry.description)));
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

function Test(name, description, status, status_details, steps, tags, properties, links, parents) {
	this.name = name;
	this.description = description;
	this.status = status;
	this.status_details = status_details;
	this.steps = [];
	this.tags = (tags != null) ? tags : [];
	this.properties = (properties != null) ? properties : [];
	this.links = (links != null) ? links : [];
	for (var i = 0; i < steps.length; i++) {
		this.steps.push(new Step(steps[i], i+1));
	}
	this.parents = (parents != null) ? parents : [];
	this.is_displayed = false;
};

Test.prototype = {
	constructor: Test,
	
	render: function() {
		var cols = [ ];

		/* build status column */
		if (this.status == "passed") {
			status_text_class = "text-success";
		} else if (this.status == "failed") {
			status_text_class = "text-danger";
		} else {
			status_text_class = "text-warning";
		}
		$status_col = $("<td class='test_status'><span class='" + status_text_class + "' style='font-size:120%'>" + this.status.toUpperCase() + "</span></td>");
		cols.push($status_col);

		/* build description column */
		var path = this.parents.map(function(p) { return p.name }).concat(this.name).join(".");
		link_attrs = {"name": path, "href": "#" + path}
		if (this.outcome == false) {
			link_attrs["class"] = "text-danger";
		}
		$test_link = $("<a>", link_attrs).text(this.description).click(this.toggle.bind(this));
		var $test_desc = $("<h5>").append($test_link).append($("<br/><small>").text(path));
		cols.push($("<td>").append($test_desc));

		/* build tags & properties column */
		var $tags = $("<span>" + 
			$.map(this.tags, function(tag) {
				return escapeHtml(tag);
			}).concat(
			$.map(this.properties, function(value, key) {
				return escapeHtml(key + ": " + value);
			})).join("<br/>") +
			"</span>"
		);
		cols.push($("<td>").append($tags));
		
		/* build links column */
		var $links = $.map(this.links, function (link) {
			var label = link.name ? link.name : link.url;
			return "<a href='" + escapeHtml(link.url) + "' title='" + escapeHtml(label) + "'>" + escapeHtml(label) + "</a>";
		}).join(", ");
		cols.push($("<td>").append($links));

		/* build the whole line test with steps */
		$test_row = $("<tr>", { }).append(cols);
		rows = [ $test_row ];
		var step_rows = [ ];
		for (i in this.steps) {
			step_rows = step_rows.concat(this.steps[i].render());
		}
		rows = rows.concat(step_rows);
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

function TestSuite(data, parents) {
    this.parents = (parents == null) ? [] : parents;
    this.name = data.name;
    this.description = data.description;
    this.tags = data.tags;
    this.properties = data.properties;
    this.links = data.links;
    this.suite_setup = null;
    this.suite_teardown = null;
    this.tests = [ ];
    this.sub_suites = [ ];

    if (data.suite_setup) {
    	this.suite_setup = new Test("n/a", " - Setup suite -", data.suite_setup.outcome ? "passed" : "failed", null, data.suite_setup.steps);
    }

    if (data.suite_teardown) {
    	this.suite_teardown = new Test("n/a", " - Teardown suite -", data.suite_teardown.outcome ? "passed" : "failed", null, data.suite_teardown.steps)
    }

    for (var i = 0; i < data.tests.length; i++) {
        var t = data.tests[i]
    	this.tests.push(new Test(t.name, t.description, t.status, t.status_details, t.steps, t.tags, t.properties, t.links, this.parents.concat(this)));
    }

    for (var i = 0; i < data.sub_suites.length; i++) {
        this.sub_suites.push(new TestSuite(data.sub_suites[i], this.parents.concat(this)));
    }
}

TestSuite.prototype = {
	constructor: TestSuite,
	
	render: function() {
		var panels = [ ];

		if (this.tests.length > 0) {
			var description = this.parents.map(function(p) { return p.description }).concat(this.description).join(" > ");
			var path = this.parents.map(function(p) { return p.name }).concat(this.name).join(".");
			var $panel_heading = $("<div class='panel-heading'>");

			$panel_heading.append($("<h4>").text(description).append($("<br/><small>").text(path)));
			if (this.properties.length > 0 || this.tags.length > 0) {
				$panel_heading.append($("<br/>"));
				$panel_heading.append($("<span style='font-size: 75%'>Properties/Tags: ").text(
					this.tags.join(", ") + (this.tags.length > 0 ? ", " : "") +
					$.map(this.properties, function(value, key) {
						return key + ": " + value;
					}).join(", ")
				));
			}
			if (this.links.length > 0) {
				$panel_heading.append($("<br/>"));
				$panel_heading.append($("<span style='font-size: 75%'>links: " +
					$.map(this.links, function (link) {
						var label = link.name ? link.name : link.url;
						return "<a href='" + escapeHtml(link.url) + "' title='" + escapeHtml(label) + "'>" + escapeHtml(label) + "</a>";
				}).join(", ")));
			}
			var $panel = $("<div class='panel panel-default ' style='margin-left:" + (0 * this.parents.length) + "px'>")
				.append($panel_heading);
			panels.push($panel);

			var rows = [ ];
			if (this.suite_setup) {
				rows = rows.concat(this.suite_setup.render());
			}
			for (var i = 0; i < this.tests.length; i++) {
			    rows = rows.concat(this.tests[i].render());
			}
			if (this.suite_teardown) {
				rows = rows.concat(this.suite_teardown.render());
			}
			
			var $table = $("<table class='table table-hover table-bordered table-condensed'/>")
				.append($("<colgroup><col width='10%'><col width='60%'><col width='20%'><col width='10%'></colgroup>"))
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
	this.test_session_setup = null;
	this.test_session_teardown = null;
	
	if (data.test_session_setup) {
		this.test_session_setup = new Test("n/a", " - Setup test session -", data.test_session_setup.outcome ? "passed" : "failed", null, data.test_session_setup.steps);
	}
	if (data.test_session_teardown) {
		this.test_session_teardown = new Test("n/a", " - Teardown test session -", data.test_session_teardown.outcome ? "passed" : "failed", null, data.test_session_teardown.steps);
	}
	
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
				.append($("<td>").text(data[i][0]))
				.append($("<td>").text(data[i][1]));
			$table.append($row);
		}
		return $table;
	},
	
	render_hook_data: function(test, label) {
		var $panel_heading = $("<div class='panel-heading'><h4>" + label + "</h4></div>");
		var $panel = $("<div class='panel panel-default'>").append($panel_heading);
		rows = test.render();
		var $table = $("<table class='table table-hover table-bordered table-condensed'/>")
			.append($("<colgroup><col width='10%'><col width='60%'><col width='20%'><col width='10%'></colgroup>"))
			.append($("<tbody>").append(rows));
		$panel.append($table);
		return $panel;
	},
	
	render: function () {
		$("<h1>Information</h1>").appendTo(this.node);
		this.render_key_value_table(this.data.info).appendTo(this.node);
		
		$("<h1>Statistics</h1>").appendTo(this.node);
		this.render_key_value_table(this.data.stats).appendTo(this.node);
		
		$("<h1>Test results</h1>").appendTo(this.node);
		
		if (this.test_session_setup) {
			$panel = this.render_hook_data(this.test_session_setup, "- Setup test session -");
			$panel.appendTo(this.node);
		}
		
		for (var i = 0; i < this.suites.length; i++) {
			panels = this.suites[i].render();
			for (var j = 0; j < panels.length; j++) {
				$(panels[j]).appendTo(this.node);
			}
		}
		
		if (this.test_session_teardown) {
			$panel = this.render_hook_data(this.test_session_teardown, "- Teardown test session -");
			$panel.appendTo(this.node);
		}
	}	
};