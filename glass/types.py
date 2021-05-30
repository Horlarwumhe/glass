class Header(dict):
    '''Response headers
    '''
    def __init__(self, default=None):
        if default:
            if isinstance(default, dict):
                default = default.items()
            for key, value in default:
                self.add(key, value)

    def add(self, name, value):
        self[name] = value

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default


class WSGIHeader(dict):
    '''Headers passed to the app from WSGI server
    without modification
    '''
    def __init__(self, environ):
        self.environ = environ

    def __getitem__(self, key):
        key = key.upper().replace('-', '_')
        if key not in ("REQUEST_METHOD","CONTENT_TYPE", 'CONTENT_LENGTH'):
            key = 'HTTP_' + key
        return self.environ[key]

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def _fail(self, *args):
        raise TypeError('Read only header')

    __setitem__ = __delitem__ = _fail

    def __iter__(self):
        for key, value in self.environ.items():
            key = key.replace('_', '-')
            if key.startswith('HTTP_'):
                key = key.lstrip('HTTP_')
            key = key.title()
            yield key, value
