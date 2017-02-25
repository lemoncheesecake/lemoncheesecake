'''
Created on Feb 14, 2017

@author: nicolas
'''

from __future__ import print_function

from lemoncheesecake.cli import Command
from lemoncheesecake.commands.cliutils import print_table
from lemoncheesecake.testsuite import add_filter_args_to_cli_parser, get_filter_from_cli_args, filter_testsuites, walk_testsuites
from lemoncheesecake.project import find_project_file, Project
from lemoncheesecake.exceptions import ProjectError, ProgrammingError

class StatsCommand(Command):
    def get_name(self):
        return "stats"
    
    def get_description(self):
        return "Display statistics about the project's tests"
    
    def add_cli_args(self, cli_parser):
        self.add_color_cli_args(cli_parser)
        add_filter_args_to_cli_parser(cli_parser)

    def run_cmd(self, cli_args):
        self.process_color_cli_args(cli_args)
        
        project_file = find_project_file()
        if not project_file:
            return "Cannot find project file"
        try:
            project = Project(project_file)
            suites = project.load_testsuites()
        except (ProjectError, ProgrammingError) as e:
            return str(e)
        
        filter = get_filter_from_cli_args(cli_args)
        suites = filter_testsuites(suites, filter)
        
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
        for tag in sorted(set(list(test_stats.tags.keys()) + list(suite_stats.tags.keys()))):
            lines.append([self.bold(tag), test_stats.tags.get(tag, 0), suite_stats.tags.get(tag, 0)])
        print_table(self.bold("Tags"), ["Tag", "Used in tests", "Used in testsuites"], lines)

        # Show properties
        lines = []
        for prop_name in sorted(set(list(test_stats.properties.keys()) + list(suite_stats.properties.keys()))):
            prop_values = sorted(set(
                list(test_stats.properties.get(prop_name, {}).keys()) + list(suite_stats.properties.get(prop_name, {}).keys())
            ))
            for prop_value in prop_values:
                lines.append([
                    self.bold(prop_name), self.bold(prop_value),
                    test_stats.properties.get(prop_name, {}).get(prop_value, 0),
                    suite_stats.properties.get(prop_name, {}).get(prop_value, 0)
                ])
        print_table(self.bold("Properties"), ["Property", "Value", "Used in tests", "Used in testsuites"], lines)

        # Show links
        lines = []
        for link in sorted(set(list(test_stats.links.keys()) + list(suite_stats.links.keys())), key=lambda l: l[0]):
            lines.append([
                self.bold(link[1] or "-"), link[0], test_stats.links.get(link, 0), suite_stats.links.get(link, 0)
            ])
        print_table(self.bold("Links"), ["Name", "URL", "Used in tests", "Used in testsuites"], lines)

        print("Total %s: %s" % (self.bold("testsuites"), suite_stats.nb))
        print("Total %s: %s" % (self.bold("tests"), test_stats.nb))
        print()
        
        return 0