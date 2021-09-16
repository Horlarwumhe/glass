import functools
import threading


class cached_property:
    '''cache result of some methods'''
    def __init__(self, key=None):
        self.key = key

    def __call__(self, func):
        functools.update_wrapper(self, func)
        self.func = func
        self.key = self.key or func.__name__
        return self

    def __get__(self, obj, cls):
        if not obj:
            return self
        storage = obj.__storage__ if hasattr(obj,
                                             '__storage__') else obj.__dict__
        if self.key not in storage:
            try:
                ret = self.func(obj)
            except AttributeError as e:
                # due to how __get__ is implemeted in python
                # doing this is required
                raise TypeError(e)
            storage[self.key] = ret
        return storage[self.key]

    def __set__(self, obj, value):
        raise TypeError("cant set attribute")


def _thread_local():
    '''This is very useful on multithread
    web servers
    credit: github.com/bottlepy/bottlepy
    '''
    ls = threading.local()

    def fget(obj):
        try:
            return ls.var
        except AttributeError:
            if obj.__class__.__name__ in ('Request', 'Session'):
                raise RuntimeError(
                    "Request context not initialized. "
                    "This means you are trying to use function that "
                    "requires HTTP request")
            raise RuntimeError("%s object not initialized" %
                               obj.__class__.__name__)

    def fset(_, value):
        ls.var = value

    def fdel(_):
        del ls.var

    return property(fget, fset, fdel, 'Thread-local property')


def encode(value, encoding='utf-8'):
    if isinstance(value, str):
        return value.encode(encoding)
    return value


def decode(value, encoding='utf-8'):
    if isinstance(value, (bytes, bytearray)):
        return value.decode(encoding)
    return value
