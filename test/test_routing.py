import sys

import pytest
from glass.exception import HTTP404
from glass.routing import Router, Rule

environ = {}


def test_route():
    rule1 = Rule('/u/<user>/profile/')
    rule2 = Rule('/login/user/')
    rule3 = Rule('/u/<int:user>/add/')
    router = Router()
    router.add(rule1)
    router.add(rule2)
    router.add(rule3)
    environ['PATH_INFO'] = '/u/horlar/profile/'
    rule, kwargs = router.match(environ)
    assert rule is rule1
    assert kwargs == {'user': 'horlar'}
    environ['PATH_INFO'] = '/login/user/'
    rule, kwargs = router.match(environ)
    assert rule is rule2
    assert kwargs == {}
    with pytest.raises(HTTP404):
        environ['PATH_INFO'] = '/user/login/'
        router.match(environ)
    environ['PATH_INFO'] = '/u/90/add'
    rule, kwargs = router.match(environ)
    assert rule is rule3
    assert kwargs == {'user': 90}


def test_optional_params():
    r = '/settings/<name>/<value>?'
    # <value> is optional
    rule1 = Rule(r)
    router = Router()
    router.add(rule1)
    environ['PATH_INFO'] = '/settings/security/auth'
    rule, kwargs = router.match(environ)
    assert rule is rule1
    assert kwargs == {'name':'security','value':'auth'}
    environ['PATH_INFO'] = '/settings/security'
    rule, kwargs = router.match(environ)
    assert rule is rule1
    assert kwargs == {'name':'security','value':''}

    # with end slash

    r = '/settings/<name>/<value>?/'
    # <value> is optional
    rule1 = Rule(r)
    router = Router()
    router.add(rule1)
    environ['PATH_INFO'] = '/settings/security/auth/'
    rule, kwargs = router.match(environ)
    assert rule is rule1
    assert kwargs == {'name':'security','value':'auth'}
    environ['PATH_INFO'] = '/settings/security'
    rule, kwargs = router.match(environ)
    assert rule is rule1
    assert kwargs == {'name':'security','value':''}

    param = rule1.params['value']
    assert param.optional
    param = rule1.params['name']
    assert not param.optional

    r = '/settings/<name>?/<int:value>?/'
    # <value> and <name>  optional
    rule1 = Rule(r)
    router = Router()
    router.add(rule1)
    environ['PATH_INFO'] = '/settings/'
    rule, kwargs = router.match(environ)
    assert rule is rule1
    assert kwargs == {'name':'','value':None}

    r = '/settings/<name>?/global'
    # <name>  optional
    rule1 = Rule(r)
    router = Router()
    router.add(rule1)
    environ['PATH_INFO'] = '/settings/global'
    rule, kwargs = router.match(environ)
    assert rule is rule1
    assert kwargs == {'name':''}
