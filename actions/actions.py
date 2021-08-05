#!/usr/bin/env python3
# Copyright 2021 ZestBloom Inc
# See LICENSE file for licensing details.

import os
import sys
import urllib3

from subprocess import check_output, CalledProcessError

_path = os.path.dirname(os.path.realpath(__file__))
_lib = os.path.abspath(os.path.join(_path, '../lib'))


def _add_path(path):
    if path not in sys.path:
        sys.path.insert(1, path)


_add_path(_lib)


from charmhelpers.core.hookenv import (
    action_fail,
    action_set,
    config,
)

from charmhelpers.core.host import (
    service_start,
    service_stop,
)

FAST_CATCHUP_URLS = {
    "betanet": "https://algorand-catchpoints.s3.us-east-2.amazonaws.com/channel/betanet/latest.catchpoint",
    "testnet": "https://algorand-catchpoints.s3.us-east-2.amazonaws.com/channel/testnet/latest.catchpoint",
    "mainnet": "https://algorand-catchpoints.s3.us-east-2.amazonaws.com/channel/mainnet/latest.catchpoint",
}


def check_node_status(args):
    """Return the output of 'goal node status'.

    :param args: Unused
    :type args: List[str]
    """
    try:
        nodestat = check_output(['goal', 'node', 'status'],
                                   universal_newlines=True)
        action_set({'output': nodestat})
    except CalledProcessError as e:
        action_set({'output': e.output})
        action_fail('Failed to check algorand node status')
    except Exception:
        raise


def restart_service(args):
    """Restarts Algorand Node service.

    :param args: Unused
    :type args: List[str]
    """
    try:
        service_stop('algorand')
        service_start('algorand')
    except CalledProcessError as e:
        action_set({'output': e.output})
        action_fail('Failed to start algorand service after force_boot')
        return False


def fast_catchup(args):
    """Executes Fast Catch-Up for the Node"""

    # Get the Fast Catch-Up Token
    algo_net = config()["algo_net"]
    catchup_url =  FAST_CATCHUP_URLS[algo_net]
    http = urllib3.PoolManager()
    r = http.request('GET', catchup_url)
    catchup_token = r.data.decode("utf-8").strip()

    try:
        cmd = ['goal', 'node', 'catchup', f'{catchup_token}']
        catchup_op = check_output(cmd, universal_newlines=True)
        action_set({'output': catchup_op})
    except CalledProcessError as e:
        action_set({'output': e.output})
        action_fail('Failed to run fast-catchup')


# A dictionary mapping the defined actions to callables
ACTIONS = {
    "check-node-status": check_node_status,
    "restart-service": restart_service,
    "fast-catchup": fast_catchup,
}


def main(args):
    os.environ["ALGORAND_DATA"] = "/var/lib/algorand"
    action_name = os.path.basename(args[0])
    try:
        action = ACTIONS[action_name]
    except KeyError:
        s = "Action {} undefined".format(action_name)
        action_fail(s)
        return s
    else:
        try:
            action(args)
        except Exception as e:
            action_fail("Action {} failed: {}".format(action_name, str(e)))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
