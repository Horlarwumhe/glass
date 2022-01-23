from urllib.parse import unquote

import pytest
from glass import GlassApp, url_for

app = GlassApp()


@app.route('/reset/<username>/<int:id>/<code>')
def reset_password(username, id, code):
    return "Hello"


@app.route('/u/<user_id>/<token>/')
def confirm_reg(user_id, token):
    return "hello"


@app.route('/u/login')
def login():
    return "hello"


@app.route('/<id>/<title>')
def get_post(id, title):
    return "hello"


def test_url_for_no_servername():
    # no server name
    with app.mount():
        path = url_for('reset_password',
                       id=1,
                       code='somecode',
                       username='glass',
                       _scheme='https')
        assert path == '/reset/glass/1/somecode'
        assert path != '/reset/glass/1/somecode/'  #end slash

    with app.mount():
        # with query string /a/b/c?d=1&e=2
        path = url_for('reset_password',
                       id=1,
                       code='abcd',
                       username='admin',
                       sent="abc",
                       sort='yes')
        path, query_string = path.split('?', 1)
        assert 'sent=abc' in query_string
        assert 'sort=yes' in query_string
        assert '&' in query_string
        assert path == '/reset/admin/1/abcd'


def test_url_for_with_servername():
    app.config['SERVER_NAME'] = 'http://glass.Horlarwumhe.me'
    with app.mount():
        path = url_for('reset_password',
                       id=1,
                       code='somecode',
                       username='glass')
        assert path == ('http://glass.Horlarwumhe.me/reset/glass/1/somecode')
        assert path != ('http://glass.Horlarwumhe.me/reset/glass/1/somecode/')
        #end slash
    # https
    app.config['SERVER_NAME'] = 'https://glass.Horlarwumhe.me'
    with app.mount():
        path = url_for('reset_password',
                       id=1,
                       code='somecode',
                       username='glass')
        assert path == ('https://glass.Horlarwumhe.me/reset/glass/1/somecode')
        assert path != ('https://glass.Horlarwumhe.me/reset/glass/1/somecode/')

    # no scheme
    app.config['SERVER_NAME'] = 'glass.Horlarwumhe.me'
    with app.mount():
        path = url_for('login')
        assert path == 'http://glass.Horlarwumhe.me/u/login'


def test_url_for_with_query_string():
    app.config['SERVER_NAME'] = 'https://glass.Horlarwumhe.me'
    with app.mount():
        # path with query string /a/b/?c=3&q=8
        path = url_for(
            'reset_password',
            id=1,
            username='user',
            code='usercode',
            time='1234',
            opt='value',
        )
        path, query = path.split('?', 1)
        assert 'time=1234' in query
        assert 'opt=value' in query
        assert path == ('https://glass.Horlarwumhe.me/reset/user/1/usercode')


def test_url_for_with_scheme():
    app.config['SERVER_NAME'] = 'https://blog.Horlarwumhe.me'
    with app.mount():
        assert url_for('login') == ('https://blog.Horlarwumhe.me/u/login')
        path = url_for('login', redirect_to='/u/profile')
        assert unquote(path) == (
            'https://blog.Horlarwumhe.me/u/login?redirect_to=/u/profile')
        # change scheme
        path = url_for('login', _scheme='http')
        assert path == 'http://blog.Horlarwumhe.me/u/login'

        path = url_for('login', _scheme='https')
        assert path == 'https://blog.Horlarwumhe.me/u/login'

        #url fragment
        # https://example.com/path/#target
        path = url_for('login', _fragment='loginForm')

        assert path == 'https://blog.Horlarwumhe.me/u/login#loginForm'


def test_all():
    app.config['SERVER_NAME'] = ''
    with app.mount():
        path = url_for('get_post',
                       id=3,
                       title='post-title',
                       sort='true',
                       view='mobile',
                       _fragment='postHeader')
        full_path = '/3/post-title?sort=true&view=mobile#postHeader'
        assert path == full_path
        path, query_string = path.split('?', 1)
        assert 'sort=true' in query_string
        assert 'view=mobile' in query_string

        app.config['SERVER_NAME'] = 'https://blog.Horlarwumhe.me'

        path = url_for('get_post',
                       id=3,
                       title='post-title',
                       sort='true',
                       view='mobile',
                       _fragment='postHeader')
        path, query_string = path.split('?', 1)
        assert path == 'https://blog.Horlarwumhe.me/3/post-title'
        assert query_string == 'sort=true&view=mobile#postHeader'


def test_not_found_view():
    with app.mount():
        with pytest.raises(LookupError):
            url_for('logout')


def test_missing_args():
    with app.mount():
        with pytest.raises(TypeError):
            # missing <title> argument
            url_for('get_post', id=54)


def test_url_for_in_tags():
    s = '''
    {% url_for "url_view" _scheme="http" _target="target"|upper|url param1="value1" param2=param.meth %}
    '''
    from glass.templating import AppTemplateEnviron

    from glass import GlassApp
    app = GlassApp()

    env = app.template_env
    template = env.from_string(s)
    template.compile()
    nodelist = template.nodelist
    node = url_for_node = nodelist.nodelist[0]
    var_node = node.view_name
    assert var_node.var_name == '"url_view"'
    view_name = var_node.eval({})
    assert view_name == 'url_view'
    url_for_kwargs = list(node.view_kwargs.keys())
    url_for_values = list((v.var_name for v in node.view_kwargs.values()))
    assert url_for_kwargs == ['_scheme', '_target', 'param1', 'param2']
    assert url_for_values == ['"http"', '"target"', '"value1"', 'param.meth']
    func = node.view_kwargs['_target'].funcs
    assert func == ['upper', 'url']
