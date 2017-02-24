from functools import partial
import os
import subprocess
import html

import sublime
import sublime_plugin

from .anaconda_lib.helpers import get_settings
from .anaconda_lib.tooltips import Tooltip

class Pref:
    @staticmethod
    def load():
        settings = sublime.load_settings('pman.sublime-settings')
        Pref.show_debug = settings.get('show_debug', False)
        Pref.pman_executable_path = settings.get('pman_executable_path', 'pman')
        Pref.pman_col_executable_path = settings.get('pman_col_executable_path', 'col')


st_version = 2
if sublime.version() == '' or int(sublime.version()) > 3000:
    st_version = 3

if st_version == 2:
    Pref.load()

def plugin_loaded():
    Pref.load()


def debug_message(msg):
    """Debug functionality"""
    if Pref.show_debug is True:
        print("[pman] " + msg)


class PmanCommand():
    """Class to represent the wrapper around pman command line application"""
    def __init__(self, entity):
        self.entity = entity

    def execute(self):
        colCmd = [Pref.pman_col_executable_path]
        colCmd.append('-b')

        if os.name == 'nt':
            pmanCmd = ['man', '-M', Pref.pman_executable_path, self.entity]
            pman = subprocess.Popen(pmanCmd, stdout=subprocess.PIPE, shell=True)
            col = subprocess.Popen(colCmd, stdout=subprocess.PIPE, stdin=pman.stdout, shell=True)
        else:
            pmanCmd = [Pref.pman_executable_path]
            pmanCmd.append(self.entity)

            debug_message(' '.join(pmanCmd))
            debug_message(' '.join(colCmd))
            pman = subprocess.Popen(pmanCmd, stdout=subprocess.PIPE)
            col = subprocess.Popen(colCmd, stdout=subprocess.PIPE, stdin=pman.stdout)

        data = col.communicate()[0]

        return data

class BasePman(sublime_plugin.TextCommand):
    """Base class for pman functionality"""
    def execute(self, keyword):
        data = PmanCommand(keyword).execute()

        try:
            data = data.decode('utf-8')
        except UnicodeDecodeError:
            data = output.decode(sublime.active_window().active_view().settings().get('fallback_encoding'))

        if data == '':
            sublime.error_message('There is no manual entry for "' + keyword + '"')
        else:
            self.render(keyword, data)

    def render(self, keyword, output):
        self.print_popup(output)

        # output_view = sublime.active_window().get_output_panel("pman")
        # output_view.set_read_only(False)
        # output_view.run_command('output_helper', {'text': output})

        # output_view.sel().clear()
        # output_view.sel().add(sublime.Region(0))
        # output_view.set_read_only(True)
        # sublime.active_window().run_command("show_panel", {"panel": "output.pman"})

    def print_doc(self, edit: sublime.Edit) -> None:
        """Print the documentation string into a Sublime Text panel
        """

        doc_panel = self.view.window().create_output_panel(
            'anaconda_documentation'
        )

        doc_panel.set_read_only(False)
        region = sublime.Region(0, doc_panel.size())
        doc_panel.erase(edit, region)
        doc_panel.insert(edit, 0, self.documentation)
        self.documentation = None
        doc_panel.set_read_only(True)
        doc_panel.show(0)
        self.view.window().run_command(
            'show_panel', {'panel': 'output.anaconda_documentation'}
        )

    def print_popup(self, edit) -> None:
        """Show message in a popup
        """
        dlines = str.splitlines(html.escape(edit, False))
        # name = dlines[5].strip()
        docstring = '<br>'.join(dlines[5:(len(dlines) - 2)])
        content = {'content': docstring}
        self.documentation = None
        css = get_settings(self.view, 'anaconda_tooltip_theme', 'popup')
        Tooltip(css).show_tooltip(
            self.view, 'signature', content, partial(self.print_doc, edit))


class PmanManualForKeywordCommand(BasePman):
    """Command to take entered input and run through pman"""
    def run(self, args):
        sublime.active_window().show_input_panel('Keyword', '', self.execute, None, None)


class PmanManualForSelectionCommand(BasePman):
    """Command to take the selection and run through pman"""
    def run(self, args):
        for region in self.view.sel():
            word = self.view.word(region)
            if not word.empty():
                keyword = self.view.substr(word)
                self.execute(keyword)


class OutputHelper(sublime_plugin.TextCommand):
    """Help render the data to the screen for ST3"""
    def run(self, edit, text = None):
        if text:
            self.view.insert(edit, self.view.size(), text)

        return
