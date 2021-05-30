
class App:
    def __getattr__(self, name):
        from glass.requests import request
        app = getattr(request, 'app', None)
        if app:
            return getattr(app, name)
current_app = App()
