from glass.template import Template, Environment
from glass.template.nodes import VarNode

env = Environment()


@env.tag('match')
def match_parse(parser):
    match_, test = parser.get_next_token().clean_tag()
    test = VarNode.parse(test)
    parser.skip_untill(('end', 'case'))
    cases = case_parse(parser)
    end, _ = parser.next_token().clean_tag()
    if end != 'end':
        raise ValueError('match tag expect end')
    parser.skip_token(1)
    return MatchNode(test, cases)


def case_parse(parser):
    cases = []
    cmd, _ = parser.next_token().clean_tag()
    while cmd == 'case':
        cmd, value = parser.get_next_token().clean_tag()
        #token = parser.get_next_token()
        # cmd,test = token.clean_tag()
        body = parser.parse(stop_at=('end', 'case'))
        value = VarNode.parse(value)
        node = CaseNode(value, body)
        cmd, _ = parser.next_token().clean_tag()
        cases.append(node)
    return cases


@env.filter('upper')
def func(value):
    return value.upper()


class MatchNode:
    #{% match test %}
    def __init__(self, test, cases):
        self.test = test
        self.cases = cases

    def render(self, context, env=None):
        test_value = self.test.eval(context, env)
        for case in self.cases:
            case_value = case.value.eval(context, env)
            print(test_value, case_value)
            if test_value == case_value:
                return case.render(context, env)
        return ''


class CaseNode:
    # {% case value %}
    def __init__(self, value, body):
        self.value = value
        self.body = body

    def render(self, context, env=None):
        return self.body.render(context, env)


t = env.from_string('''{% if user %} hm {% endif %}
''')
context = {'user': {'name': 'ola', 'status': 'pending'}}
p = t.render(context)
t = env.from_string('''
 {% match user.status %}

      {% case 'verified' %}
         hello
          {{user.name | upper  }} {{ user.name.upper.lower | escape }}

      {% case 'pending' %}
         {{user.name}} is pending

      {% case 'suspend' %}
         {{user.name}} is suspend
    {% end %}
''')

i = t.render(context)
s = '''
 {% match user.status %}

      {% case 'verified' %}
          {{user.name | upper  }} {{" <b> is verified <b> ".upper}}

      {% case 'pending' %}
         {{user.name}} is pending

      {% case 'suspend' %}
         {{user.name}} is suspend
    {% end %}
    {% if k %}
'''
print(i, 'helllo')
