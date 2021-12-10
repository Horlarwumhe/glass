import ast
import logging
import operator
import re
import types
import warnings

logger = logging.getLogger('glass.template')

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
    '//': operator.floordiv
}


class TemplateSyntaxError(Exception):
    def __init__(self, msg, token=None):
        self.msg = msg
        self.token = token
        super().__init__(msg)


class Node:
    def render(self, context, env=None):
        return ''


class TextNode(Node):
    def __init__(self, text):
        self.text = text
        super().__init__()

    def render(self, context, env=None):
        return self.text

    def __repr__(self):
        return ' <TextNode text={}'.format(self.text.strip()[:20])


class VarNode(Node):
    def __init__(self, var_name, funcs=None):
        self.var_name = self.var = var_name
        self.funcs = funcs or []
        self.args = ()
        super().__init__()

    def render(self, ctx, env=None):
        ret = self.eval(ctx, env)
        if ret is None:
            return ''
        # it is possible for self.eval to return non string
        # example, {{name.split}} which return list
        return str(ret)

    def eval(self, ctx, env=None):
        '''This wil be called when VarNode is part of a block tag
        eg. {% for name is names %}, {% if name %}, this will be called
        to know what (name) is.
        If it is not part of tag eg {{name}}, then render will be called
        '''
        if not self.var:
            return None
        # var = self.var
        if self.var[0] in ("'", '"'):
            quote = self.var[0]
            i = self.var.index(quote, 1)
            string = self.var[:i + 1]
            attrs = self.var[i + 1:]
            attrs = attrs.split('.')
            var = string
        else:
            var, *attrs = self.var.split('.')
        var = self.resolve(var, ctx)
        if var is None:
            return None
        if isinstance(
                var, (types.MethodType, types.FunctionType,
                      types.BuiltinFunctionType)):
            var = var()
        for attr in attrs:
            if not attr:
                continue
            attr = attr.strip()
            if hasattr(var, attr):
                func = getattr(var, attr)
                if isinstance(func, (types.MethodType, types.FunctionType,
                                     types.BuiltinFunctionType)):
                    var = func()
                else:
                    var = func
            elif hasattr(var, '__getitem__'):
                try:
                    var = var[attr]
                except (KeyError, TypeError):
                    # try list
                    # list.0
                    try:
                        var = var[int(attr)]
                    except (LookupError, ValueError, TypeError):
                        return

            else:
                return
        if env:
            for func in self.funcs:
                callback = env.filters.get(func)
                if callback:
                    var = callback(var)
        return var

    def resolve(self, var, context):
        var = var.strip()
        try:
            return ast.literal_eval(var)
        except ValueError:
            return context.get(var)

    def __repr__(self):
        return '<Var %s' % self.var_name

    @classmethod
    def parse(cls, var):

        warnings.warn(
            "classmethod nodes.VarNode.parse is depreciated."
            " Use function variable_parse() in glass.template.parser",
            UserWarning)
        var = var.strip()
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
                raise TemplateSyntaxError('couldnt parse %s .' % var)
        for match in FILTER.finditer(var):
            start = match.start()
            if start != end:
                raise TemplateSyntaxError('couldnt parse %s from ( %s ).' %
                                          (var[end:start], var))
            func = ''.join(match.group().split()).strip('|')
            funcs.append(func)
            end = match.end()
        if end != len(var):
            raise TemplateSyntaxError('couldnt  parse %s from %s.' %
                                      (var[end:], var))
        return cls(var_name, funcs)


class IfNode(Node):
    def __init__(self, condition, elifs, else_body, body):
        self.elifs = elifs
        self.else_ = else_body
        self.body = body
        self.condition = condition
        super().__init__()

    def render(self, context, env=None):
        match = self.condition.eval(context, env)
        if match:
            return self.body.render(context, env)
        for elif_ in self.elifs:
            match = elif_.condition.eval(context, env)
            if match:
                return elif_.body.render(context, env)
        if self.else_:
            body = self.else_.body
            return body.render(context, env)
        return ''


class ForNode(Node):
    def __init__(self, var, iter_object, body, else_=None):
        super().__init__()
        self.iter_object = iter_object
        self.body = body
        self.loopvars = self.var = var
        self.else_ = else_

    def render(self, context, env=None):
        iter_object = self.iter_object.eval(context, env)
        for_context = context.copy()
        if not hasattr(iter_object, '__iter__'):
            return ''
        loopvars = self.loopvars
        result = []
        multi = len(loopvars) > 1
        use_else = True
        if not hasattr(iter_object, '__len__'):
            iter_object = list(iter_object)
        for index, item in enumerate(iter_object):
            use_else = False
            if multi:
                try:
                    item_len = len(item)
                except TypeError:
                    item_len = 1
                if item_len != len(loopvars):
                    raise TypeError(
                        "For loop sequence '%s' returned %s value(s),"
                        " but loop variable has %s values(s), (%s)." %
                        (self.iter_object.var, item_len, len(loopvars),
                         ','.join(loopvars)))
                key_value = zip(loopvars, item)
                for_context.update(key_value)
            else:
                for_context[self.loopvars[0]] = item
            loop = LoopCounter(iter_object)
            loop.set_index(index)
            for_context['loop'] = loop
            result.append(self.body.render(for_context, env))
        if use_else and self.else_ is not None:

            return self.else_.body.render(for_context, env)
        return ''.join(result)


class ElseNode(Node):
    def __init__(self, body):
        self.body = body
        super().__init__()

    def render(self, context, env=None):
        # This is never called, rendering of this
        # node is done when redering if node
        return ''


class ConditionNode(Node):
    '''Test of if/elif node
    {% if condition %}
    the condition can take 3 forms
    1. lhs op rhs (if 1 == 2),(if a or b)
    2. not lhs (if not user.name)
    3. lhs (if user.name)
    '''
    def __init__(self, lhs, op, rhs):
        self.lhs = lhs
        self.rhs = rhs
        self.op = op
        super().__init__()

    def eval(self, context, env=None):
        lhs = rhs = None
        if self.lhs:
            lhs = self.lhs.eval(context, env)
        if self.rhs:
            rhs = self.rhs.eval(context, env)
        if self.op == 'not':
            # {% if not x %}
            return operator.not_(lhs)
        if not self.op:
            # {% if x %}
            return bool(lhs)
        try:
            # {% if x op y %}
            # op is supported operator
            return operators[self.op](lhs, rhs)
        except TypeError:
            # probably datatype issue,
            # eg str > int
            return False
        except KeyError:
            # this should not occur.
            raise TypeError('Unknown operator "%s".' % self.op)


class ElifNode(Node):
    '''elif node'''
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body
        super().__init__()

    def render(self, context, env=None):
        # This is never called, rendering of this
        # node is done when redering if node
        return ''


class FilterNode(Node):
    '''{% filter upper %}
           everyting here with be in upper case
           including {{user.name}}
        {% end %}
        but not this, it is outside the filter node
    '''
    def __init__(self, funcs, body):
        self.funcs = funcs
        self.body = body
        super().__init__()

    def render(self, context, env=None):
        result = self.body.render(context, env)
        if env:
            for func in self.funcs:
                callback = env.filters.get(func)
                if callback:
                    result = callback(result)
        # callback might not return string
        return str(result)

    def __repr__(self):
        return '<FilterNode filters=[{}]'.format(','.join(self.funcs))


class IncludeNode(Node):
    def __init__(self, template):
        self.template = template

    def render(self, context, env=None):
        template_name = self.template.eval(context, env)
        if template_name is None:
            msg = "Couldn't find template refers to as '%s' in include tag." % self.template.var_name
            raise TemplateSyntaxError(msg)
        if env:
            template = env.get_template(template_name)
            return template.render(context)
        return ''


class ExtendNode(Node):
    def __init__(self, template, nodelist):
        self.template = template
        self.nodelist = self.body = nodelist

    def render(self, context, env=None):
        if env:
            template = self.template.eval(context, env)
            if template is None:
                # {% extends name %}
                msg = "Couldn't find template refers to as '%s' in extend tag." % self.template.var_name
                raise TemplateSyntaxError(msg)
            parent = env.get_template(template)
            parent_nodelist = parent.body
            extend = None
            parent_blocks = iter([])
            if len(parent_nodelist.nodelist) > 0:
                first_node = parent_nodelist.nodelist[0]
                if first_node.__class__ is self.__class__:
                    extend = first_node
                    parent_blocks = extend.nodelist.get_node_by_type(BlockNode)
                else:
                    parent_blocks = parent_nodelist.get_node_by_type(BlockNode)
            parent_blocks = {block.name: block for block in parent_blocks}
            blocks = self.nodelist.get_node_by_type(BlockNode)
            for block in blocks:
                if block.name in parent_blocks:
                    current_block = parent_blocks[block.name]
                    if block.is_super:
                        current_block.nodelist.add_node(block)
                    elif block.is_super_end:
                        current_block.nodelist.insert_node(0, block)
                    else:
                        if extend:
                            extend.nodelist.replace_node(current_block, block)
                        else:
                            parent.nodelist.replace_node(current_block, block)
                elif extend:
                    # This block is not found in the parent template. Parent template also
                    # extends another template.
                    extend.nodelist.add_node(block)
                else:
                    # block not found, parent doesn't extend other template.
                    # ignore ? warning ? just append it ?
                    pass
            return parent.render(context)
        return self.nodelist.render(context, env)

    def __repr__(self):
        return '<ExtendNode template={}'.format(self.template.var_name)


class BlockNode(Node):
    def __init__(self, name, nodelist, is_super, is_super_end=False):
        self.name = name
        self.nodelist = self.body = nodelist
        self.is_super = is_super
        self.is_super_end = is_super_end

    def render(self, context, env=None):
        return self.nodelist.render(context, env)

    def __repr__(self):
        return '<BlockNode name={} is_super={} is_super_end={}'.format(
            self.name, self.is_super, self.is_super_end)


class SetNode(Node):

    def __init__(self,kwargs):
        self.kwargs = kwargs


    def render(self,context,env=None):
        resolved = {}
        for key,value in self.kwargs.items():
            resolved[key] = value.eval(context,env)
        context.update(resolved)
        return ""

class NodeList(Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist
        super().__init__()

    def render(self, context, env=None):
        results = []
        for node in self.nodelist:
            result = node.render(context, env)
            if result is None:
                logger.warning(
                    '%s returns None'
                    '  all template nodes are expected to return str'
                    '  the result of this node is ignored' % node.__class__)
                continue
            results.append(str(result))
        if hasattr(self, '_original_nodes_'):
            self.nodelist = self._original_nodes_
            del self._original_nodes_
        return ''.join(results)

    def get_node_by_type(self, nodetype):
        for node in self.nodelist:
            if isinstance(node, nodetype):
                yield node

    def replace_node(self, node, replacement_node):
        self._copy_nodelist()
        if not isinstance(replacement_node, Node):
            return
        try:
            i = self.nodelist.index(node)
        except ValueError:
            return
        self.nodelist[i] = replacement_node

    def add_node(self, node):
        self._copy_nodelist()
        self.nodelist.append(node)

    def insert_node(self, pos, node):
        self._copy_nodelist()
        self.nodelist.insert(pos, node)

    def _copy_nodelist(self):
        """Little tricky here.
        The nodelist for a Node object are copied temporary.
        For extends tag which will override the some blocks tag in
        other template,the original nodelist are copied so the nodelist can
        be restored back to the default nodelist after the Node is rendered.
        """

        if hasattr(self, '_original_nodes_'):
            return
        self._original_nodes_ = self.nodelist.copy()


class LoopCounter:


    def __init__(self,iteratable):
        self._index = 0
        self.iteratable = list(iteratable)

    @property
    def index(self):
        # 1 based index
        return self._index + 1

    @property
    def index_0(self):
        # 0 based index
        return self._index

    @property
    def first(self):
        return self.index == 1

    @property
    def last(self):
        return self.index == len(self.iteratable)


    def set_index(self,index):
        self._index = index



