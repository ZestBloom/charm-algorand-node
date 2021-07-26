import os
import mock
import yaml
import unittest
import tempfile

from pathlib import Path

import setuppath

from ops.testing import Harness
from src.charm import AlgorandCharm

class BaseTestAlgoCharm(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Setup class fixture."""
        # Setup a tmpdir
        cls.tmpdir = tempfile.TemporaryDirectory()

        # Create test Genesis Config Files
        for algonet in ["betanet", "devnet", "mainnet", "testnet"]:
            with open(os.path.join(cls.tmpdir.name, "test_genesis_{}".format(algonet)), "w") as f:
                f.write(algonet)

        # Stop unit test from calling fchown
        fchown_patcher = mock.patch("os.fchown")
        cls.mock_fchown = fchown_patcher.start()
        chown_patcher = mock.patch("os.chown")
        cls.mock_chown = chown_patcher.start()



        # Stop charmhelpers host from logging via debug log
        host_log_patcher = mock.patch("charmhelpers.core.host.log")
        cls.mock_juju_log = host_log_patcher.start()

        # Stop charmhelpers snap from logging via debug log
        snap_log_patcher = mock.patch("charmhelpers.fetch.snap.log")
        cls.mock_snap_log = snap_log_patcher.start()

        # Prevent charmhelpers from calling systemctl
        host_service_patcher = mock.patch("charmhelpers.core.host.service_stop")
        cls.mock_service_stop = host_service_patcher.start()
        host_service_patcher = mock.patch("charmhelpers.core.host.service_start")
        cls.mock_service_start = host_service_patcher.start()
        host_service_patcher = mock.patch("charmhelpers.core.host.service_restart")
        cls.mock_service_restart = host_service_patcher.start()

        add_source_patcher = mock.patch("src.charm.add_source")
        cls.mock_add_source = add_source_patcher.start()

        # Setup mock JUJU Environment variables
        os.environ["JUJU_UNIT_NAME"] = "mock/0"
        os.environ["JUJU_CHARM_DIR"] = "."

    @classmethod
    def tearDownClass(cls):
        """Tear down class fixture."""
        mock.patch.stopall()
        cls.tmpdir.cleanup()

    def setUp(self):
        """Set up tests."""
        self.harness = Harness(AlgorandCharm)

        # Make default config available
        with open(Path("./config.yaml"), "r") as config_file:
            config = yaml.safe_load(config_file)

        self.charm_config = {}
        for key, _ in config["options"].items():
            self.charm_config[key] = config["options"][key]["default"]

        # Disable snap retry delay for testing
        self.apt_retry_patcher = mock.patch(
            "charmhelpers.fetch.ubuntu.CMD_RETRY_DELAY", 0
        )
        self.addCleanup(self.apt_retry_patcher.stop)

        # Setup mock JUJU Environment variables
        os.environ["JUJU_UNIT_NAME"] = "mock/0"
        os.environ["JUJU_CHARM_DIR"] = "."

        # Load config defaults
        self.harness.update_config(self.charm_config)

    def get_notice_count(self, hook):
        """Return the notice count for a given charm hook."""
        notice_count = 0
        handle = "AlgorandCharm/on/{}".format(hook)

        for event_path, _, _ in self.harness.charm.framework._storage.notices(None):
            if event_path.startswith(handle):
                notice_count += 1

        return notice_count
