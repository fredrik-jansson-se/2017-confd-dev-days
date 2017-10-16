#!/usr/bin/env python

import confd.maapi as maapi
import confd.maagic as maagic

with maapi.single_write_trans('admin', 'system') as t:
    root = maagic.get_root(t)
    for i in root.interface.GigabitEthernet:
        i.shutdown.create()
    t.apply()
