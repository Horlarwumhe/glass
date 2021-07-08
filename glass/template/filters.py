import html

DEFAULT_FILTERS = {}


def register(name):
    def inner(func):
        DEFAULT_FILTERS[name] = func
        return func

    return inner


@register('upper')
def upper(value):
    return str(value).upper()


@register('escape')
def escape(value):
    return html.escape(str(value))


@register('call')
def call(func):
    if hasattr(func, '__call__'):
        return func()
    return func
