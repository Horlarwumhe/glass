import io
import json
import mimetypes
import os
from datetime import datetime
from email.utils import parsedate_tz
from glass import http, utils
from glass.cookie import HTTPCookie
from glass.types import Header
from glass.sessions import session


class BaseResponse:
    ''' Base Response class.
    This class is not returned directly, but it is subclassed
    by other class. Use subclasess instead.

    Use :class:`glass.response.Response` or its subclasses

    :param content_type: response header `Content-Type`
    :param status_code: response http status code
    :param charset: content-type charset, default utf-8
    :param headers: ``dict`` or ``list`` of tuples, response headers
    '''
    status_code = 200
    charset = 'utf-8'
    content_type = 'text/html'

    def __init__(self,
                 content_type='',
                 charset='',
                 status_code=None,
                 headers=None):
        if status_code:
            self.status_code = status_code
        self.cookies = HTTPCookie()
        self.headers = Header()
        self.charset = charset or self.charset
        if headers:
            if isinstance(headers, dict):
                headers = headers.items()
            for name, value in headers:
                self.set_header(name, value)
        header_content_type = self.headers.get("Content-Type")
        if not header_content_type:
            self.headers['Content-Type'] = content_type \
            or self.content_type + '; charset=%s' %self.charset

    def set_cookie(self, name, value, **kw):
        """Add cookie to the response that will be
        sent to browser

        :param name: cookie name
        :param value: cookie value
        :param kw: optional keywords argument

        Example::

           @app.route('/')
           def home():
             resp = Response('hello')
             resp.set_cookie('name',value)
             resp.set_cookie('name1',value,
             expires='',max_age=0,httponly=True,
             secure=False,samesite='lax')
             # check mozilla for details about
             # the keywords argument

        """
        kw['Path'] = kw.get('path') or kw.get('Path') or '/'
        kw['HttpOnly'] = kw.get('httponly') or kw.get('HttpOnly', False)
        self.cookies.add_cookie(name, value, **kw)

    def delete_cookie(self, key, **kw):
        """Delete cookie previously sent to server

        Example::

          resp = Response('hello')
          resp.delete_cookie('name',path='/',domain='domain')

        """
        kw['max_age'] = 0
        self.set_cookie(key, "", **kw)

    def set_header(self, name, value, **kwargs):
        """Add header to the response headers"""

        self.headers.add(name, value, **kwargs)

    def start_response(self, environ, start_response):
        # self.set_headers()
        headers = list(self.headers.items())
        for cookie in self.cookies:
            headers.append(cookie.as_wsgi())
        reason = http.HTTP_STATUS_CODES.get(self.status_code, 'Unknown')
        # headers.append(self.default_headers())
        start_response("%s %s" % (self.status_code, reason), headers)

    # def set_headers(self, **headers):
    #     self.headers.update(headers)

    def __iter__(self):

        if isinstance(self.content, (str, bytes)):
            return map(utils.encode, (self.content, ))
        return map(utils.encode, iter(self.content))

    def close(self):
        if hasattr(self.content, 'close'):
            self.content.close()


class Response(BaseResponse):
    """
    Main response object,

    :param content: ``str`` or ``bytes`` or any object with ``iter``

    see :class:`glass.response.BaseResponse` for
    the parameters

    ::

           resp = Response('hello',
           headers={"key":'value'},status_code=200
             )

    """
    def __init__(self, content, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if isinstance(content, (str, bytes)):
            content = utils.encode(content)
            self.headers['Content-Length'] = len(content)
        self.content = content


class JsonResponse(Response):
    """Return json object as response.
    see :class:`glass.response.BaseResponse` for
    the parameters and methods
    ::
       @app.route('/')
       def json()
           data  = {'name':'username','email':'usermail@mail.com'}
           return JsonResponse(data)
     """
    def __init__(self, content, *args, **kwargs):
        content = json.dumps(content)
        super().__init__(content, *args, **kwargs)
        self.headers[
            'Content-Type'] = 'application/json; charset=%s' % self.charset


class Redirect(Response):
    """Issue redirect response to the browser

    :param location: redirect location
    see :class:`glass.response.BaseResponse` for
    the parameters and methods

    """
    status_code = 302

    def __init__(self, location, *args, content='', **kwargs):
        super().__init__(content, *args, **kwargs)
        self.headers['Location'] = location
        self.content = content  # TODO : ADD redirect message


class FileResponse(Response):
    """Stream file or file object to the browser.
    Use this class to send file as response
    Example::

       @app.route('/')
       def send_file():
          return FileResponse('/path/to/file.jpg')

    """
    max_size = 10000000
    max_read = 4028

    def __init__(self, file, *args, **kwargs):
        if isinstance(file, (str, bytes)):
            self.filename = file
            # The file will close once the response is
            # sent
            file = open(file, 'rb')
        elif isinstance(file, io.IOBase):
            self.filename = file.name
        headers = kwargs.get('headers', {})
        if isinstance(headers, list):
            headers = dict(headers)
        content_type = kwargs.get("content_type")
        if content_type:
            headers['Content-Type'] = content_type
        headers = self.add_headers(headers)
        kwargs['headers'] = headers
        super().__init__(file, *args, **kwargs)

    def add_headers(self, headers):
        #  Content-Disposition: inline;
        #  filename="bootstrap.min.css"
        size = headers.get("Content-Length")
        if not size:
            headers["Content-Length"] = os.stat(self.filename).st_size
        content_type = headers.get("Content-Type")
        if not content_type:
            mime_type, encoding = mimetypes.guess_type(self.filename)
            if mime_type:
                content_type = mime_type
                if encoding:
                    content_type = mime_type + '; charset=' % encoding
            else:
                content_type = 'application/octet-stream'
            headers['Content-Type'] = content_type
        return headers


class StaticResponse(FileResponse):
    pass


def send_static(filename, app, request):
    """Send static file (css,jss,images,...)
    request is made as argument to this function,
    instead of importing, to avoid circular import

    """
    if filename.startswith('../')\
       or os.path.isabs(filename)\
       or filename == '..':
        return Response('Not Found', status_code=404)

    if_modified = request.headers.get("If-Modified-Since")
    static = app.config['STATIC_FOLDER']
    if not static:
        static = os.path.join(os.getcwd(), 'static')
    file = os.path.abspath(os.path.join(static, filename))
    if not os.path.exists(file)\
       or not os.path.isfile(file):
        return Response('Not Found', status_code=404)
    try:
        mtime = os.stat(file).st_mtime
    except OSError:
        return Response('Not Found', status_code=404)
    mtime = datetime.utcfromtimestamp(mtime)
    if if_modified:
        time_tuple = parsedate_tz(if_modified)
        if time_tuple:
            if_modified = datetime(*time_tuple[:6])
            if not mtime > if_modified:
                return Response('', status_code=304)
    last_modified = mtime.strftime('%a, %d %b %Y %H:%M:%S GMT')
    headers = {
        'Cache-Control': 'public, max-age=3153600',
        'Last-Modified': last_modified,
    }
    return FileResponse(file, headers=headers)


def redirect(location, code=302, response=''):
    return Redirect(location, content=response, status_code=code)


def flash(message):
    flashes = session.get('__flash__', None)
    if not flashes:
        flashes = session['__flash__'] = []
    flashes.append(message)


def messages():
    msgs = session.get('__flash__', [])
    r = []
    for msg in msgs:
        r.append(msg)
        msgs.pop(0)
    return r


flash_messages = messages
