CHANGELOG
=============

v0.0.4
---------

There is no changes to this release. This release is same as v0.0.3. Released to fix a missing module on pypi release.

v0.0.3
----------


Newest changes to Glass v0.0.3 .

Template
~~~~~~~~~~

Fixed spaces quoted in string (``''`` or ``""``) not recognized.

::

 {% if name == '  admin  ' %}
  {% endif %}


Previously, the tag above would raise syntax error due to how glass splited tokens content. Tokens were splited with space which means quoted space(space in string " ") would also be splited.

Previously, the above tag would yield this.
::

  ('if', 'name', '==', "'", 'admin', "'")

The above will now yield,
::

  ("if", "name","==","'  admin  '")


This is now a valid template syntax;
::

   {% if text == 'hello word' %}
     hello word
    {% elif text == "text with space " %}
      text with space
    {% endif %}

Custom tags can use ``token.split_args`` to make use of this change.


::

  def tag_parser(parser):
    # {% if name == '  admin  ' %}
    token = parser.get_next_token()
    args = token.split_args()
    print(args)
	    #  ['name', '==', "'  admin  '"]

Added support for ``list`` indexing.

::

  items = ['item1','item2']
  render_template('test.html',items=items)

  # test.html
  {{items.0}} # items[0]

  {{items.1}} #items[1]



Routing
~~~~~~~~

Added :func:`url_for <glass.routing.url_for>` for url building.
::

  from glass import GlassApp, redirect, url_for,request

  app = GlassApp()

  @app.route('/u/login')
  def login():
	return "Hello"

  @app.route('/view')
  def view_name():
    user = request.user
    if not user:
      return redirect(url_for('login'))
    if not user.verify:
      path = url_for('reset_code',user=user.id,code=user.code)
      return redirect(path)

  @app.route('/r/<user>/<code>')
  def reset_code(user,code):
    return 'hello'

``url_for`` is also availble in the template.


::

	<a href='{% url_for "login" %}'>login</a>

	<a href={% url_for "reset_code" user=user.id code=user.code %}> reset</a>

Other changes.

:meth:`app.route <glass.app.GlassApp.route>` now takes optional argument ``view_name``. Which is used with ``url_for``.

::

  @app.route('/')
  def home()
    return "hello"


To build the url for ``home``, the function name is used.

::

	url_for('home')

using ``view_name``;

::

  @app.route('/',view_name='main')
  def home()
  return "hello"


::

  url_for('main')



Other Changes

1. Fix function not being called in the template if it is python builtin.
2. Pop session flash messages if it is empty.
3. includes bugs fix
