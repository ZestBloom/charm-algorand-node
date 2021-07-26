#!/usr/bin/env python3
# Copyright 2021 ZestBloom Inc
# See LICENSE file for licensing details.

"""Charm the service."""

import logging
import setuppath

from lib_algorand import AlgorandHelper
from ops.charm import CharmBase
from ops.main import main
from ops.framework import StoredState

from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus, ModelError

from charmhelpers.core import (
    hookenv,
    host,
    unitdata,
)
from charmhelpers.fetch import (
    configure_sources, apt_install, apt_update, add_source
)

logger = logging.getLogger(__name__)


class AlgorandCharm(CharmBase):
    """Charm the service."""

    state = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.install, self._on_install)
        self.framework.observe(self.on.start, self._on_start)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.upgrade_charm, self._on_upgrade_charm)

        self.helper = AlgorandHelper(self.model.config, self.state)

        self.state.set_default(installed=False)
        self.state.set_default(configured=False)
        self.state.set_default(started=False)

        ## self._stored.set_default(things=[])
        # snap retry is excessive
        # snap.SNAP_NO_LOCK_RETRY_DELAY = 0.5
        # snap.SNAP_NO_LOCK_RETRY_COUNT = 3

    def _on_upgrade_charm(self, event):
        """Handle upgrade and resource updates."""
        # Re-install for new snaps
        logging.info("Reinstalling for upgrade-charm hook")
        self._on_install(event)

    def _on_install(self, event):
        """Charm installation event handler"""
        self.unit.status = MaintenanceStatus("Installing charm software")

        # Perform install tasks
        try:
            packages = ["algorand", "algorand-devtools"]
            add_source(
                source=self.model.config.get('install_source', None),
                key=self.model.config.get('install_key', None),
            )
            apt_install(packages, fatal=True)
        except Exception:
            self.unit.status = BlockedStatus("Algorand failed to install")
            logging.warning(
                "No resource available, install blocked, deferring event: {}".format(
                    event.handle
                )
            )
            self._defer_once(event)

            return

        host.service_stop(self.helper.service_name)
        self.unit.status = MaintenanceStatus("Install complete")
        logging.info("Install of software complete")
        self.state.installed = True

    def _on_config_changed(self, event):
        if not self.state.installed:
            logging.info(
                "Config changed called before install complete, deferring event: "
                "{}".format(event.handle)
            )
            self._defer_once(event)

            return

        try:
            self.helper.configure()
            self.unit.status = ActiveStatus()
        except Exception as e:
            logging.error(e)
            self.unit.status = ModelError("Config Change Error")

    def _on_start(self, _):
        pass

    def _defer_once(self, event):
        """Defer the given event, but only once."""
        notice_count = 0
        handle = str(event.handle)

        for event_path, _, _ in self.framework._storage.notices(None):
            if event_path.startswith(handle.split("[")[0]):
                notice_count += 1
                logging.debug("Found event: {} x {}".format(event_path, notice_count))

        if notice_count > 1:
            logging.debug(
                "Not deferring {} notice count of {}".format(handle, notice_count)
            )
        else:
            logging.debug(
                "Deferring {} notice count of {}".format(handle, notice_count)
            )
            event.defer()

if __name__ == "__main__":
    main(AlgorandCharm)

