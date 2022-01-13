import io
import json
import logging
import os
import urllib.parse
from http.cookies import SimpleCookie

import multipart
from glass._helpers import current_app
from glass.exception import BadRequest, RequestTooLarge
from glass.types import WSGIHeader
from glass.utils import _thread_local, cached_property
from multipart import parse_form_data

logger = logging.getLogger('glass.app')


def _parse_form_data_(environ):

    max_length = current_app.config['MAX_CONTENT_LENGTH']
    if max_length and request.content_length > int(max_length):
        raise RequestTooLarge()
    try:
        form, files = parse_form_data(environ, strict=True)
    except multipart.MultipartError as e:
        raise BadRequest(e)
    return form, files


class Request:
    """This implement HTTP request to access
    incoming request data.

    ::

      from glass import request

    """
    __storage__ = _thread_local()
    environ = _thread_local()

    def __init__(self, environ=None):
        self.environ = environ

    @cached_property()
    def path(self):
        """HTTP request path"""
        return self.environ.get("PATH_INFO", '')

    @cached_property()
    def cookies(self):
        """A ``dict`` object of cookies sent to
        the server::

          @app.route('/')
          def home():
            cookie = request.cookies.get('name')
            do_something(cookie)
            return 'hello'

        """
        cookie = SimpleCookie(self.environ.get("HTTP_COOKIE", ''))
        cookie = cookie.values()
        cookie_dict = {}
        for c in cookie:
            cookie_dict[c.key] = c.value
        return cookie_dict

    @cached_property()
    def query(self):
        """URL query string, values after
        ``?`` in request path. ``/users/list/?sort=True&type=name``

        ::

           sort = request.args.get('sort')
           type = request.args.get('type')
           # request.args and request.query are same, use anyone.
        """

        return dict(
            urllib.parse.parse_qsl(self.environ.get("QUERY_STRING", '')))

    args = query

    @cached_property()
    def headers(self):
        """A dict-like object request HTTP Headers
        Example::

             content_type = request.headers.get("Content-Type")

        """
        return WSGIHeader(self.environ)

    @property
    def host(self):
        """Host field in the request header"""
        return self.environ.get("HTTP_HOST", '')

    def get_json(self):
        """Return data sent as json. If content_type is not
        ``application/json`` this returns ``None``

        """
        if not "application/json" in self.content_type:
            return None
        body = self.get_data()
        return json.loads(body)

    def get_data(self):
        """Returns data sent to server as ``bytes``.
        It is good to check :attr:`content_length` with
        ``request.content_length`` before calling this method as
        content_length allows you to know size of the data
        and to avoid reading a very large data at once.

        When this method is called,
        data stream sent to the server
        will be consumed,
        :attr:`request.post` and :attr:`request.files` will
        return empty dict if they are called
        after this method is called.

        You can read the data sent in small chunck with :attr:`request.stream`.
        ::

          size = request.content_length
          if size > 50_000_000: # 50MB
             # probably, you dont want read data
             # of this size at once.
             # use request.stream here
        """
        if hasattr(self, 'raw_data'):
            return self.raw_data.getvalue()
        size = self.environ.get('CONTENT_LENGTH')
        if size:
            size = int(size)
        data = self.environ['wsgi.input'].read(size)
        self.raw_data = io.BytesIO(data)
        return data

    @property
    def method(self):
        """HTTP request method"""
        #FIXME: HTTP_REQUEST_METHOD or REQUEST_METHOD
        return self.environ.get("REQUEST_METHOD", '').upper()

    @property
    def user_agent(self):
        return self.environ.get('HTTP_USER_AGENT', '')

    @property
    def stream(self):
        """Body of the request

          ::

           # read 1024 bytes from request data
           data = request.stream.read(1024)
           # read everything at once
           data = request.stream.read()
        """
        return self.environ['wsgi.input']

    @property
    def content_type(self):
        """Request content_type"""
        return self.environ.get("CONTENT_TYPE", '')

    @property
    def content_length(self):
        """Request content length"""
        return int(self.environ.get("CONTENT_LENGTH", 0))

    def __setattr__(self, key, name):
        if key in ("environ", '__storage__'):
            super().__setattr__(key, name)
        else:
            self.__storage__[key] = name

    def __getattr__(self, name):
        if name in object.__dict__:
            return object.__dict__[name]
        if name in self.__storage__:
            value = self.__storage__[name]
            if hasattr(value, 'var'):
                return value.var
            return value
        raise AttributeError('Atrribute not defined "%s"' % name)

    def close(self):
        try:
            self.raw_data.close()
        except AttributeError:
            pass
        self.__storage__.clear()

    @cached_property()
    def files(self):
        """A dict-like object of files
        posted to the server.::

           user_pics = request.files.get('profile_pics')
           if user_pics:
               # save the file
               filename = user_pics.filename
               user_pics.save_as('/somepath')

        .. note::
            This only works if the :attr:`request.method`
            is POST, PUT or PATCH, and content_type is
            multipart/form-data.
            If not , it returns empty dict
            object

        """
        form, files = _parse_form_data_(self.environ)
        self.__storage__['post'] = form
        return files

    @cached_property()
    def post(self):
        """A dict-like object of post/put
        data. ::

            <input type='text' name='username'>
            <input type='password' name='password'>

        Get the values with::

                request.post.get('username')
                request.post.get('password')
        """
        form, files = _parse_form_data_(self.environ)
        self.__storage__['files'] = files
        return form

    def bind(self, env):
        '''Bind request to  wsgi environ
        '''
        self.environ = env
        self.__storage__ = {}


request = Request()
