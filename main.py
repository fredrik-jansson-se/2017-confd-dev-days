#!/usr/bin/env python

import logging
import time

import socket
import select


from config_ns import ns
import confd.maapi as maapi
import _confd

from confd.experimental import Subscriber, DataCallbacks
from confd.dp import Action, Daemon

from counters import get_counters, clear_counters


class MySub(Subscriber):
    def pre_iterate(self):
        return []

    def post_iterate(self, state):
        for s in state:
            self.log.info(s)


    def should_post_iterate(self, state):
        return state != []

    def iterate(self, keypath, op, _oldv, _newv, state):
        self.log.info("iter_fn: " + str(keypath))
        if 'GigabitEthernet' == str(keypath[1]):
            self.log.info("Handling GigabitEthernet")
            name = str(keypath[0][0])
            if _confd.MOP_DELETED == op:
                state.append("Delete GigabitEthernet " + name)
            elif _confd.MOP_CREATED == op:
                state.append("Add GigabitEthernet " + name)
            elif _confd.MOP_MODIFIED == op:
                state.append("Changed GigabitEthernet " + name)
            else:
                self.log.info("Unknown op: " + str(op))

            return _confd.ITER_CONTINUE


class ActionCallbacks(Action):
    @Action.action
    def cb_action(self, uinfo, name, keypath, input, output):
        if_name = str(keypath[0][0])
        self.log.info("clear interface name =" + if_name)
        (old_sent, old_received) = clear_counters(if_name)
        output.sent = old_sent
        output.received = old_received

class DataCbs(object):
    def __init__(self, log):
        self.log = log


    def get_object(self, tctx, keypath, _args):

        self.log.info("cb_get_elem: " + str(keypath))

        if_name = str(keypath[2][0])
        (sent, recv) = get_counters(if_name)
        return {
            "stats": {
                "sent": sent,
                "received": recv
            }
        }

def poll_loop():
    try:
        while True:
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nCtrl-C pressed\n")


def main():
    log = logging.getLogger(__file__)

    # Need to load the schemas in the Python VM
    with maapi.Maapi(load_schemas=True):
        pass

    d = Daemon('demo')

    # register the action handler callback object
    acb = ActionCallbacks(d, 'clear', log)

    acb.start()

    handler = DataCbs(log)
    dcb = DataCallbacks(log)
    dcb.register('/config:interface/config:GigabitEthernet', handler)
    _confd.dp.register_data_cb(d.ctx(), ns.callpoint_stats, dcb)

    d.start()

    subscriber = MySub(log=log)
    subscriber.register('/interface')
    subscriber.start()

    try:
        poll_loop()
    finally:
        subscriber.stop()
        acb.stop()
        d.finish()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
