import tempfile
import unittest
import mock
import yaml
import os

from types import SimpleNamespace

from lib.lib_algorand import AlgorandHelper

class TestLibAlgorand(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Setup class fixture."""
        # Load default config
        with open("./config.yaml") as default_config:
            cls.config = yaml.safe_load(default_config)
        # Setup a tmpdir
        cls.tmpdir = tempfile.TemporaryDirectory()
        # Class wide mocks
        charm_dir_patcher = mock.patch(
            "charmhelpers.core.hookenv.charm_dir", lambda: "."
        )
        cls.mock_charm_dir = charm_dir_patcher.start()
        fchown_patcher = mock.patch("os.fchown")
        cls.mock_fchown = fchown_patcher.start()
        host_log_patcher = mock.patch("charmhelpers.core.host.log")
        cls.mock_juju_log = host_log_patcher.start()

    @classmethod
    def tearDownClass(cls):
        """Tear down class fixture."""
        mock.patch.stopall()
        cls.tmpdir.cleanup()

    def setUp(self):
        """Setup test fixture."""
        self.helper = AlgorandHelper(self.config, SimpleNamespace())
        self.helper.config_path = tempfile.NamedTemporaryFile(
            prefix="config_", dir=self.tmpdir.name
        ).name
        # Setup a tmpfile for the genesis file
        self.helper.genesis_path = tempfile.NamedTemporaryFile(
            prefix="genesis_", dir=self.tmpdir.name
        ).name

        # Set a genesis template path to the pattern of the test genesis files
        self.helper.genesis_template_path = \
            os.path.join(self.tmpdir.name, "test_genesis_{}")

        # Setup charm deafult states
        self.helper.state.installed = False
        self.helper.state.configured = False
        self.helper.state.started = False

    def tearDown(self):
        """Clean up test fixture."""
        pass