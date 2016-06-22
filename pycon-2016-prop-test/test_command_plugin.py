# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from contextlib import contextmanager
from io import StringIO
import os
import re
import shutil
import sys
import tempfile

from hypothesis import assume, settings, strategies as st
from hypothesis.stateful import rule, RuleBasedStateMachine
import requests

# from unittest.mock import patch
# FIXME: Change to a patch
from nikola import utils
utils.ask_yesno = lambda x: True

PLUGIN_URL = 'http://localhost:9999/v7/plugins.json'

def plugin_name_generator():
    r = requests.get(PLUGIN_URL).json()
    return st.sampled_from(r)


class SimplifiedPluginModel(object):

    def __init__(self, plugins=None):
        self.installed = set() if plugins is None else set(plugins)
        self.disabled = set()

    def install(self, value):
        self.installed.add(value)

    def remove(self, value):
        self._safe_remove(self.installed, value)
        self._safe_remove(self.disabled, value)

    def _safe_remove(self, set_, value):
        if value in set_:
            set_.remove(value)


class PluginStateMachine(RuleBasedStateMachine):
    def __init__(self):
        super(PluginStateMachine, self).__init__()
        self._create_demo_site()
        self._init_site_object()
        pre_installed = self._get_installed()
        self.model = SimplifiedPluginModel(pre_installed)

    def teardown(self):
        os.chdir('..')
        shutil.rmtree('demo')

    def _init_site_object(self):
        from nikola import nikola
        import conf
        self._site = nikola.Nikola(**conf.__dict__)
        self._site.init_plugins()

    def _create_demo_site(self):
        from nikola.plugins.command.init import CommandInit
        command_init = CommandInit()
        command_init.execute(options={'demo': True, 'quiet': True}, args=['demo'])
        os.chdir('demo')
        sys.path.insert(0, '')

    @contextmanager
    def _captured_output(self):
        old_stdout = sys.stdout
        stdout = StringIO()
        try:
            sys.stdout = stdout
            yield stdout

        finally:
            sys.stdout = old_stdout

    def _run_command(self, args=[]):
        from nikola.__main__ import main
        with self._captured_output() as out:
            main(['plugin', '-u', PLUGIN_URL] + args)
            out.seek(0)
            return out.read()

    def _get_installed(self):
        output = self._run_command(['--list-installed'])
        self._installed = set(re.findall('(.*)\s+at\s+.*', output))
        return self._installed

    def _install(self, name):
        self._run_command(['-i', name])
        self.model.install(name)
        self._get_installed()

    def _remove(self, name):
        self._run_command(['-r', name])
        self.model.remove(name)
        self._get_installed()

    @rule(name=plugin_name_generator())
    def install(self, name):
        self._install(name)
        assert name in self._installed
        self.assert_model_state_matches()

    @rule(name=plugin_name_generator())
    # FIXME: Use a precondition here instead of assume?
    def remove(self, name):
        assume(name in self.model.installed)
        self._remove(name)
        assert name not in self._installed
        self.assert_model_state_matches()

    def assert_model_state_matches(self):
        # NOTE: Can't check equality, since some plugins install other plugins.
        # There is no way to find out the dependency before hand.
        assert self._installed.issuperset(self.model.installed)

    # @rule(name=st.text())
    # def disable(self, name):
    #     pass

    # @rule(name=st.text())
    # def enable(self, name):
    #     pass

class PluginTestCase(PluginStateMachine.TestCase):

    def setUp(self):
        """Create a temp working directory."""
        self._create_temp_dir_and_cd()

    def tearDown(self):
        """ Restore world order. """
        self._remove_temp_dir()

    def _create_temp_dir_and_cd(self):
        self._testdir = tempfile.mkdtemp()
        self._old_dir = os.getcwd()
        os.chdir(self._testdir)

    def _remove_temp_dir(self):
        os.chdir(self._old_dir)
        shutil.rmtree(self._testdir)


PluginStateMachine.TestCase.settings = settings(
    max_examples=1000, stateful_step_count=100, timeout=600, min_satisfying_examples=1
)



if __name__ == '__main__':
    import unittest
    unittest.main()
