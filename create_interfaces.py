# coding: utf-8
import confd
import confd.maagic as maagic
import confd.maapi as maapi

with maapi.single_write_trans('admin', 'test') as th:
    root = maagic.get_root(th)
    for i in range(0,5):
        ti = root.interface.GigabitEthernet.create(str(i))
        ti.shutdown.create()
    th.apply()

