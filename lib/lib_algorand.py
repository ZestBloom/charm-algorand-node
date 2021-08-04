#! /usr/bin/env python3
# Copyright © 2021 ZestBloom Inc
# Distributed under terms of the GPL license.
import os
import logging
import shutil

from charmhelpers.core import templating


class AlgorandHelper:
    """Algorand Node Helper module"""

    def __init__(self, config, state):
        """Initialize the module with charm config and state."""
        self.charm_config = config
        self.state = state

        self.config_path = "/var/lib/algorand/config.json"
        self.genesis_path = "/var/lib/algorand/genesis.json"
        self.genesis_template_path = "/var/lib/algorand/genesis/{}/genesis.json"
        self.service_name = "algorand.service"

        self._algod_token = "/var/lib/algorand/algod.token"

        os.environ["ALGORAND_DATA"] = "/var/lib/algorand"

    def configure(self):
        """Update configuration."""
        logging.info("Configuring Algorand Node")

        algonet = self.charm_config["algo_net"]
        if algonet not in ["betanet", "devnet", "mainnet", "testnet"]:
            logging.exception("Unexpected Algorand Genesis Network specified")
        else:
            # Set Genesis File
            shutil.copyfile(
                self.genesis_template_path.format(algonet),
                self.genesis_path
            )

        # Render Config File
        self.render_config()


    def render_config(self):
        """Render algorand node config file"""
        context = {}

        context["AnnounceParticipationKey"] = self.charm_config.get("AnnounceParticipationKey")
        context["Archival"] = self.charm_config.get("Archival")
        context["BaseLoggerDebugLevel"] = self.charm_config.get("BaseLoggerDebugLevel")
        context["EnableDeveloperAPI"] = self.charm_config.get("EnableDeveloperAPI")

        # TODO
        # TLS Cert
        # TLS Key

        templating.render(
            "config.yaml",
            self.config_path,
            context,
            owner="algorand",
            group="algorand",
            perms=0o440
        )
