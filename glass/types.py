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

    def __getitem__(self, header_key):
        key = header_key.upper().replace('-', '_')
        if key not in ("REQUEST_METHOD", "CONTENT_TYPE", 'CONTENT_LENGTH'):
            key = 'HTTP_' + key
        if key in self.environ:
            return self.environ[key]
        raise KeyError(header_key)


    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def _fail(self, *args):
        raise TypeError('Read only header')

    __setitem__ = __delitem__ = pop = _fail

    def __iter__(self):
        #fix HTTP_HOST return Ost
        for key, value in self.environ.items():
            key = key.replace('_', '-')
            if key.startswith('HTTP-'):
                key = key.lstrip('HTTP').lstrip('-')
            key = key.title()
            yield key, value

    def __repr__(self):
        return str(dict(list(self)))
