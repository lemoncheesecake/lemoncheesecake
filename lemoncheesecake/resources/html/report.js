// borrowed from http://stackoverflow.com/questions/6234773/can-i-escape-html-special-chars-in-javascript
function escapeHtml(unsafe) {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}

function humanize_duration(duration) {
    return (duration / 1000) + "s";
}

function get_duration_between_datetimes(dt1, dt2) {
    duration = new Date(dt2).getTime() - new Date(dt1).getTime();
    return humanize_duration(duration);
}

function get_time_from_datetime(dt) {
    return dt.split(" ")[1];
}

function make_time_extra_info(start_datetime, end_datetime) {
    if (! start_datetime)
        return $();
    start_time = get_time_from_datetime(start_datetime);
    duration = get_duration_between_datetimes(start_datetime, end_datetime);
    return $("<span class='extra_info'>" + start_time + "	&rarr; " + duration + "</span>");
}

function Step(step, nb) {
	this.step = step;
	this.nb = nb;
};

Step.prototype = {
	constructor: Step,
	
	render: function () {
		this.step_row = $("<tr style='display: none' class='step'>").
			append($("<td colspan='4'>").
				append($("<h6>").
						append($("<strong style='font-size:120%'>").text(this.nb + ". " + this.step.description)).
						append($("<span class='extra_info' style='float: right;'>").append(make_time_extra_info(this.step.start_time, this.step.end_time)))
				));
		this.entry_rows = [ ];
		
		for (i in this.step.entries) {
			var entry = this.step.entries[i];
			$row = $("<tr style='display: none'>");
			this.entry_rows.push($row);
			if (entry.type == "check") {
				$row.addClass("step_entry check");
				$row.append($("<td>", {"class": entry.outcome ? 'text-success' : 'text-danger'}).text("CHECK"));
				$row.append($("<td>").text(entry.description));
				$row.append($("<td colspan='2'>").text(entry.details ? entry.details : ""));
			} else if (entry.type == "log") {
				$row.addClass("step_entry log");
				if (entry.level == "error") {
					log_level_class = "text-danger";
				} else if (entry.level == "warn") {
					log_level_class = "text-warning";
				} else {
					log_level_class = "text-info";
				}
				log_time = get_time_from_datetime(entry.time);
				$row.append($("<td class='text-uppercase " + log_level_class + "'>").text(entry.level));
				$row.append($("<td colspan='3'>").
				    append($("<samp>").text(entry.message)).
				    append($("<span class='extra_info' style='float: right;'>" + log_time + "</span>")));
			} else if (entry.type == "attachment") {
				$row.addClass("step_entry attachment");
				$row.append($("<td class='text-uppercase text-info'>").text("ATTACHMENT"));
				$row.append($("<td colspan='3'>").append($("<a>", { "target": "_blank", "href": entry.filename }).text(entry.description)));
			} else if (entry.type == "url") {
				$row.addClass("step_entry url");
				$row.append($("<td class='text-uppercase text-info'>").text("URL"));
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

function Test(data, parents, special) {
	this.data = data;
	this.steps = [];
	for (var i = 0; i < data.steps.length; i++) {
		this.steps.push(new Step(data.steps[i], i+1));
	}
	this.parents = (parents != null) ? parents : [];
	this.special = special;
	this.is_displayed = false;

	Test.prototype.all_tests[this.get_path()] = this;
};

Test.prototype = {
	constructor: Test,

	get_path: function() {
	    return this.parents.map(function(p) { return p.data.name }).concat(this.data.name).join(".");
	},

	render: function() {
		var cols = [ ];

		/* build status column */
		if (this.data.status == "passed") {
			status_text_class = "text-success";
		} else if (this.data.status == "failed") {
			status_text_class = "text-danger";
		} else if (this.data.status == null) {
			status_text_class = "";
		} else if (this.data.status == "disabled") {
            status_text_class = "text-default";
		} else {
			status_text_class = "text-warning";
		}
		$status_col = $("<td class='test_status' title='" + (this.data.status_details ? escapeHtml(this.data.status_details) : "") + "'>" + 
				"<span class='" + status_text_class + "' style='font-size:120%'>" + (this.data.status ? this.data.status.toUpperCase() : "n/a") + "</span></td>");
		if (this.steps.length > 0) {
			$status_col.css("cursor", "pointer");
			$status_col.click(this.toggle.bind(this));
		}
		cols.push($status_col);

		/* build description column */
		var test_path = this.get_path();
		var $test_col_content = $("<h5>").text(this.data.description).
		    append("&nbsp;").
		    append($("<a href='#" + test_path + "' class='glyphicon glyphicon-link extra_info anchorlink' style='font-size: 90%'>")).
		    append($("<br/>")).
		    append($("<small>").text(test_path));
		if (this.special) {
			$test_col_content.addClass("special")
		}
		cols.push($("<td class='flex-container'>").append($test_col_content).
		    append(make_time_extra_info(this.data.start_time, this.data.end_time)));

		/* build tags & properties column */
		var $tags = $("<span>" + 
			$.map(this.data.tags, function(tag) {
				return escapeHtml(tag);
			}).concat(
			$.map(this.data.properties, function(value, key) {
				return escapeHtml(key + ": " + value);
			})).join("<br/>") +
			"</span>"
		);
		cols.push($("<td>").append($tags));
		
		/* build links column */
		var $links = $.map(this.data.links, function (link) {
			var label = link.name ? link.name : link.url;
			return "<a href='" + escapeHtml(link.url) + "' title='" + escapeHtml(label) + "' target='_blank'>" + escapeHtml(label) + "</a>";
		}).join(", ");
		cols.push($("<td>").append($links));

		/* build the whole line test with steps */
		$test_row = $("<tr>", { "id": test_path, "class": "test" }).append(cols);
		rows = [ $test_row ];
		var step_rows = [ ];
		for (i in this.steps) {
			step_rows = step_rows.concat(this.steps[i].render());
		}
		rows = rows.concat(step_rows);
		return rows;
	},
	
	current_displayed_test: null,
	all_tests: {},
	
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
	this.data = data;
    this.parents = (parents == null) ? [] : parents;
    this.tests = [ ];
    this.suites = [ ];

    if (data.suite_setup) {
    	test_data = Object();
    	test_data.name = "n/a";
    	test_data.description = " - Setup suite -";
    	test_data.status = data.suite_setup.outcome ? "passed" : "failed";
    	test_data.status_details = null;
    	test_data.steps = data.suite_setup.steps;
    	this.suite_setup = new Test(test_data, [], true);
    }

    if (data.suite_teardown) {
    	test_data = Object();
    	test_data.name = "n/a";
    	test_data.description = " - Teardown suite -";
    	test_data.status = data.suite_teardown.outcome ? "passed" : "failed";
    	test_data.status_details = null;
    	test_data.steps = data.suite_teardown.steps;
    	this.suite_teardown = new Test(test_data, [], true);
    }

    for (var i = 0; i < data.tests.length; i++) {
    	this.tests.push(new Test(data.tests[i], this.parents.concat(this)));
    }

    for (var i = 0; i < data.suites.length; i++) {
        this.suites.push(new TestSuite(data.suites[i], this.parents.concat(this)));
    }
}

TestSuite.prototype = {
	constructor: TestSuite,

	render: function() {
		var panels = [ ];

		if (this.tests.length > 0) {
			var description = this.parents.map(function(p) { return p.data.description }).concat(this.data.description).join(" > ");
			var path = this.parents.map(function(p) { return p.data.name }).concat(this.data.name).join(".");
			var $panel_heading = $("<div class='panel-heading flex-container'>");

            if (this.tests.length > 0) {
                suite_start_time = this.data.tests[0].start_time;
                suite_end_time = this.data.tests[this.data.tests.length-1].end_time;
            } else {
                suite_start_time = null;
                suite_end_time = null;
            }
			$panel_heading.append($("<span>").
			    append($("<h4>").text(description).append($("<br/><small>").text(path)))).
			    append(make_time_extra_info(suite_start_time, suite_end_time));
			if (this.data.properties.length > 0 || this.data.tags.length > 0) {
				$panel_heading.append($("<br/>"));
				$panel_heading.append($("<span style='font-size: 75%'>Properties/Tags: ").text(
					this.data.tags.join(", ") + (this.data.tags.length > 0 ? ", " : "") +
					$.map(this.data.properties, function(value, key) {
						return key + ": " + value;
					}).join(", ")
				));
			}
			if (this.data.links.length > 0) {
				$panel_heading.append($("<br/>"));
				$panel_heading.append($("<span style='font-size: 75%'>links: " +
					$.map(this.data.links, function (link) {
						var label = link.name ? link.name : link.url;
						return "<a href='" + escapeHtml(link.url) + "' title='" + escapeHtml(label) + "' target='_blank'>" + escapeHtml(label) + "</a>";
				}).join(", ")));
			}
			var $panel = $("<div class='panel panel-default ' style='margin-left:" + (0 * this.parents.length) + "px'>")
				.append($panel_heading);
			panels.push($panel);

			var rows = [ ];
			if (this.data.suite_setup) {
				rows = rows.concat(this.suite_setup.render());
			}
			for (var i = 0; i < this.tests.length; i++) {
			    rows = rows.concat(this.tests[i].render());
			}
			if (this.data.suite_teardown) {
				rows = rows.concat(this.suite_teardown.render());
			}
			
			var $table = $("<table class='table table-hover table-bordered table-condensed'/>")
				.append($("<colgroup><col width='10%'><col width='60%'><col width='20%'><col width='10%'></colgroup>"))
				.append($("<tbody>").append(rows));
			$panel.append($table);
		}
		
		for (var i = 0; i < this.suites.length; i++) {
			panels = panels.concat(this.suites[i].render());
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
		test_data = Object();
		test_data.name = "n/a";
		test_data.description = " - Setup test session -";
		test_data.status = data.test_session_setup.outcome ? "passed" : "failed";
		test_data.status_details = null;
		test_data.steps = data.test_session_setup.steps;
		this.test_session_setup = new Test(test_data, null, true);
	}
	if (data.test_session_teardown) {
		test_data = Object();
		test_data.name = "n/a";
		test_data.description = " - Teardown test session -";
		test_data.status = data.test_session_teardown.outcome ? "passed" : "failed";
		test_data.status_detail = null;
		test_data.steps = steps;
		this.test_session_teardown = new Test(test_data, null, true);
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
		var $panel_heading = $("<div class='panel-heading'><h4 class='special'>" + label + "</h4></div>");
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

window.onload = function() {
        splitted = document.location.href.split('#');
        if (splitted.length == 2) {
            test = Test.prototype.all_tests[splitted[1]];
            test.show()
        }
}
