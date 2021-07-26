#!/usr/bin/env python3
# Copyright 2021 ZestBloom Inc
# See LICENSE file for licensing details.

import os
import sys

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
)

from charmhelpers.core.host import (
    service_start,
    service_stop,
)


def check_node_status(args):
    """Return the output of 'rabbitmqctl cluster_status'.

    :param args: Unused
    :type args: List[str]
    """
    try:
        nodestat = check_output(['goal', 'node', 'status'],
                                   universal_newlines=True)
        action_set({'output': nodestat})
    except CalledProcessError as e:
        action_set({'output': e.output})
        action_fail('Failed to run rabbitmqctl cluster_status')
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


# A dictionary mapping the defined actions to callables
ACTIONS = {
    "check-node-status": check_node_status,
    "restart-service": restart_service,
}


def main(args):
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