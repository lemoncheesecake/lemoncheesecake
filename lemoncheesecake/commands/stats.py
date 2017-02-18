'''
Created on Feb 14, 2017

@author: nicolas
'''

from lemoncheesecake.cli import Command
from lemoncheesecake.commands.cliutils import bold, print_table
from lemoncheesecake.testsuite import add_filter_args_to_cli_parser, get_filter_from_cli_args, walk_testsuites
from lemoncheesecake.project import find_project_file, Project
from lemoncheesecake.exceptions import ProjectError, ProgrammingError

class StatsCommand(Command):
    def get_name(self):
        return "stats"
    
    def get_description(self):
        return "Display statistics about the project's tests"
    
    def add_cli_args(self, cli_parser):
        add_filter_args_to_cli_parser(cli_parser)

    def run_cmd(self, cli_args):
        project_file = find_project_file()
        if not project_file:
            return "Cannot find project file"
        try:
            project = Project(project_file)
            suites = project.load_testsuites()
        except (ProjectError, ProgrammingError) as e:
            return str(e)
        
        filter = get_filter_from_cli_args(cli_args)
        
        for suite in suites:
            suite.apply_filter(filter)

        class Stats:
            def __init__(self):
                self.nb = 0
                self.tags = {}
                self.properties = {}
                self.links = {}
        test_stats = Stats()
        suite_stats = Stats()
        
        def handle_obj(stats):
            def wrapped(obj):
                stats.nb += 1
                for tag in obj.tags:
                    stats.tags[tag] = stats.tags.get(tag, 0) + 1
                for prop, value in obj.properties.items():
                    if prop not in stats.properties:
                        stats.properties[prop] = {}
                    if value not in stats.properties[prop]:
                        stats.properties[prop][value] = 0
                    stats.properties[prop][value] += 1
                for link in obj.links:
                    stats.links[link] = stats.links.get(link, 0) + 1
            return wrapped
        
        walk_testsuites(suites, testsuite_func=handle_obj(suite_stats), test_func=handle_obj(test_stats))
        
        # Show tags
        lines = []
        for tag in sorted(set(test_stats.tags.keys() + suite_stats.tags.keys())):
            lines.append([bold(tag), test_stats.tags.get(tag, 0), suite_stats.tags.get(tag, 0)])
        print_table(bold("Tags"), ["Tag", "Used in tests", "Used in testsuites"], lines)

        # Show properties
        lines = []
        for prop_name in sorted(set(test_stats.properties.keys() + suite_stats.properties.keys())):
            prop_values = sorted(set(
                test_stats.properties.get(prop_name, {}).keys() + suite_stats.properties.get(prop_name, {}).keys()
            ))
            for prop_value in prop_values:
                lines.append([
                    bold(prop_name), bold(prop_value),
                    test_stats.properties.get(prop_name, {}).get(prop_value, 0),
                    suite_stats.properties.get(prop_name, {}).get(prop_value, 0)
                ])
        print_table(bold("Properties"), ["Property", "Value", "Used in tests", "Used in testsuites"], lines)

        # Show links
        lines = []
        for link in sorted(set(test_stats.links.keys() + suite_stats.links.keys()), key=lambda l: l[0]):
            lines.append([
                bold(link[1]) or "-", link[0], test_stats.links.get(link, 0), suite_stats.links.get(link, 0)
            ])
        print_table(bold("Links"), ["Name", "URL", "Used in tests", "Used in testsuites"], lines)

        print "Total %s: %s" % (bold("testsuites"), suite_stats.nb)
        print "Total %s: %s" % (bold("tests"), test_stats.nb)
        print
        