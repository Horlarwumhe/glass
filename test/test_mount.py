from glass import GlassApp
from glass import current_app
from glass import render_string,render_template
from glass import request

import pytest

app = GlassApp()


def test_mount_error():
    with pytest.raises(RuntimeError):
        render_string("Hello {{name}}", name='glass')

    with pytest.raises(RuntimeError):
        current_app.config.get("KEY")

    with pytest.raises(RuntimeError):
        host = request.host

    with pytest.raises(RuntimeError):
        render_template('index.html')


def test_mount_success():
    with app.mount():
        assert bool(current_app) is True
        assert app.config is current_app.config

    assert bool(current_app) is False
    with app.mount():
        result = "Hello glass"
        assert render_string("Hello {{name}}", name='glass') == result
    with app.mount():
        with pytest.raises(OSError):
            # template not found
            render_template('template.html')
    with app.mount():
        # this should raise an error.
        # request object is not available.
        # though the app is mouted, but environ argument is not provided.
        with pytest.raises(RuntimeError):
            host = request.host

    environ = {}
    environ['HTTP_USER_AGENT'] = 'curl'
    with app.mount(environ):
        assert request.user_agent == 'curl'
