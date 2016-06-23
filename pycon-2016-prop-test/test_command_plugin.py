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
from hypothesis.stateful import precondition, rule, RuleBasedStateMachine
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
        self._pre_installed = set() if plugins is None else set(plugins)
        self._installed = set()
        self.disabled = set()

    @property
    def installed(self):
        return (self._installed | self._pre_installed) - self.disabled

    def install(self, name):
        self._installed.add(name)

    def remove(self, name):
        self._safe_remove(self._pre_installed, name)
        self._safe_remove(self._installed, name)

    def disable(self, name):
        self.disabled.add(name)

    def enable(self, name):
        self._safe_remove(self.disabled, name)

    def _safe_remove(self, set_, name):
        if name in set_:
            set_.remove(name)


class PluginStateMachine(RuleBasedStateMachine):
    def __init__(self):
        super(PluginStateMachine, self).__init__()
        self._create_demo_site()
        self._update_disabled_plugins([])
        self._init_site_object()
        self._update_installed_disabled()
        self.model = SimplifiedPluginModel(self._installed)

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

    def _update_installed_disabled(self):
        output = self._run_command(['--list-installed'])
        self._installed = set(re.findall('(.*)\s+at\s+.*', output))
        d_ = re.findall("disabled these plugins: \[(.+)\]", output)
        self._disabled = set(re.sub("[',]", "", d_[0]).split()) if d_ else set()
        self._installed.difference_update(self._disabled)
        return self._installed

    def _install(self, name):
        self._run_command(['-i', name])
        self.model.install(name)
        self._update_installed_disabled()

    def _remove(self, name):
        self._run_command(['-r', name])
        self.model.remove(name)
        self._update_installed_disabled()

    def _get_disabled(self):
        import conf
        utils._reload(conf)
        return set(getattr(conf, 'DISABLED_PLUGINS', []))

    def _is_disabled(self, name):
        return name in self._get_disabled()

    DISABLED_RE = re.compile('\nDISABLED_PLUGINS = .*')

    def _update_disabled_plugins(self, disabled_plugins):
        disabled_plugins = '\nDISABLED_PLUGINS = {}'.format(repr(disabled_plugins))

        with open('conf.py') as f:
            text = f.read()
            match = self.DISABLED_RE.search(text)
            if match is not None:
                text_ = self.DISABLED_RE.sub(disabled_plugins, text)

            else:
                text_ = text + disabled_plugins

        with open('conf.py', 'w') as f:
            f.write(text_)
            f.flush()

    def _disable(self, name):
        disabled_plugins = list(self._get_disabled()|set([name]))
        self._update_disabled_plugins(disabled_plugins)
        self._update_installed_disabled()
        self.model.disable(name)

    def _enable(self, name):
        if self._is_disabled(name):
            disabled_plugins = list(self._get_disabled() - set([name]))
            self._update_disabled_plugins(disabled_plugins)
            self.model.enable(name)
        self._update_installed_disabled()

    def assert_model_state_matches(self):
        # NOTE: Can't check equality, since some plugins install other plugins.
        # There is no way to find out the dependency before hand.
        assert self._installed.issuperset(self.model.installed)
        assert self._disabled == self.model.disabled

    @rule(name=plugin_name_generator())
    def install(self, name):
        self._install(name)
        if name in self.model.installed:
            assert name in self._installed

        else:
            assert name in self.model.disabled
            assert name not in self._installed
        self.assert_model_state_matches()

    @rule(name=plugin_name_generator())
    # FIXME: Not good enough precondition, can we do better?
    @precondition(lambda self: len(self.model._installed) > 0)
    def remove(self, name):
        assume(name in self.model.installed)
        self._remove(name)
        assert name not in self._installed
        self.assert_model_state_matches()

    @rule(name=plugin_name_generator())
    def disable(self, name):
        self._disable(name)
        assert name not in self.model.installed
        assert name not in self._installed
        self.assert_model_state_matches()

    @rule(name=plugin_name_generator())
    def enable(self, name):
        self._enable(name)
        assert ((name in self._installed) == (name in self.model.installed))
        self.assert_model_state_matches()


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
