import random

IF_CTRS = {}

def get_counters(if_name):
    global IF_CTRS
    (sent, recv) = IF_CTRS.get(if_name, (0, 0))
    new_sent = sent + random.randrange(0, 200)
    new_recv = recv + random.randrange(0, 200)

    IF_CTRS[if_name] = (new_sent, new_recv)

    return (sent, recv)


def clear_counters(if_name):
    global IF_CTRS
    sent_recv = IF_CTRS.get(if_name, (0, 0))
    IF_CTRS[if_name] = (0, 0)
    return sent_recv
