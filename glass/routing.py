import re
import types
from urllib.parse import quote as urlquote
from urllib.parse import urlencode, urlparse, urlunparse

from glass.exception import HTTP404, MethodNotAllow

# from glass.requests import request
from ._helpers import current_app as app

RULE_REGEX = re.compile(r'<(?:(?P<converter>[^>:]+):)?(?P<parameter>\w+)>')

CONVERTERS_REGEX = {'int': r'\d+', 'path': r'.+', 'str': r'[^/]+'}

# CONVERTERS = {'int': int, 'str': str, 'path': str}


class ParamConverter:
    def __init__(self, name, converter):
        self.param_name = name
        self.regex = converter.regex  # raw regex
        self.c_regex = re.compile(self.regex)  # compiled regex
        self.converter_name = converter.name
        self.converter = converter

    def __call__(self, *args):
        return self.__class__

    def __repr__(self):
        return '<Param %s --> %s' % (self.param_name, self.converter_name)

    def to_python(self, value):
        return self.converter.to_python(value)

    def to_url(self, value):
        return self.converter.to_url(value)


class Rule:
    def __init__(self, rule, callback=None, methods=None, **kw):
        self.url_rule = rule
        self.callback = callback
        self.methods = methods or []
        self.converter = {}
        self.params = {}
        self.regex = ''

    def __repr__(self):
        return '<Rule %s --> %s, {%s}' % (self.url_rule, self.callback,
                                          ', '.join(self.methods))

    def get_callback(self, request_method=''):
        if not self.methods or not request_method:
            return self.callback
        if request_method not in self.methods:
            raise MethodNotAllow()
        return self.callback

    def __call__(self, **kwargs):
        return self.callback(**kwargs)

    def build(self, **kwargs):
        if not self.regex:
            raise TypeError
        out = self.url_rule
        missing_args = set(self.params) - set(kwargs)
        if missing_args:
            raise TypeError("Rule (%s) missing required parameters %s " %
                            (self.url_rule, missing_args))
        for _, param_converter in self.params.items():
            try:
                value = kwargs.pop(param_converter.param_name)
            except KeyError:
                # unlikely to occur. line 58 above.
                raise
            value = param_converter.to_url(value)
            # if not param_converter.c_regex.match(value):
            #    pass
            sub = '<(%s:)?%s>' % (param_converter.converter_name,
                                  param_converter.param_name)
            pattern = re.compile(sub)
            out = pattern.sub(value, out)
        return out


class Router:
    def __init__(self, app=None):
        self.rules = []
        self._url_caches = {}

    def compile(self, rule):
        '''compile url rule to regex
        return the rule regex and converters

        credit: github.com/django/django

        '''
        original_route = rule
        parts = ['^']
        converters = {}
        while True:
            match = RULE_REGEX.search(rule)
            if not match:
                parts.append(re.escape(rule))
                break
            parts.append(re.escape(rule[:match.start()]))
            rule = rule[match.end():]
            parameter = match.group('parameter')
            if not parameter.isidentifier():
                raise TypeError('invalid identifier (%s) in URL rule %s' %
                                (parameter, original_route))
            converter = match.group('converter')
            if converter is None:
                # no converter, default is str
                converter = 'str'
            try:
                converter_cls = CONVERTERS[converter]
            except KeyError:
                raise TypeError("unknown converter %s for the rule '%s'" %
                                (converter, original_route))
            param_converter = ParamConverter(parameter, converter_cls())
            converters[parameter] = param_converter
            parts.append('(?P<' + parameter + '>' + converter_cls.regex + ')')
        if original_route.endswith('/'):
            parts.append('?')
        parts.append('$')
        return ''.join(parts), converters

    def add(self, rule):
        '''add new url rule'''
        regex, params = self.compile(rule.url_rule)
        #rule.converter = dict((k, v.func) for k, v in params.items())
        regex = re.compile(regex)
        rule.regex = regex
        rule.params = params
        self.rules.append((rule, regex))

    def match(self, environ):
        path = environ["PATH_INFO"]
        rule, view_kwargs = self._url_caches.get(path, (None, None))
        if rule:
            return rule, view_kwargs
        for rule, regex in self.rules:
            match = regex.match(path)
            if match:
                kwargs = match.groupdict()
                kwargs = self.apply_converter(kwargs, rule)
                if not kwargs:
                    # static url rule,
                    # example: /login/,/user/reset/ ...
                    # cache it to avoid searching next time
                    self._url_caches[path] = (rule, kwargs)

                return rule, kwargs
        raise HTTP404()

    def apply_converter(self, view_kwargs, rule):
        '''apply converter to url rule
        if the url rule == '/<str:user>/<int:user_id>'
        for this url '/horlar/1',
        the url parameter and value is
        {'user':'horlar','user_id':'1'}
        converters map : {'user_id':int,'user':str}
        when the converters are applied
        the parameter and value now seem to be
        {'user':str('horlar'),'user_id':int('1')}
        '''
        applied = {}
        for param, value in view_kwargs.items():
            converter = rule.params.get(param)
            if not converter:
                applied[param] = value
                continue
            applied[param] = converter.to_python(value)
        return applied

    def add_converter(self, name, regex, func):
        try:
            re.compile(regex)
        except re.error:
            raise ValueError('bad re syntax %s' % regex)
        CONVERTERS_REGEX[name] = regex
        CONVERTERS[name] = func

    def use_converter(self, converter):
        CONVERTERS[converter.name] = converter


def url_for(view_name, **kwargs):
    '''Build url for a view
    ::

      @app.route('/u/login')
      def login():
        return "Hello"
      # url_for('login')

    :param view_name: name of the url view

    Required arguments.
       arguments for the target  url.
       ``/u/<id>/<username>/``
       url_for('view',id=58,username='user')

    Optional arguments.
    Note, optional arguments start with ``_``

    :param _scheme: url scheme (``http``, ``https`` or other)

                    if not given, scheme is determined in this order.

                    1 . from app configuration, app.config['SERVER_NAME'] = ``'http://domain.com'``

                    2. default to 'http'.

    :param _fragment: value after ``#`` in url ``http://domai.com/a/a#target``.
                      default to '',no fragment.

    :param _target: same as ``_fragment``

    Other arguments provided will be used as query string for the url.
    ::
       path = url_for('login',q="1",x="2",y="3")``
       # /u/login?q=1&x=2&y=3

    .. versionadded:: 0.0.3

    '''

    if isinstance(view_name, types.FunctionType):
        view_name = view_name.__name__
    rule = app.view_func.get(view_name)
    if not rule:
        raise LookupError('Endpoint with view name "%s" not found' % view_name)
    path = rule.build(**kwargs)
    for param in rule.params:
        kwargs.pop(param, None)
    server_name = app.config['SERVER_NAME']
    if server_name is None:
        server_name = ''
    fragment = kwargs.pop('_fragment', '')
    if not fragment:
        fragment = kwargs.pop('_target', '')
    scheme = kwargs.pop('_scheme', '')
    uri = urlparse(server_name)
    netloc = uri.netloc
    scheme = scheme or uri.scheme or 'http'
    if not netloc and uri.path:
        if not uri.path.startswith('/'):
            # /www.domain.com is consider as path
            netloc = uri.path[:-1] if uri.path.endswith('/') else uri.path
        # urlparse('www.domain.com')
        # urllib parse this as path and not netloc
    if not netloc and scheme:
        scheme = ''
    query_string = urlencode(kwargs)
    url = urlunparse(
        (scheme, netloc, urlquote(path), '', query_string, fragment))
    return url


class BaseCoverter:

    regex = ''
    name = ''

    def to_url(self, value):
        return NotImplemented

    def to_python(self, value):
        pass


class StrConverter(BaseCoverter):
    regex = r'[^/]+'
    name = 'str'

    def to_url(self, value):
        return str(value)

    def to_python(self, value):
        return str(value)


class IntConverter(BaseCoverter):
    regex = r'\d+'
    name = 'int'

    def to_url(self, value):
        return str(value)

    def to_python(self, value):
        return int(value)


class PathConverter(StrConverter):
    regex = r'.+'
    name = 'path'


CONVERTERS = {
    'int': IntConverter,
    'str': StrConverter,
    'path': PathConverter,
}
