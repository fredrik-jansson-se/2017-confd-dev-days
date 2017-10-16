import confd
import confd.maagic as maagic
import confd.maapi as maapi

m = maapi.Maapi()
m.start_user_session('admin', 'test_context')
