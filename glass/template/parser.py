import operator
import re

from . import nodes as Node

TOKEN_REGEX = re.compile(
    '''
   (\\{%.*?%\\}|
   \\{\\{.*?\\}\\}|
   \\{\\#.*?\\#\\}
   )''', re.VERBOSE)

VAR = re.compile(r'''
^[\w_\.]+
''', re.VERBOSE)

STRING = re.compile(r'''
(('.*')|".*")(\.\w+)*
''', re.VERBOSE)

FILTER = re.compile(r'''
\s*\|\s*\w+
''', re.VERBOSE)

operators = {
    'in': operator.contains,
    '==': operator.eq,
    '>': operator.gt,
    '<': operator.lt,
    '>=': operator.ge,
    '<=': operator.le,
    '!=': operator.ne,
    'and': operator.and_,
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.floordiv,
    'not': operator.not_
}


class TemplateSyntaxError(Exception):
    def __init__(self, msg, token=None):
        self.msg = msg
        self.token = token
        super().__init__(msg)


default_tags = {}


def register_tag(name):
    def inner(func):
        default_tags[name] = func
        return func
    return inner


class Token:
    def __init__(self, token_type, content, lineno=0):
        self.type = token_type
        self.content = content
        self.lineno = lineno

    def __repr__(self):
        return "<Token %s %s" % (self.type, str(self))

    def __str__(self):
        if self.type == 'VAR':
            return '{{ %s }}' % self.content.strip()
        elif self.type == 'BLOCK':
            return '{%c %s %c}' % (37, self.content, 37)
        return self.content.strip()[:20]

    def clean_tag(self):
        if self.type not in ("BLOCK", "ENDBLOCK"):
            return '', ''
        try:
            cmd, *rest = self.content.split(maxsplit=1)
        except ValueError:
            raise TemplateSyntaxError('Empty tag node', self)
        return cmd, ''.join(rest)


class Lexer:
    def __init__(self, template):
        self.template = template

    def tokenize(self):
        tokens = []
        lineno = 1
        for token in TOKEN_REGEX.split(self.template):
            if not token:
                continue
            if token.startswith('{{'):
                content = self.clean(token[2:-2])
                tokens.append(Token('VAR', content, lineno))
            elif token.startswith('{%'):
                content = token[2:-2]
                content = self.clean(content)
                if re.search('end[a-z]+', content):
                    tokens.append(Token('BLOCK', self.clean(content), lineno))
                else:
                    tokens.append(Token('BLOCK', self.clean(content), lineno))
            else:
                if not token.isspace():
                    tokens.append(Token("TEXT", token, lineno))
            lineno += token.count('\n')
        return tokens

    def clean(self, token):
        return token.strip().rstrip()


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens.copy()
        self.tags = {}
        self.tags.update(default_tags)

    def next_token(self):
        try:
            return self.tokens[0]
        except IndexError:
            return None

    def get_next_token(self):
        try:
            return self.tokens.pop(0)
        except IndexError:
            return None

    def parse(self, stop_at=None):
        if not stop_at:
            stop_at = []
        result = []
        while 1:
            token = self.get_next_token()
            if not token:
                if stop_at:
                    raise TemplateSyntaxError("expect %s" % ",".join(stop_at))
                break
            if token.type == "ENDBLOCK":
                self.tokens.insert(0, token)
                break
            if token.type == "BLOCK":
                cmd, _ = token.clean_tag()
                if cmd in stop_at:
                    self.tokens.insert(0, token)
                    break
                ret = self.parse_block(token)
            elif token.type == 'VAR':
                ret = parse_variable(token.content)
            elif token.type == 'TEXT':
                ret = Node.TextNode(token.content)
            result.append(ret)
        return Node.NodeList(result)

    def parse_block(self, token):
        try:
            cmd = token.content.split(maxsplit=1)[0]
        except IndexError:
            raise TemplateSyntaxError('Empty block tag ', token)
        self.tokens.insert(0, token)
        try:
            ret = self.tags[cmd](self)
        except KeyError:
            if re.search('end[a-z]+', cmd):
                raise TemplateSyntaxError("Unexpected token %s" % token, token)
            raise TemplateSyntaxError('Uknown tag %s' % token, token)
        return ret

    def skip_token(self, n=1):
        for _ in range(n):
            self.get_next_token()

    def skip_untill(self, tags):
        cmd, _ = self.next_token().clean_tag()
        while cmd not in tags:
            self.skip_token(1)
            token = self.next_token()
            if token:
                cmd, _ = token.clean_tag()
            else:
                raise TemplateSyntaxError("unclosed tag expect one of %s" %
                                          ','.join(tags))


def parse_variable(var):
    # TODO
    var = var.strip().rstrip()
    match = VAR.match(var)
    funcs = []
    if match:
        end = match.end()
        var_name = match.group()
    else:
        match = STRING.match(var)
        if match:
            end = match.end()
            var_name = match.group()
        else:
            raise TemplateSyntaxError('couldnt parse %s ' % var)
    for match in FILTER.finditer(var):
        start = match.start()
        if start != end:
            raise TemplateSyntaxError('couldnt parse %s from ( %s )' %
                                      (var[end:start], var))
        func = ''.join(match.group().split()).strip('|')
        funcs.append(func)
        end = match.end()
    if end != len(var):
        raise TemplateSyntaxError('couldnt  parse %s from %s' %
                                  (var[end:], var))
    return Node.VarNode(var_name, funcs)


@register_tag('if')
def if_parse(parser):
    token = parser.get_next_token()
    cmd, args = token.clean_tag()
    body = parser.parse(stop_at=("elif", 'else', "endif"))
    elifs = elif_parse(parser)
    else_ = else_parse(parser)
    parser.parse(stop_at=("endif", ))
    parser.skip_token(1)
    condition = condition_parse(token)
    return Node.IfNode(condition, elifs, else_, body)


def elif_parse(parser):
    token = parser.next_token()
    cmd, args = token.clean_tag()
    elifs = []
    while cmd == "elif":
        token = parser.get_next_token()
        _, args = token.clean_tag()
        body = parser.parse(stop_at=("elif", "else", "endif"))
        condition = condition_parse(token)
        node = Node.ElifNode(condition, body)
        elifs.append(node)
        token = parser.next_token()
        cmd, _ = token.clean_tag()
    return elifs


def else_parse(parser, stop=None):
    # stop can be endif or endfor
    cmd, _ = parser.next_token().clean_tag()
    if cmd == "else":
        parser.skip_token(1)
        if not stop:
            stop = ("endif", )
        body = parser.parse(stop_at=stop)
        return Node.ElseNode(body)
    return None


def condition_parse(token):
    """Parse if/elif condition
    eg. if i, if not i, if i > 1:
    """
    _, args = token.clean_tag()
    bits = args.split()
    if len(bits) == 3:
        # a == b
        # x > y
        # h in list
        lhs, op, rhs = bits
    elif len(bits) == 2:
        # not a
        rhs = None
        op, lhs = bits
        if op != 'not':
            raise TemplateSyntaxError(
                'unexpected token'
                ' "{op}" {t} line {line}'.format(op=op,
                                                 t=token,
                                                 line=token.lineno), token)
    elif len(bits) == 1:
        # if condition
        lhs = bits[0]
        rhs = op = None
    else:
        raise TemplateSyntaxError('unknown condition type %s' % token, token)
    if lhs:
        lhs = parse_variable(lhs)
    if rhs:
        rhs = parse_variable(rhs)
    if op and op not in operators:
        raise TemplateSyntaxError('unknown operator %s in %s' % (op, token),
                                  token)
    return Node.ConditionNode(lhs, op, rhs)


@register_tag('for')
def for_parse(parser):
    token = parser.get_next_token()
    cmd, args = token.clean_tag()
    body = parser.parse(stop_at=('endfor', 'else'))
    else_ = else_parse(parser, ('endfor', ))
    parser.skip_token(1)
    bits = args.split()
    match = re.search(r'\b(in)\b', args)
    if not match:
        raise TemplateSyntaxError('for loop expect in', token)
    loopvars = args[:match.start()]
    iter_object = args[match.end():].strip()
    loopvars = ''.join(loopvars.split()).rstrip(',')
    loopvars = loopvars.split(',')
    for var in loopvars:
        if not var.isidentifier():
            raise TemplateSyntaxError('invalid loop variable %s' % var, token)
    iter_obj = parse_variable(iter_object)
    return Node.ForNode(loopvars, iter_obj, body, else_)


@register_tag('filter')
def filter_parse(parser):
    token = parser.get_next_token()
    _, args = token.clean_tag()
    body = parser.parse(stop_at=('end', ))
    args = ''.join(args.split()).rstrip(',')
    args = args.split(',')
    for _ in args:
        if not _.isidentifier():
            raise TemplateSyntaxError(
                "Filter tag require an identifier not %s" % _, token)
    parser.skip_token(1)
    return Node.FilterNode(args, body)


@register_tag('extends')
def parse_extend(parser):
    token = parser.get_next_token()
    _, args = token.clean_tag()
    args = args.split()
    if len(args) > 1 or not args:
        raise TemplateSyntaxError('extends requires one arg', token)
    template = args[0].strip('"').strip("'")
    nodelist = parser.parse()

    return Node.ExtendNode(template, nodelist)


@register_tag('block')
def parse_block(parser):
    token = parser.get_next_token()
    _, args = token.clean_tag()
    args = args.split()
    block_super = False
    super_end = False
    if len(args) == 2:
        if args[1] != 'super':
            raise TemplateSyntaxError(
                'second arg of block tag should be super not %s' % args[1],
                token)
        block_super = True
    elif len(args) != 1 or not args:
        raise TemplateSyntaxError('block tag requires atleast one arg', token)
    body = parser.parse(stop_at=('endblock', ))
    # endblock tag
    _, endargs = parser.get_next_token().clean_tag()
    if endargs:
        super_end = endargs.split()[0]
        if super_end == 'super' and not block_super:
            super_end = True
    name = args[0]
    return Node.BlockNode(name, body, block_super, super_end)


@register_tag('include')
def parse_include(parser):
    _, name = parser.get_next_token().clean_tag()
    name = name.split()[0]
    return Node.IncludeNode(name)
