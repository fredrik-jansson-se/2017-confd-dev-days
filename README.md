# Python, Low Level to High Level
The HL code is in main.py and the LL version is in main_orig.py.

## Run the code
make all start

## Using python to interact
Create a couple of interfaces
```python
import confd
import confd.maagic as maagic
import confd.maapi as maapi

with maapi.single_write_trans('admin', 'test') as th:
    root = maagic.get_root(th)
    for i in range(0,5):
        ti = root.interface.GigabitEthernet.create(str(i))
        ti.shutdown.create()
    th.apply()
```

Remove the shutdown flag to trigger the subscriber:
```python
import confd.maapi as maapi
import confd.maagic as maagic

with maapi.single_write_trans('admin', 'system') as th:
    root = maagic.get_root(th)
    for i in root.interface.GigabitEthernet:
        del i.shutdown
    th.apply()
```

show stats, please note db=confd.OPERATIONAL and the fact we're using a read-only transaction.
```python
import confd
import confd.maagic as maagic
import confd.maapi as maapi

with maapi.single_read_trans('admin', 'test', db=confd.OPERATIONAL) as th:
    root = maagic.get_root(th)
    for i in root.interface.GigabitEthernet:
        print(i.name, i.stats.sent, i.stats.received)
```

Clear the stats of GigabitEthernet 1
```python
import confd
import confd.maagic as maagic
import confd.maapi as maapi

with maapi.single_read_trans('admin', 'test', db=confd.OPERATIONAL) as th:
    root = maagic.get_root(th)
    root.interface.GigabitEthernet['1'].clear()
```
