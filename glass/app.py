import logging
import os

from glass.config import Config
from glass.exception import HTTPError, InternalServerError
from glass.requests import request
from glass.response import JsonResponse, Redirect, Response, send_static
from glass.routing import Router, Rule
from glass.sessions import SessionManager
from glass.templating import (AppTemplateEnviron, AppTemplateLoader, Cache,
                              JinjaEnvironment, JinjaFileLoader)
from glass.utils import cached_property

from ._helpers import app_stack

logger = logging.getLogger('glass.app')
stream = logging.StreamHandler()
stream.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s: %(message)s',
                              datefmt='%d/%m/%Y %H:%M:%S %p')
stream.setFormatter(formatter)
logger.addHandler(stream)
logger.setLevel(logging.DEBUG)


class GlassApp:
    """Main application object
    ::

      from glass import GlassApp

      app = GlassApp()
      @app.route('/')
      def home():
         return 'Hello'
    """
    def __init__(self, **kwargs):

        self.session_cls = SessionManager()
        self.config = Config()
        self.router = Router()
        self.error_code_handlers = {}
        self.error_handlers = {}
        self.before_request_funcs = []
        self.after_request_funcs = []
        self.url_rules = []
        self.view_func = {}
        static_url = self.config['STATIC_URL'] or 'static'
        static_url = static_url.strip('/')
        self.add_url_rule('/%s/<path:filename>' % static_url,
                          self.send_static,
                          view_name='static')

    @cached_property()
    def template_env(self):
        """Returns :class:`~glass.template.main.Environment` instance."""
        env = AppTemplateEnviron(
            self,
            loader=AppTemplateLoader(path=self.config['TEMPLATES_FOLDER']),
            cache=self.template_cache)
        return env

    @cached_property()
    def jinja_env(self):
        path = self.config['TEMPLATES_FOLDER']
        if not path:
            path = os.path.abspath(os.path.join(os.getcwd(), 'templates'))
        env = JinjaEnvironment(self, loader=JinjaFileLoader(path))
        return env

    def send_static(self, filename):
        return send_static(filename, self, request)

    @cached_property()
    def template_cache(self):
        return Cache()

    def route(self, url_rule, methods='GET', view_name=None, **kwargs):
        """Register a view function for URL as decorator
        ::

           @app.route('/')
           def index():
              return 'Hello'
        """
        def decorator(func):
            self._add_rule(url_rule, func, methods, view_name, **kwargs)
            return func

        return decorator

    def _add_rule(self, url_rule, func, methods, view_name=None, **kwargs):

        if not methods:
            methods = ["GET"]
        if isinstance(methods, str):
            methods = [methods]
        methods = list(map(str.upper, methods))
        rule = Rule(url_rule, func, methods, **kwargs)
        self.router.add(rule)
        self.url_rules.append(rule)
        if not view_name:
            view_name = func.__name__
        self.view_func[view_name] = rule

    def add_url_rule(self, rule, func, methods=None, view_name=None):
        return self.route(rule, methods, view_name)(func)

    def get(self, url_rule, **kwargs):
        return self.route(url_rule, 'GET', **kwargs)

    def post(self, url_rule, **kwargs):
        return self.route(url_rule, 'POST', **kwargs)

    def before_request(self, func):
        """Register a function to run before each request.
           For example, this can be used to open a database connection, or to load
           logged in user from   session.

        ::

            @app.before_request
            def load_user():
                id = session.get('user_id')
                if id:
                    user = db.get(id=id)
                    request.user = user
                else:
                    # make sure to set request.user = value
                    # to avoid python raising AttributeError
                    request.user = None


        If the function doest not return None, the return value will be
        used as the response.
        ::

           @app.before_request
           def maintenance():
              return "This site is under maintenance"

        ::

          def load_user():
            pass
          app.before_request(load_user)

        """
        self.before_request_funcs.append(func)
        return func

    def after_request(self, func):
        """Register a function to run after each request.

        This can be used to add header(s) or cookie(s) to the response.
        The function takes one argument,(:class:`glass.response.Response`) and must return
        the same response object.

        ::

           @app.after_request
           def set(response):
             response.set_header('name','value')
             response.set_cookie('name','value',path='/')
             return response

           @app.after_request
           def turn_upper(response):
              if isinstance(response.content,(str,bytes)):
                  response.content = response.content.upper()
              return response

        """
        self.after_request_funcs.append(func)
        return func

    def error(self, error):
        """Register a function to call when an error occurs in the
        application. The function can be registered with code or
        exception class. The function takes the exception class
        as argument.

        ::

              @app.error(404):
              def not_found(err):
                return "path not found"

              # with exception class
              @app.error(TypeError)
              def type_error(error):
                assert error.__class__ is TypeError
                return 'TypeError exception occurs'
        """
        def decorator(func):
            if isinstance(error, int):
                self.error_code_handlers[error] = func
            else:
                self.error_handlers[error] = func
            return func

        return decorator

    def url_converter(self, name, regex, func):
        self.router.add_converter(name, regex, func)


    def use_converter(self,converter):
        self.router.use_converter(converter)

    def run(self, host='127.0.0.1', port=8000, debug=None, auto_reload=False):
        """Run the application development server.

        :param host: ip address to listen on. default to localhost ``127.0.0.1``
        :param port: port for the server to listen. default to ``8000``
        :param auto_reload: enable reloader. reload the server when the
               app source files change. default to ``False``
        :param debug: run the app in debug mode.

        ::

            app = GlassApp()
            @app.route('/')
            def index():
                return "Hello"
            app.run(debug=True)
        """
        if debug is not None:
            self.config['DEBUG'] = bool(debug)
        from glass.server import GlassServer
        GlassServer().run_app(self, host, port, auto_reload)

    def mount(self, environ=None):
        ''' see :ref:`doc <mount-app>`'''

        app_stack.push(self)
        if environ is not None:
            request.bind(environ)
            self.session_cls.open()
        return app_stack

    def _call_before_request(self):
        for func in self.before_request_funcs:
            response = func()
            if response:
                return response
        return None

    def _call_after_request(self, response):
        return_value = None
        for func in self.after_request_funcs:
            return_value = func(response)
            if not isinstance(return_value, response.__class__):
                raise TypeError(
                    'after_request function should return %s not %s' %
                    (response.__class__, return_value.__class__))
        if not return_value:
            return response
        return return_value

    def _call_callback(self, environ):
        try:
            rule, kwargs = self.router.match(environ)
            method = environ.get("REQUEST_METHOD", 'GET')
            if rule.url_rule.endswith('/'):
                if not environ['PATH_INFO'].endswith('/'):
                    return Redirect(environ['PATH_INFO'] + '/',
                                    status_code=307)
            callback = rule.get_callback(method)
            response = self._call_before_request()
            if not response:
                response = callback(**kwargs)
        except HTTPError as exc:
            response = self._handle_http_exc(exc)
        except Exception as exc:
            response = self._handle_app_exc(exc)
        response = self._build_response(response)
        return self._call_after_request(response)

    def _handle_app_exc(self, exc):
        if not self.config['DEBUG']:
            if hasattr(exc, 'code'):
                handler = self.error_code_handlers.get(exc.code)
            else:
                handler = self.error_handlers.get(exc.__class__)
            if handler:
                self.log_exception(exc)
                return handler(exc)
        exc = InternalServerError(code=500)
        return self._handle_http_exc(exc)

    def _handle_http_exc(self, exc):
        self.log_exception(exc)
        debug = self.config['DEBUG']
        if not debug:
            error_handler = self.error_code_handlers.get(exc.code)
            if error_handler:
                return error_handler(exc)
        if exc.code < 500:
            debug = False
        headers = exc.headers()
        resp = exc.get_response(debug=debug)
        return Response(resp, status_code=exc.code, headers=headers)
        # response = exc.response(debug=config['DEBUG'])

    def log_exception(self, exc):
        code = 0
        if hasattr(exc, 'code'):
            code = exc.code
        if code and code < 500:
            logger.debug('''[{exc}] {cls} {path} {code}'''.format(
                exc=exc,
                cls=exc.__class__.__name__,
                path=request.path,
                code=code))
        else:
            logger.exception('Error in path [%s]' % request.path)

    def _build_response(self, response):
        if isinstance(response, Response):
            return response
        if isinstance(response, (str, bytes)):
            return Response(response)
        if isinstance(response, dict):
            return JsonResponse(response)
        if isinstance(response, tuple):
            try:
                response, code = response
            except (ValueError, TypeError):
                raise TypeError('view return unknown response')
            response = self._build_response(response)
            response.status_code = code
            return response
        raise TypeError('view return unknown response type %s' %
                        response.__class__)

    def close_resources(self):
        request.close()

    def _get_response(self, environ):
        request.bind(environ)
        request.app = self
        with self.mount():
            self.session_cls.open()
            response = self._call_callback(environ)
            self.session_cls.save(response)
            self.close_resources()
        return response

    def __call__(self, environ, start_response):

        response = self._get_response(environ)
        response.start_response(environ, start_response)
        return response
