import re

from glass.exception import HTTP404, MethodNotAllow

RULE_REGEX = re.compile(r'<(?:(?P<converter>[^>:]+):)?(?P<parameter>\w+)>')

CONVERTERS_REGEX = {
    'int': r'\d+',
    'path': r'.+',
    'str': r'[^/]+'
}

CONVERTERS = {
    'int': int,
    'str': str,
    'path': str
}


class Rule:
    def __init__(self, rule, callback=None, methods=None, **kw):
        self.url_rule = rule
        self.callback = callback
        self.methods = methods or []
        self.converter = {}

    def __repr__(self):
        return '<Rule %s --> %s, {%s}' % (self.url_rule, self.callback,
                                          ''.join(self.methods))

    def get_callback(self, request_method=''):
        if not self.methods or not request_method:
            return self.callback
        if not request_method in self.methods:
            raise MethodNotAllow()
        return self.callback


class Router:
    def __init__(self,app=None):
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
                regex = CONVERTERS_REGEX[converter]
            except KeyError:
                raise TypeError("unknown converter %s for the rule '%s'" %
                                (converter, original_route))
            converters[parameter] = CONVERTERS.get(converter, str)
            parts.append('(?P<' + parameter + '>' + regex + ')')
        if original_route.endswith('/'):
            parts.append('?')
        parts.append('$')
        return ''.join(parts), converters

    def add(self, rule):
        '''add new url rule'''
        regex, converter = self.compile(rule.url_rule)
        rule.converter = converter
        regex = re.compile(regex)
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
                kwargs = self.apply_converter(kwargs, rule.converter)
                if not kwargs:
                    # static url rule,
                    # example: /login/,/user/reset/ ...
                    # cache it to avoid searching next time
                    self._url_caches[path] = (rule, kwargs)

                return rule, kwargs
        raise HTTP404()

    def apply_converter(self, view_kwargs, converters):
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
            func = converters.get(param)
            if not func:
                applied[param] = value
                continue
            applied[param] = func(value)
        return applied

    def add_converter(self,name,regex,func):
        try:
            re.compile(regex)
        except re.error:
            raise ValueError('bad re syntax %s'%regex)
        CONVERTERS_REGEX[name] = regex
        CONVERTERS[name] = func
