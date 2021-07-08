from argparse import Namespace

from boring.server import Server


class GlassServer(Server):
    def create_args(self):
        if self.args is None:
            self.args = CliArgument()

    def run_app(self, app, addr='127.0.0.1', port=8000, auto_reload=False):
        self.app = app
        self.create_args()
        self.args.bind = addr
        self.args.port = port
        self.args.reload = auto_reload
        self.start()

    def load_app(self):
        if not hasattr(self, 'app'):
            raise RuntimeError('Use app.run() to start app server')
        if self.app is None:
            raise RuntimeError('Use app.run() to start app server')
        return self.app


class CliArgument(Namespace):
    def __getattr__(self, attr):
        return False

    def __bool__(self):
        return False
