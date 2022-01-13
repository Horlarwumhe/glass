import logging
import sys
import traceback

from glass import http

from . import highlight

ERROR_TEMPLATE = '''
<title>{code} {title}</title>
<h1>{title}</h1>
<p>{description}</p>
'''
logger = logging.getLogger('glass.app')


class HTTPError(Exception):
    code = 500
    description = "Internal Server Error"

    def __init__(self, description='', code=None):

        self.description = description or self.description
        self.code = code or self.code
        super().__init__(self.description)

    def get_response(self, debug=False):
        if debug and None not in sys.exc_info():
            return self._format_tb(traceback.format_exc())

        return self._format_response()

    def _format_response(self):
        title = http.HTTP_STATUS_CODES.get(self.code, "Error")
        response = ERROR_TEMPLATE.format(code=self.code,
                                         title=title,
                                         description=self.description)
        return response

    def headers(self):
        header = [('Content-Type', 'text/html; charset=utf-8')]
        return header

    def _format_tb(self, tb):
        html = ['<html><body> <h1> Server Error</h1>']
        try:
            html.append(highlight.highlight(tb, 'python'))
        except Exception as e:
            logger.info('Failed to highlight traceback [%s]' % e)
            html.append(tb)
        html.append('''
        <h3>Note: You are seeing this traceback because
        <b>Debug</b> is set to True.</h3>''')
        html.append('</body></html>')
        return ''.join(html)


class HTTP404(HTTPError):

    code = 404
    description = 'The requested url not found on this server'


class MethodNotAllow(HTTPError):
    code = 405
    description = 'The method not allow for the requested path'


class InternalServerError(HTTPError):
    code = 500
    description = """
    Internal Server Error. An error occurs
    while processing request
    """


class BadRequest(HTTPError):
    code = 403
    description = '''Bad Request'''


class RequestTooLarge(HTTPError):
    code = 413
    description = 'Payload Too Large'
