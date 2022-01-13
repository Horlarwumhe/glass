import re

from glass.routing import url_for
from glass.template.nodes import Node
from glass.template.parser import TemplateSyntaxError, parse_variable
from glass.template.utils import smart_split

# from ._helpers import url_for

pattern_kwag = re.compile(r"(\w+)\s*=\s(.+)*")
pattern_kwarg = re.compile(r'''
    \w+\s*=\s*(\w+|'.*?'|".*?")
    ''', re.VERBOSE)


def url_for_parser(parser):
    # {%  url_for 'view' arg="val1" arg2=val2 arg3=' val ' %}
    token = parser.get_next_token()
    _, args_str = token.clean_tag()
    args_list = smart_split(args_str)
    view_kwargs = {}
    if not args_list:
        raise TemplateSyntaxError("url_for requires at least one argument",
                                  token)
    view_name = args_list[0]
    args_list = args_list[1:]
    for args in args_list:
        try:
            key, value = map(str.strip, args.split('=', 1))
        except ValueError:
            raise TemplateSyntaxError('malformed argumentin url_for tag',
                                      token)
        view_kwargs[key] = parse_variable(value)
    view_name = parse_variable(view_name)
    return URLForNode(view_name, view_kwargs)


class URLForNode(Node):
    def __init__(self, view_name, view_kwargs):
        self.view_name = view_name
        self.view_kwargs = view_kwargs

    def render(self, ctx, env=None):
        view_name = self.view_name.eval(ctx, env)
        if view_name is None:
            return ''
        resolved = {}
        for key, var_node in self.view_kwargs.items():
            value = var_node.eval(ctx, env)
            resolved[key] = value
        return url_for(view_name, **resolved)
