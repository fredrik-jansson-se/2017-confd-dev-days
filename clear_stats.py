import confd
import confd.maagic as maagic
import confd.maapi as maapi

with maapi.single_read_trans('admin', 'test', db=confd.OPERATIONAL) as th:
    root = maagic.get_root(th)
    root.interface.GigabitEthernet['1'].clear()
