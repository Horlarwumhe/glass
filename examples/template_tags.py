# Example on how to create custom tag for Glass application.

from glass.template import Environment
from glass.template.parser import parse_variable
from glass.template.nodes import Node

env = Environment()


@env.tag('match')
def match_parse(parser):
    match_, test = parser.get_next_token().clean_tag()
    test = parse_variable(test)  # return VarNode object
    # skip all token till {% case %}, {% default %} or
    # {% end %} is reached
    parser.skip_untill(('end', 'case', 'default'))
    cases = case_parse(parser)
    default = parse_default(parser)
    end, _ = parser.next_token().clean_tag()
    if end != 'end':
        raise ValueError('match tag expect end')
    #skip {% end %} tag
    parser.skip_token(1)
    return MatchNode(test, cases, default)


def case_parse(parser):
    # case tag is not registered, since
    # {% case %} cant stand alone, it must be
    # part of {% match %} tag
    cases = []
    cmd, _ = parser.next_token().clean_tag()
    while cmd == 'case':
        cmd, value = parser.get_next_token().clean_tag()
        # or
        # token = parser.get_next_token()
        # cmd,test = token.clean_tag()
        body = parser.parse(stop_at=('end', 'case', 'default'))
        value = parse_variable(value)  # return VarNode object
        node = CaseNode(value, body)
        cmd, _ = parser.next_token().clean_tag()
        cases.append(node)
    return cases


def parse_default(parser):
    cmd, _ = parser.next_token().clean_tag()
    if cmd == 'default':
        _ = parser.get_next_token()
        body = parser.parse(stop_at=('end', ))
        return DefaultNode(body)


class MatchNode(Node):
    #{% match test %}
    def __init__(self, test, cases, default):
        self.test = test
        self.cases = cases
        self.default = default

    def render(self, context, env=None):
        test_value = self.test.eval(context, env)
        for case in self.cases:
            case_value = case.value.eval(context, env)
            if test_value == case_value:
                return case.render(context, env)
        if self.default is not None:
            return self.default.render(context, env)
        return ''


class CaseNode(Node):
    # {% case value %}
    def __init__(self, value, body):
        self.value = value
        self.body = body

    def render(self, context, env=None):
        return self.body.render(context, env)


class DefaultNode(Node):
    def __init__(self, body):
        self.body = body

    def render(self, context, env=None):
        return self.body.render(context, env)


source = '''
   {% for user in users %}
      {% match user.status %}
        {% case 'verified' %}
            <b>{{user.name}}</b> is verified
        {% case 'pending' %}
           <b>{{user.name}}</b> is pending
       {% case 'suspend' %}
          <b>{{user.name}}</b> is suspended
       {% default %}
           <b>{{user.name}}</b> status is unknown
     {% end %}
    {% endfor %}
 '''

t = env.from_string(source)
ctx = {
    'verified':
    'verified',
    'users': [
        {
            'name': 'Horlarwumhe',
            'status': 'suspend'
        },
        {
            'name': 'Horlar',
            'status': 'pending'
        },
        {
            'name': 'Olawumi',
            'status': 'verified'
        },
        {
            'name': 'Hor',
            'status': ''
        },
    ]
}
p = t.render(ctx)
