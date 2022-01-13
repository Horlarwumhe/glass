from glass._helpers import current_app as app
from glass._helpers import flash_messages
from glass.template import Environment, FileLoader

from .templatetags import url_for_parser

try:
    import jinja2
    from jinja2 import Environment as BaseJinjaEnvironment
    from jinja2 import FileSystemLoader as JinjaFileLoader
except ImportError:

    class BaseJinjaEnvironment:
        def __init__(self, *args, **kwargs):
            raise ValueError('jinja is required')

    JinjaFileLoader = BaseJinjaEnvironment


class Context(dict):
    pass


def render_template(template, context=None, **kwargs):
    if context is not None:
        if not isinstance(context, dict):
            raise ValueError("context must be dict")
    context = context or {}
    context = Context(context)
    backend = app.config.get('TEMPLATE_BACKEND', 'stl')
    backend_render = TEMPLATE_RENDER.get(backend)
    if not backend_render:
        raise ValueError("Unknown template backend %s" % backend)
    return backend_render(template, context, **kwargs)


def render_string(string, context=None, **kwargs):
    #TODO: code in this function similar to  above
    #fix it
    if context:
        if not isinstance(context, dict):
            raise ValueError("context must be dict")
    context = context or {}
    context = Context(context)
    backend = app.config.get('TEMPLATE_BACKEND', 'stl')
    backend_render = STRING_RENDER.get(backend)
    if not backend_render:
        raise ValueError("Unknown template backend %s" % backend)
    return backend_render(string, context, **kwargs)


def _render_stl_string(string, context, **kwargs):
    """Render string using the builtin template."""
    env = app.template_env
    context.update(kwargs)
    template = env.from_string(string)
    return template.render(context)


def _render_stl_template(template, context, **kwargs):
    """Render template file using builtin template ``stl``"""
    env = app.template_env
    context.update(kwargs)
    return env.render_template(template, context)


class AppTemplateEnviron(Environment):
    def __init__(self, app, *args, **kwargs):
        self.app = app
        tags = kwargs.pop('tags', {})
        tags.update(dict(url_for=url_for_parser))
        kwargs['tags'] = tags
        super().__init__(*args, **kwargs)
        self.add_globals()

    def add_globals(self):
        """Get global values to inject in to the templates
        """
        from glass.requests import request
        from glass.sessions import session

        globals = {
            'get_flash_messages': flash_messages,
            'request': request,
            'session': session,
            'app': self.app
        }
        self.globals.update(globals)


class AppTemplateLoader(FileLoader):
    pass

    # def load_template(self, template):
    #     path = app.config["TEMPLATES_FOLDER"]
    #     if path:
    #         path = os.path.join(path, template)
    #         if not os.path.exists(path):
    #             raise OSError("Template not found %s" % path)
    #     else:
    #         # template folder is not set in the
    #         # app.config, use default method
    #         return super().load_template(template)
    #     self.history[path] = int(os.stat(path).st_mtime)
    #     with open(path, 'r') as file:
    #         content = file.read()
    #     return content

    # def check_if_modified(self, name):
    #     path = app.config['TEMPLATES_FOLDER']
    #     if not path:
    #         # template folder is not set in the
    #         # app config, use default method
    #         return super().check_if_modified(name)
    #     path = os.path.join(path, name)
    #     if not os.path.exists(path):
    #         return True
    #     cache_time = self.history.get(path)
    #     if cache_time:
    #         cur_time = int(os.stat(path).st_mtime)
    #         if cur_time > cache_time:
    #             return True
    #         return False
    #     return True


class Cache(dict):
    def set(self, key, value):
        self[key] = value

    def get(self, key):
        return super().get(key)


###########################

# jinja2 stuffs

###########################


class JinjaEnvironment(BaseJinjaEnvironment):
    def __init__(self, app, *args, **kwargs):
        from glass.requests import request
        from glass.sessions import session
        super().__init__(*args, **kwargs)

        self.globals.update({
            'request': request,
            'app': app,
            'session': session,
            'config': app.config,
            'get_flash_messages': flash_messages
        })

    def register_filter(self, name):
        """
        app = GlassApp()
        @app.jinja_env.register_filter('split')
        def split(value,param=''):
            return value.split(param)
        # in the template
        #{{name | split(',')}}
        """
        def decor(func):
            self.filters[name] = func
            return func

        return decor


def _render_jinja_string(string, context, **kwargs):
    """Render string template using  ``jinja``"""
    template = app.jinja_env.from_string(string)

    return template.render(context, **kwargs)


def _render_jinja_template(template, context, **kwargs):
    """Render template file using ``jinja``"""
    template = app.jinja_env.get_template(template)
    return template.render(context, **kwargs)


TEMPLATE_RENDER = {
    'jinja': _render_jinja_template,
    'jinja2': _render_jinja_template,
    'stl': _render_stl_template,
}

STRING_RENDER = {
    'jinja': _render_jinja_string,
    'jinja2': _render_jinja_string,
    'stl': _render_stl_string,
}
