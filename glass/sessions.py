import base64
import hashlib
import logging
import pickle

from glass._helpers import current_app as app
from glass.requests import request
from glass.utils import _thread_local

log = logging.getLogger('glass.app')


def _get_session_cookie_config():
    cookie_config = {}
    domain = app.config['SESSION_COOKIE_DOMAIN']
    if domain:
        cookie_config['Domain'] = domain
    cookie_config['Path'] = app.config['SESSION_COOKIE_PATH'] or '/'
    expire = app.config['SESSION_COOKIE_EXPIRE']
    if expire:
        cookie_config['Expires'] = expire
    max_age = app.config['SESSION_COOKIE_MAXAGE']
    if max_age:
        cookie_config['Max-Age'] = max_age
    httponly = app.config['SESSION_COOKIE_HTTPONLY']
    if httponly is True:
        # only accept True or False
        cookie_config['HttpOnly'] = True
    secure = app.config['SESSION_COOKIE_SECURE']
    if secure is True:
        # only accept True or False
        cookie_config['Secure'] = True
    # name = app.config['SESSION_COOKIE_NAME']
    same_site = app.config['SESSION_COOKIE_SAMESITE']
    if same_site:
        cookie_config['SameSite'] = same_site
    return cookie_config


def encode_session(data, key=b'session-key'):
    """Encode current session data and sign it.
    This generate string to be used as cookie

    :param data: ``dict``, current session data
    :param key: ``str``, app.secret-key
    :returns: ``str``.

    """
    app_key = app.config['SECRET_KEY']
    if not app_key:
        log.warning('You used session without secret key set'
                    ' consider setting secret key')
    key = key.encode()
    data = base64.b64encode(pickle.dumps(data))
    hash_value = hashlib.sha1(data + key).hexdigest()
    hash_value = hash_value[10:30]
    return '%s.%s' % (hash_value, data.decode())


def decode_session(string, key='session-key'):
    """Get current session data from session cookie.
    Returns empty dict if there is no cookie or
    the cookie verification failed.
    """
    # key = app.config['SECRETE_KEY'] or key
    key = key.encode()
    try:
        hash_value, data = string.split('.', 1)
    except ValueError:
        return None
    real_hash = hashlib.sha1(data.encode() + key).hexdigest()[10:30]
    if real_hash != hash_value:
        # the cookie has been tampered with
        return None
    data = base64.b64decode(data)
    return pickle.loads(data)


class Session(dict):
    """glass session object.
    ::

       from glass import session
       @app.route('/')
       def home():
        session['name'] = 'username'
    """

    session_data = _thread_local()
    modified = _thread_local()

    def __init__(self, data=None):
        self.data = data
        self.modified = False

    def get(self, key, default=None):
        """Get session data with its key,
           returns default if not found.
           Example::

             from glass import session
             @app.route('/')
             def home():
                name = session.get('name')
        """
        try:
            return self[key]
        except KeyError:
            return default

    def __setitem__(self, key, value):
        """Add item to the current session.
        Example::

           session['name'] = 'username'
        """
        self.modified = True
        self.session_data[key] = value


    def __getitem__(self, key):

        try:
            return self.session_data[key]
        except (KeyError, TypeError):
            raise KeyError(key)


    def __iter__(self):
        return iter(self.session_data)

    def bind(self, data):
        self.session_data = data
        self.modified = False

    def __len__(self):
        return len(self.session_data)


    def __contains__(self,key):
        return key in self.session_data

    def pop(self, key, default=None):
        """Remove item from session data and
        return the item value.


        Example::

           @app.route('/popname')
            def pop():
               name = session.pop('name')
               # if you dont need the value
               # session.pop('name')
               return 'hello'
        """
        self.modified = True
        try:
            return self.session_data.pop(key)
        except KeyError:
            return default

    def __delitem__(self, item):
        self.modified = True
        self.pop(item)

    def clear(self):
        """Clear current session data.
        ::

            @app.route('/clear')
            def clear():
                session.clear()
                return 'hello'
        """
        self.modified = True
        self.session_data.clear()


class SessionManager:
    salt = 'session-salt-'

    def open(self):
        key = app.config['SECRET_KEY']
        name = app.config['SESSION_COOKIE_NAME']
        cookie = request.cookies.get(name)
        data = {}
        if cookie:
            data = decode_session(cookie, key) or {}
        session.bind(data)

    def save(self, response=None):
        # TODO: add Secure and SameSite
        key = app.config['SECRET_KEY']
        cookie_config = _get_session_cookie_config()
        data = session.session_data
        name = app.config['SESSION_COOKIE_NAME']
        if not data:
            if not session.modified:
                return
            #TODO: add path,domain to delete_cookie
            response.delete_cookie(name, **cookie_config)
            return
        cookie = encode_session(data, key)
        response.set_cookie(name, cookie, **cookie_config)


session = Session()
