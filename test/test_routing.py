import sys

import pytest

from glass.routing import Rule, Router
from glass.exception import HTTP404

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
