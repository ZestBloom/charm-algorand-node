# Copyright 2021 ZestBloom Inc
# See LICENSE file for licensing details.
import os
import mock
import yaml
import subprocess
import tempfile

import setuppath  # noqa:F401

from unittest_base import BaseTestAlgoCharm

class TestCharm(BaseTestAlgoCharm):

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

        self.mock_add_source.assert_called_with(
            source=self.charm_config["install_source"],
            key=self.charm_config["install_key"]
        )

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
        self.assertEqual(self.get_notice_count("config_changed"), 0)

        # No config value should be empty
        for key in ["Archival",
                    "AnnounceParticipationKey",
                    "BaseLoggerDebugLevel"]:
            self.assertNotEqual(config[key], None)
