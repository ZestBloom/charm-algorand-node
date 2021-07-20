# Copyright 2021 Ryan Farrell
# See LICENSE file for licensing details.
import os
import mock
import yaml
import unittest
import subprocess
from pathlib import Path
import tempfile
from unittest.mock import Mock

import setuppath  # noqa:F401

import ops
from ops.testing import Harness
from src.charm import AlgorandCharm


class TestCharm(unittest.TestCase):

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

        # Make default config available
        with open(Path("./config.yaml"), "r") as config_file:
            config = yaml.safe_load(config_file)
        cls.charm_config = {}

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
        # Prevent charmhelpers from calling systemctl
        host_service_patcher = mock.patch("charmhelpers.core.host.service_stop")
        self.mock_service_stop = host_service_patcher.start()
        host_service_patcher = mock.patch("charmhelpers.core.host.service_start")
        self.mock_service_start = host_service_patcher.start()
        host_service_patcher = mock.patch("charmhelpers.core.host.service_restart")
        self.mock_service_restart = host_service_patcher.start()

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

    def test_01_harness(self):
        """Verify harness."""
        self.harness.begin()
        self.assertFalse(self.harness.charm.state.installed)

    @mock.patch("charmhelpers.fetch.ubuntu.subprocess.check_call")
    def test_02_install_failed(self, mock_ubuntu_subprocess):
        """Test install failure."""
        mock_ubuntu_subprocess.return_value = 1
        error = subprocess.CalledProcessError("cmd", "Install failed")
        error.returncode = 1
        mock_ubuntu_subprocess.side_effect = error
        self.apt_retry_patcher.start()
        self.harness.begin()
        self.harness.charm.on.install.emit()
        self.assertEqual(self.harness.charm.unit.status.name, "blocked")
        self.assertEqual(
            self.harness.charm.unit.status.message,
            "Algorand failed to install",
        )

    def test_03_config_changed_defer(self):
        """Test config changed defer."""
        self.harness.begin()
        self.harness.charm.state.installed = False
        self.harness.charm.on.config_changed.emit()

        self.assertEqual(self.get_notice_count("config_changed"), 1)

    @mock.patch("charmhelpers.fetch.ubuntu.subprocess.check_call")
    def test_04_install_success(self, mock_ubuntu_subprocess):
        """Test install success."""
        mock_ubuntu_subprocess.return_value = 0
        mock_ubuntu_subprocess.side_effect = None
        self.harness.begin()
        self.harness.charm.on.install.emit()
        self.assertEqual(self.harness.charm.unit.status.name, "maintenance")
        self.assertEqual(
            self.harness.charm.unit.status.message,
            "Install complete",
        )

    @mock.patch("charmhelpers.fetch.snap.subprocess.check_output")
    def test_05_config_changed_ready(self, mock_snap_check_output):
        """Test config changed when ready."""
        self.harness.begin()

        # Setup a tmpfile for the config file
        self.harness.charm.helper.config_path = tempfile.NamedTemporaryFile(
            prefix="config_", dir=self.tmpdir.name
        ).name
        # Setup a tmpfile for the genesis file
        self.harness.charm.helper.genesis_path = tempfile.NamedTemporaryFile(
            prefix="genesis_", dir=self.tmpdir.name
        ).name

        # Set a genesis template path to the pattern of the test genesis files
        self.harness.charm.helper.genesis_template_path = \
            os.path.join(self.tmpdir.name, "test_genesis_{}")

        self.harness.charm.state.installed = True
        self.harness.charm.on.config_changed.emit()

        # Verify expected contents of the genesis path
        expected_genesis_contents = self.harness.charm.config["algo_net"]
        with open(self.harness.charm.helper.genesis_path, "r") as f:
            actual_genesis_data = f.read().strip()
        self.assertEqual(expected_genesis_contents, actual_genesis_data)

        # Config changed after install should process
        with open(self.harness.charm.helper.config_path) as config_file:
            config = yaml.safe_load(config_file)
        # self.assertEqual(self.harness.charm.state.exporter_configured, True)
        # self.assertEqual(self.get_notice_count("config_changed"), 0)

        # No config value should be empty
        for key, value in config["install_key"].items():
           self.assertNotEqual(
               value, None, "Install Key config '{}' is None".format(key)
           )

        # Check config values
        ## self.assertEqual(config["logging"]["level"], "INFO")
