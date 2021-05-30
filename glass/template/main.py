import os

from .filters import DEFAULT_FILTERS
from .parser import Lexer, Parser, TemplateSyntaxError


class Template:
    def __init__(self, source, env=None):
        self.filters = {}
        self.source = source
        self.tags = {}
        self.context = {}
        if env:
            self.add_filters(env.filters)
            self.add_tags(env.tags)
            self.context.update(env.globals)

        self._compiled_nodes = None
        self.nodelist = None
        self.env = env

    def add_filters(self, filters):
        for name, func in filters.items():
            if not hasattr(func, '__call__'):
                raise ValueError('filter func must be callable , %s' % func)
            self.filters[name] = func

    def render(self, context):
        if self._compiled_nodes is None:
            self.compile()
        context = context.copy()
        context.update(self.context)
        return self._compiled_nodes.render(context, self.env)

    def add_tags(self, tags):
        self.tags.update(tags)

    def compile(self):
        try:
            tokens = Lexer(self.source).tokenize()
            parser = Parser(tokens)
            if self.env:
                parser.tags.update(self.env.tags)
            nodelist = parser.parse()
        except TemplateSyntaxError as exc:
            details = []
            details.append(exc.msg)
            if exc.token:
                source = self.source.split('\n')

                line = exc.token.lineno
                try:
                    line_source = source[line - 1].strip()
                except IndexError:
                    line_source = ''
                details.append('line( %s)' % line)
                details.append('source( %s )' % line_source)
            error = ' ,'.join(details)
            raise TemplateSyntaxError(error, exc.token)
        self.nodelist = self._compiled_nodes = nodelist
        return self

    def __repr__(self):
        return '<Template compiled=%s >' % bool(self._compiled_nodes)


class TemplateLoader:
    def check_if_modified(self, name):
        return True


class FileLoader(TemplateLoader):
    def __init__(self, path=None):
        # save all the files loaded by this class
        # with last time each was modified
        # next time the template needs to be rendered,
        # just check if it has been modified
        self.history = {}
        if path is None:
            path = []
        if isinstance(path, str):
            path = [path]
        self.path = list(path)

    def load_template(self, name):
        if not self.path:
            # append both /path/to/{cwd}/templates
            # and /path/to/cwd
            self.path.append(os.path.join(os.getcwd(), 'templates'))
            self.path.append(os.path.join(os.getcwd()))
        for path in self.path:
            path = os.path.join(path, name)
            if not os.path.exists(path):
                continue
            self.history[path] = int(os.stat(path).st_mtime)
            with open(path, 'r') as file:
                content = file.read()
            return content
        raise OSError("Template not found %s tried %s" % ' ,'.join(name,self.path))

    def check_if_modified(self, name):
        for path in self.path:
            path = os.path.join(path,name)
            if not os.path.exists(path):
                continue
            cache_time = self.history.get(path)
            if cache_time:
                cur_time = int(os.stat(path).st_mtime)
                if cur_time > cache_time:
                    return True
                return False
            return True
        return True


class Environment:
    def __init__(self, cache=None, tags=None, filters=None, **options):

        self.cache = cache
        self.options = options
        self.loader = options.get('loader') or FileLoader()
        self.tags = tags or {}
        self.filters = filters or {}
        self.filters.update(DEFAULT_FILTERS)
        self.globals = {}

    def from_string(
        self,
        string,
    ):
        template = Template(string, env=self)
        return template.compile()

    def get_template(self, template_name):
        modified = self.loader.check_if_modified(template_name)
        # check if the template has been modified
        if not modified:
            # not modified
            if self.cache:
                #check if the compiled template is available
                #in the cache
                template = self.cache.get(template_name)
                if template:
                    #template has been compiled
                    #just render wthout having to parse again
                    return template
        load_template = self.loader.load_template(template_name)
        template = Template(load_template, env=self)
        template = template.compile()
        if self.cache is not None:
            self.cache.set(template_name, template)
        return template

    def render_template(self, template, context):
        return self.get_template(template).render(context)

    def get_globals(self):
        # override this method to add some
        # global values to the context
        return {}

    def tag(self, name):
        def inner(func):
            self.tags[name] = func
            return func

        return inner

    def filter(self, name):
        def inner(func):
            self.filters[name] = func
            return func

        return inner
