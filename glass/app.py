import logging
import os

from glass.sessions import SessionManager
from glass.config import Config
from glass.exception import (HTTPError, InternalServerError)
from glass.requests import request
from glass.response import JsonResponse, Response, Redirect, send_static
from glass.routing import Router, Rule
from glass.templating import AppTemplateEnviron, AppTemplateLoader, Cache
from glass.templating import JinjaEnvironment, JinjaFileLoader
from glass.utils import cached_property

logger = logging.getLogger('glass.app')
stream = logging.StreamHandler()
stream.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s: %(message)s',
                              datefmt='%d/%m/%Y %H:%M:%S %p')
stream.setFormatter(formatter)
logger.addHandler(stream)
logger.setLevel(logging.DEBUG)


class GlassApp:

    def __init__(self, **kwargs):

        self.session_cls = SessionManager()
        self.config = Config()
        self.router = Router()
        self.error_code_handlers = {}
        self.error_handlers = {}
        self.before_request_funcs = []
        self.after_request_funcs = []
        static_url = self.config['STATIC_URL'] or 'static'
        static_url = static_url.strip('/')
        self.add_url_rule('/%s/<path:filename>' % static_url, self.send_static)

    @cached_property()
    def template_env(self):
        env = AppTemplateEnviron(self, loader=AppTemplateLoader(),
                                 cache=self.template_cache)
        return env

    @cached_property()
    def jinja_env(self):
        path = self.config['TEMPLATES_FOLDER']
        if not path:
            path = os.path.abspath(os.path.join(os.getcwd(), 'templates'))
        env = JinjaEnvironment(self,loader=JinjaFileLoader(path))
        return env

    def send_static(self, filename):
        return send_static(filename, self, request)

    @cached_property()
    def template_cache(self):
        return Cache()

    def route(self, url_rule, methods='GET', **kwargs):
        def decorator(func):
            req_method = methods
            if not req_method:
                req_method = ["GET"]
            if isinstance(req_method, str):
                req_method = [req_method]
            req_method = list(map(str.upper, req_method))
            rule = Rule(url_rule, func, req_method, **kwargs)
            self.router.add(rule)
            return func

        return decorator

    def add_url_rule(self, rule, func, methods=None):
        return self.route(rule, methods)(func)

    def get(self, url_rule, **kwargs):
        return self.route(url_rule, 'GET', **kwargs)

    def post(self, url_rule, **kwargs):
        return self.route(url_rule, 'POST', **kwargs)

    def before_request(self, func):
        self.before_request_funcs.append(func)
        return func

    def after_request(self, func):
        self.after_request_funcs.append(func)
        return func

    def error(self, error):
        # TODO: return in the decorator
        def decorator(func):
            if isinstance(error, int):
                self.error_code_handlers[error] = func
            else:
                self.error_handlers[error] = func
            return func

        return decorator

    def _call_before_request(self):
        for func in self.before_request_funcs:
            func()

    def _call_after_request(self, response):
        main_response = response
        response = None
        for func in self.after_request_funcs:
            response = func(response)
            if not isinstance(response, main_response.__class__):
                raise TypeError(
                    'after_request function should return %s not %s' %
                    (main_response.__class__, response.__class__))
        if not response:
            return main_response
        return response

    def _call_callback(self, environ):
        try:
            rule, kwargs = self.router.match(environ)
            method = environ.get("REQUEST_METHOD", 'GET')
            if rule.url_rule.endswith('/'):
                if not environ['PATH_INFO'].endswith('/'):
                    return Redirect(environ['PATH_INFO'] + '/')
            callback = rule.get_callback(method)
            self._call_before_request()
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
                cls=exc.__class__.__name__, path=request.path, code=code))
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

    def _get_response(self, environ):
        request.bind(environ)
        request.app = self
        self.session_cls.open()
        response = self._call_callback(environ)
        self.session_cls.save(response)
        return response

    def __call__(self, environ, start_response):

        response = self._get_response(environ)
        response.start_response(environ, start_response)
        return response
