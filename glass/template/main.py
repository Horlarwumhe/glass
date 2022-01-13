import os

import glass.constant as const

from .filters import DEFAULT_FILTERS
from .parser import Lexer, Parser, TemplateSyntaxError


class Template:
    """Main template. Use :class:`~Environment` instead of this.

    :param source: template source

    ::

      template =Template('Hello {{user}}')
      template.render({'user':'Horlar'})
    """
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
        self.body = None
        self.env = env
        self.filename = ''

    def add_filters(self, filters):
        for name, func in filters.items():
            if not hasattr(func, '__call__'):
                raise ValueError('filter func must be callable , %s' % func)
            self.filters[name] = func

    def render(self, context):
        """Render template"""
        if self._compiled_nodes is None:
            self.compile()
        self.context.update(context)
        self.context[const.TEMPLATE_FILENAME] = self.filename
        return self._compiled_nodes.render(self.context, self.env)

    def add_tags(self, tags):
        self.tags.update(tags)

    def compile(self):
        """Compile template source"""
        try:
            tokens = Lexer(self.source).tokenize()
            parser = Parser(tokens)
            if self.env:
                parser.tags.update(self.env.tags)
            nodelist = parser.parse()
        except TemplateSyntaxError as exc:
            details = []
            details.append(exc.msg)
            filename = self.filename or '<string>'
            details.append('file="%s",'%filename)
            if exc.token:
                source = self.source.split('\n')

                line = exc.token.lineno
                try:
                    line_source = source[line - 1].strip()
                except IndexError:
                    line_source = ''
                details.append('line=%s,'% line)
                details.append('source=(%s),' % line_source)
            error = ' '.join(details)
            raise TemplateSyntaxError(error, exc.token) from None
        self.nodelist = self._compiled_nodes = self.body = nodelist
        return self

    def __repr__(self):
        return '<Template compiled=%s name="%s">' % (bool(self._compiled_nodes), self.filename)


class TemplateLoader:
    def check_if_modified(self, name):
        return True


class FileLoader(TemplateLoader):
    """Template loader class to load templates from FileSystem(directory).
    The argument can be a directory or list of directories

    >>> loader = FileLoader('/path/to/templates')
    >>> # load templates from multiple directories
    >>> loader = FileLoader(['/path/to/templates','/path/to/other/templates'])
    >>> env = Environment(loader=loader)
    """
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
        """Load template to render.
        Returns the template source.
        """
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
        raise OSError("Template not found %s, tried %s" %
                      (name, ' ,'.join(self.path)))

    def check_if_modified(self, name):
        '''Check if the template has been modified or not.
        Returns True if it has been modified, False if not.
        '''
        for path in self.path:
            path = os.path.join(path, name)
            if not os.path.exists(path):
                continue
            cache_time = self.history.get(path)
            if cache_time:
                now = int(os.stat(path).st_mtime)
                if now > cache_time:
                    return True
                return False
            return True
        return True


class Environment:
    '''The main environment for templates. The environment stores
    tags and filter available to all templates and loader to load templates
    from diffferent sources.

    :param cache: an object use to cache compiled templates.
      default ``None`` (dont cache)

    :param tags: dict of custom tags.

    :param loader: template loader class to load templates.
    :param filters: dict of custom filters.
    '''
    def __init__(self,
                 cache=None,
                 tags=None,
                 filters=None,
                 loader=None,
                 **options):

        self.cache = cache
        # self.options = options
        self.loader = loader or FileLoader()
        self.tags = tags or {}
        self.filters = filters or {}
        self.filters.update(DEFAULT_FILTERS)
        self.globals = {}
        # options not used now. keep for future use.
        self.options = options

    def from_string(
        self,
        string,
    ):
        """Gets template to render from string,
        Returns :class:`~Template`

        >>> env = Environment()
        >>> template = env.from_string('hello {{user}}')
        >>> template.render({'user':'Horlar'})
        """
        template = Template(string, env=self)
        template.compile()
        return template

    def get_template(self, template_name):
        '''Gets template to render from file.
        Returns :class:`~Template`.
        ::

        >>> env = Environment()
        >>> template = env.get_template('index.html')
        >>> template.render({})
        '''
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
        template.filename = template_name
        template.compile()
        if self.cache is not None:
            self.cache.set(template_name, template)
        return template

    def render_template(self, template, context):
        """Render template from file.
        ::

        >>> env = Environment()
        >>> env.render_template('index.html',{})
        """
        return self.get_template(template).render(context)

    def get_globals(self):
        # override this method to add some
        # global values to the context
        return {}

    def tag(self, name):
        """Decorator to register custom tags.
        ::

            @env.tag('tagname')
            def parse(parser):
                # parse the tag here
        """
        def inner(func):
            self.tags[name] = func
            return func

        return inner

    def filter(self, name):
        """Decorator to register custom filter
        ::

            @env.filter('upper')
            def upper(value):
                return value.upper()
        """
        def inner(func):
            self.filters[name] = func
            return func

        return inner
