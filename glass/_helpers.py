import threading

from .utils import _thread_local


class AppStack:
    def __init__(self):
        self.local = threading.local()

    def push(self, obj):
        if not hasattr(self.local, 'stack'):
            self.local.stack = []
        self.local.stack.append(obj)

    def pop(self):
        return self.local.stack.pop()

    def top(self):
        try:
            return self.local.stack[-1]
        except (AttributeError, IndexError):
            return None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.pop()
        # app.unmount()


class App:
    def __enter__(self):
        return self._get_current_app().__enter__

    def __exit__(self,*args):
        return self._get_current_app().__exit__(*args)

    def __getattr__(self, attr):
        return getattr(self._get_current_app(), attr)

    def __setattr__(self, x, y):
        self._get_current_app().__setattr__(x, y)

    def __bool__(self):
        try:
            return bool(self._get_current_app())
        except RuntimeError:
            return False

    def _get_current_app(self):
        app = app_stack.top()
        if app is None:
            raise RuntimeError('Working outside app '
                               "This means you are trying to use function "
                               "that requires active application. "
                               "Use use app.mount() to solve this.")
        return app


def flash(message, category=None):
    import glass.sessions as _session
    flashes = _session.session.get('__flash__', None)
    if not flashes:
        flashes = _session.session['__flash__'] = []
    flashes.append(message)


def messages():
    #This is depreciated.
    import glass.sessions as _session
    msgs = _session.session.get('__flash__', None)
    if msgs is None:
        return 
    for msg in msgs:
        yield msg
    _session.session.pop('__flash__')
    msgs.clear()


get_session_messages = flash_messages = messages

app_stack = AppStack()

current_app = App()
