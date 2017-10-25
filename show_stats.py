import confd
import confd.maagic as maagic
import confd.maapi as maapi

with maapi.single_read_trans('admin', 'test', db=confd.OPERATIONAL) as th:
    root = maagic.get_root(th)
    for i in root.interface.GigabitEthernet:
        print(i.name, i.stats.sent, i.stats.received)
