#!/usr/bin/env python

import logging

import socket
import select


from config_ns import ns
import confd.maapi as maapi
import _confd
import _confd.dp as dp
import _confd.cdb as cdb
import _confd.error as confd_errors

from counters import get_counters, clear_counters


class MySub(object):
    def __init__(self, log, path, prio=100):
        self.log = log
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.path = path
        self.prio = prio

        cdb.connect(self.sock, cdb.SUBSCRIPTION_SOCKET, '127.0.0.1',
                    _confd.CONFD_PORT, self.path)
        self.subid = cdb.subscribe(self.sock, self.prio, ns.hash, self.path)
        cdb.subscribe_done(self.sock)

        log.info("Subscribed to {path}".format(path=self.path))

    def on_data(self):
        cdb.read_subscription_socket(self.sock)

        state = []
        cdb.diff_iterate(self.sock, self.subid, self.iter_fn, 0, state)

        cdb.sync_subscription_socket(self.sock, cdb.DONE_PRIORITY)

        for s in state:
            self.log.info(s)

    def iter_fn(self, keypath, op, _oldv, _newv, state):
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


def make_tag_value(ns_hash, tag, value):
    """
    Wrapper to create a _confd.TagValue
    """
    return _confd.TagValue(_confd.XmlTag(ns_hash, tag),
                           _confd.Value(value))


class ActionCallbacks(object):
    def __init__(self, log, worker_sock):
        self.log = log
        self.wsock = worker_sock

    def cb_init(self, uinfo):
        self.log.info("init_action called")
        dp.action_set_fd(uinfo, self.wsock)

    def cb_action(self, uinfo, name, keypath, params):
        if_name = str(keypath[0][0])
        self.log.info("clear interface name =" + if_name)
        (old_sent, old_received) = clear_counters(if_name)
        result = [
            make_tag_value(ns.hash, ns.config_received, str(old_received)),
            make_tag_value(ns.hash, ns.config_sent, str(old_sent))
        ]
        dp.action_reply_values(uinfo, result)


class TransCbs(object):

    def __init__(self, workersocket):
        self._workersocket = workersocket

    def cb_init(self, tctx):
        dp.trans_set_fd(tctx, self._workersocket)
        return _confd.CONFD_OK

    def cb_finish(self, tctx):
        return _confd.CONFD_OK


class DataCbs(object):

    def __init__(self, log):
        self.log = log

    def cb_get_elem(self, tctx, keypath):
        self.log.info("cb_get_elem: " + str(keypath))

        if_name = str(keypath[2][0])
        (sent, recv) = get_counters(if_name)

        tag = str(keypath[0])

        if tag == 'sent':
            val = _confd.Value(str(sent))
        elif tag == 'received':
            val = _confd.Value(str(recv))

        dp.data_reply_value(tctx, val)
        return _confd.CONFD_OK


def connect(dctx, csock, wsock):
    """
    Connect the sockets
    """
    # Create the first control socket, all requests to
    # create new transactions arrive here
    dp.connect(dx=dctx,
               sock=csock,
               type=dp.CONTROL_SOCKET,
               ip='127.0.0.1',
               port=4565)

    # Also establish a workersocket, this is the most simple
    # case where we have just one ctlsock and one workersock
    dp.connect(dx=dctx,
               sock=wsock,
               type=dp.WORKER_SOCKET,
               ip='127.0.0.1',
               port=4565)


def read_data(dctx, sock):
    try:
        dp.fd_ready(dctx, sock)
    except (confd_errors.Error) as e:
        # Callback error
        if e.confd_errno is _confd.ERR_EXTERNAL:
            print(str(e))
        else:
            raise e


def poll_loop(dctx, ctrl_sock, worker_sock, subscriber):
    """
    Check for I/O
    """
    _r = [ctrl_sock, worker_sock, subscriber.sock]
    _w = []
    _e = []

    try:
        while True:
            r, _, _ = select.select(_r, _w, _e)

            for rs in r:
                if rs == ctrl_sock:
                    read_data(dctx=dctx, sock=ctrl_sock)
                elif rs == worker_sock:
                    read_data(dctx=dctx, sock=worker_sock)
                elif rs == subscriber.sock:
                    subscriber.on_data()

    except KeyboardInterrupt:
        print("\nCtrl-C pressed\n")


def main():
    log = logging.getLogger(__file__)

    # Need to load the schemas in the Python VM
    with maapi.Maapi(load_schemas=True):
        pass

    ctrl_sock = socket.socket()
    worker_sock = socket.socket()

    dctx = dp.init_daemon("example")

    connect(dctx=dctx,
            csock=ctrl_sock,
            wsock=worker_sock)

    # register the action handler callback object
    acb = ActionCallbacks(worker_sock=worker_sock, log=log)
    dp.register_action_cbs(dctx, 'clear', acb)

    tcb = TransCbs(worker_sock)
    dp.register_trans_cb(dctx, tcb)
    dcb = DataCbs(log)
    dp.register_data_cb(dctx, ns.config_stats_, dcb)

    dp.register_done(dctx)

    subscriber = MySub(log, '/interface')
    try:
        poll_loop(dctx, ctrl_sock, worker_sock, subscriber)
    finally:
        worker_sock.close()
        ctrl_sock.close()
        dp.release_daemon(dctx)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
