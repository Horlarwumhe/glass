Quickstart
====================
.. _mozilla: https://developer.mozilla.org/en/docs/web/HTTP/Cookies
.. _request: request.html
.. _template: template.html
.. _config: config.html
.. _boring: https://github.com/horlarwumhe/boring
.. _cheroot: https://cheroot.cherrypy.org
.. _gunicorn: https://gunicorn.org


This page shows introduction to Glass. The content of this page is short, as Glass is just micro-framework. The code examples are self explanatory and it is easy to understand.


.. toctree::
   config
   :maxdepth: 1
   :caption: contents:


On This Page ...

.. contents::
   :depth: 2
   :local:


Introduction
-----------------


First, install from pypi:

::

   $ pip install glass-web

You can clone it from github with git.

::

  $ git clone https://github.com/horlarwumhe/glass.git

  $ cd glass

  $ python setup.py install
  $ pip install -r requirements.txt


Your first code;

.. code:: python

   from glass import GlassApp

   app = GlassApp()

   @app.route('/')
   def home():
       return 'This is home page'


Starting The Server
---------------------
You can use any wsgi web server to start the app. `gunicorn <https://gunicorn.org>`_, `cheroot <https://cheroot.cherrypy.org>`_, or `boring <https://github.com/horlarwumhe/boring>`_.

::

      $ pip install boring

      $ boring first:app --reload

Assuming the source is saved as ``first.py``.

With `gunicorn <https://gunicorn.org>`_ ;

::

  $ gunicorn first:app --reload

.. note::

   To use builtin server, add ``app.run`` to your code.

::

    # file first.py
    from glass import GlassApp

    app = GlassApp()
    @app.route('/')
    def home():
       return "Hello"
    app.run()

::

  $ python first.py

check :meth:`app.run <glass.app.GlassApp.run>` for usage.

Routing
---------

.. code:: python

   from glass import GlassApp
   
   app = GlassApp()
   @app.route('/')
   def home():
       return 'This is home page'

.. code:: python

   from glass import GlassApp

   app = GlassApp()
   @app.route('/login/')
   def login():
       return 'This is login page'

   @app.get('/')
   def do_get():
       # for GET method
       return 'Hello'

   @app.post('/post/')
   def do_post():
       # for POST method
       return "Hello"

Using variable url rule.

.. code:: python

   @app.route('/<user>/')
   def test(user):
       return 'Hello %s'%user

   @app.route('/reset/<code>')
   def reset(code):
       # do_something_with(code)
       return 'Hello'

The url rule can take optional converter.

  - int
       ``<int:param>`` will match integer only [0-9]

  - str
       ``<str:name>`` will match match all except ``/`` and space.
  - path
       ``<path:file>`` will match all except space.
       Usually for files.



.. code:: python
     
     @app.route('/read/<int:post_id>')
     def read(post_id):
         assert isinstance(post_id,int)
         return 'Hello'

     @app.route('/view/<str:username>')
     def view(username):
        return username

     @app.route('/view/<path:file>')
     def read_file(file):
        return FileResponse(file)

    # /read/<int:post_id> will match /read/82
    # but not /read/fssj

.. note::

      - If the url rule doesn't end with slash e.g. ``'/post/<post_id>'``, this url ``/post/1/`` will return ``404 Not Found``, but ``/post/1`` will match.
      - If the url rule ends with slash e.g. ``/user/login/``, user using this ``/user/login`` will be redirected to the original url ``/user/login/``


By default, each url function allow ``GET`` request method. Glass will return ``405 Method Not Allowed`` if any other request method is used. You need to provide other methods to the view.

::


    from glass import request

    @app.route('/login/',methods=['GET','POST','PUT'])
    def login():
      if request.method == 'POST':
          do_something()
      elif request.method == 'PUT':
         do_other_thing()
      else:
          # GET method
          do()
      return 'Hello'

    @app.route('/delete/',methods=['GET',"DELETE"])
    def delete():
       if request.method == 'DELETE':
           do_delete()
       else:
          # GET 
          do_get()
       return "Hello"


Response
---------

Each function handling a url rule must return a valid response. The view can return the following valid responses.


Return ``str``;

.. code:: python

   @app.route('/')
   def home():
       return 'Hello'


Return response with status code;

.. code:: python

   @app.route('/')
   def home():
       return 'Hello',200

Return ``dict``.

If the view return dict, the response headers ``Content_Type`` will be set to ``application/json``
and the response dict will be converted to json.
  
.. code:: python

   @app.route('/')
   def home():
       return {'name':'username','id':2},200
       # returning code is optional

Response Object
-----------------
To have more control over the response e.g. setting headers, cookies, content_type, use :class:`~glass.response.Response` object.

.. code:: python

   from glass import Response
   from glass import GlassApp

   app = GlassApp()

   @app.route('/')
   def home():
       # set headers
       headers = {'header1':'value1','header2':'value2'}
       # or as list
       # headers = [('header1', 'value1'), ('header2', 'value2')]
       # set content_type
       content_type = 'text/plain'
       # set response code
       code = 200
       response = Response('Hello',headers=headers,
       content_type=content_type,status_code=code)
       return response


Return json

   Use :class:`glass.response.JsonResponse` to return response object as json.

::

    from glass.response import JsonResponse

    @app.route('/api/user/<int:user_id/')
    def get_user(user_id):
       user = get_user_from_db(user_id)
       data = {
       'name':user.name,
       'email':user.email
       }
       return JsonResponse(user)

``JsonResponse`` takes same arguments as ``Response``.

Redirect
-----------

To redirect users to another url, use :func:`~glass.response.redirect`.

::

   from glass import redirect
   from glass import session

   @app.route('/')
   def home():
      name = session.get('name')
      if not name:
          return redirect('/login')
      return "Hello %s"%name

   @app.route('/login',methods=['GET',"POST"])
   def login():
       name = request.post.get('name','')
       session['name'] = name
       return 'Hello'



Sending Files
---------------

::

    from glass.response import FileResponse

    @app.route('/file/<path:filename>')
    def send_file(filename):
        return FileResponse(filename)

Handling Errors
------------------

In case an exception occurs in the application, you can register a function to call when the error occurs.

The function can be registered using error code or exception class.


.. code:: python

    from glass import GlassApp, request

    app = GlassApp()
    @app.error(404)
    def not_found(error):
       r = 'The url %s not found'%request.path
       return r, 404

    @app.error(500)
    def internal_error(error):
       return 'Hoooops, Internal Error ', 500

Handling error with exception class.

.. code:: python

  # you must set DEBUG to False for this work
  app.config['DEBUG'] = False

  @app.error(NameError)
  def handle(exc):
     assert isinstance(exc,NameError)
     return 'Hoooops, that is NameError....'

  from somemodule.exceptions import FooError

  @app.error(FooError)
  def foo_handler(exc):
    return "FooError occurs"

  @app.error(Exception)
  def err_handler(exc):
    return "%s error occurs"%exc.__class__



App API
----------

:meth:`before_request <glass.app.GlassApp.before_request>`

Use this decorator to register function(s) to call before each app request. This function can be used to open db connection or load logged in user.

::

   from glass import GlassApp, request,session

   app = GlassApp()

   @app.route('/')
   def home():
     if request.user is None:
        user = 'Guest'
    else:
      user = request.user.username
    return 'Hello %s'%user

   @app.before_request
   def load_user():

      id = session.get('user_id')
      if id:
         user = get_user_from_db(id)
         request.user = user
      else:
        request.user = None
      # make sure set request.user = value
      # to avoid getting AttributeError in the
      # view function

If the any of the functions of ``.before_request`` returns response, the response will be used and the view function of the request url will not be called.

::

  @app.before_request
  def unavailable():
      return "The site is under development"

:meth:`after_request <glass.app.GlassApp.after_request>`

Use this decorator to register a fuction(s) to call after each request.

::

   @app.after_request
   def after(response):
     response.set_header('name','value')
     return response

The function takes one argument, :class:`~glass.response.Response` object and returns the response object.



Working With Cookies
-----------------------
You  can set  cookies and also get the cookies sent to the server. To set cookies, use :meth:`Response.set_cookie <glass.response.BaseResponse.set_cookie>` and :attr:`request.cookies <glass.requests.Request.cookies>` to get cookies sent to the server.

.. code:: python

   from glass import Response

   @app.route('/')
   def home():
       resp = Response('Hello')
       resp.set_cookie('cookie1','value1')
       resp.set_cookie('cookie2','value2')
       resp.set_cookie('cookie3','value3',
           max_age=989,domain='domain.com',
           path='/',httponly=False,secure=False)
       return resp

:meth:`~glass.response.BaseResponse.set_cookie` accepts the following keywords
  - expires (default to ``None``)
  - max_age  (default to ``None``)
  - path (default to '/')
  - httponly (default to ``False``)
  - secure (default to ``False``)
  - domain (default to ``None``)

Read more at `mozilla <https://developer.mozilla.org/en/docs/web/HTTP/Cookies>`_ for more details about these values.

Get the cookies sent to the server;

::

   from glass import request

   @app.route('/')
   def home():
       cookie = request.cookies.get('cookie_name')
       # do_something_with_cookie(cookie)
       return 'Hello'

:attr:`~glass.requests.Request.cookies` returns ``dict`` .

Remove cookie;

.. code:: python

     @app.route('/del')
     def clear():
        resp = Response('Hello')
        resp.delete_cookie('cookie_name')
        return resp

:meth:`~glass.response.BaseResponse.delete_cookie` accepts keywords as ``set_cookie``

Session
---------
The session object allows you to store information about a request. The data store in session are different for different requests.

To use session, you need to set app secret_key.

.. code:: python

    from glass import session,request
    from glass import GlassApp
    from glass import  redirect
    app = GlassApp()
    #
    app.config['SECRET_KEY'] = 'some secret'
    @app.route('/')
    def home():
       name = session.get('name')
       if not name:
          return 'Hello guest'
       return 'Hello %s <a href="/del">remove</a>'%name

    @app.route('/set',methods=['GET','POST'])
    def set_name():
       form = '''
           <form method='POST'>
             <input type='text' name='username'>
            <input type='submit'>
           </form>
        '''
       if request.method == 'POST':
         name = request.post.get('username')
         if name:
            session['name'] = name
            return redirect('/')
       return form

    @app.route('/del')
    def remove_name():
       session.pop('name')
       return redirect('/')

Session class is ``dict`` object, so all methods of ``dict`` are available.

.. note::
    Like flask, session data are stored in the cookie sent to the browser, unlike django which save session data inside database.

    The default method used to encode session data only guarantee the integrity of the cookie. Anyone can decode and see the content of the cookie,  but it can`t be modified, because the ``sha1`` hash of cookie is sent with it. If  an hacker modified the cookie, it will be imposible to recompute the hash value unless the hacker has access to the app ``secret key``.


You can write  your own session storage to manage session.

.. code:: python
    
    from glass import session
    from glass import current_app
    from glass import request

    class MySessionManager:

       # must define two methods, open() and save()

       def open(self):
         # session_cookie_name
         name = current_app.config["SESSION_COOKIE_NAME"]
         cookie = request.cookies.get(name)
         if cookie:
             # you implement this function
             # get the session data from where it is stored
             data = get_session_data(cookie)
             
               # data must be dict
               # bind the data to the current request
             session.bind(data)
         else:
             session.bind({})

       def save(self,response):
        # save current session data and get cookie
        # you implement this function
        cookie = save_data(session.session_data)
        name = current_app.config['SESSION_COOKIE_NAME']
        # you need to set cookies attributes
        # expires, max-age,httponly,secure,samesite
        #
        response.set_cookie(name,cookie,...)

      app = GlassApp()
      app.session_cls = MySessionManager()

.. note::
    Session data are ``threading.local`` instance. This make the data  thread safe on multi-thread web server.


Message Flashing
---------------------

::

   from glass import GlassApp, flash
   @app.route('/')
   def home():
      return render('index.html')

   @app.route('/form',method=['GET','POST']):
   def form():
    if request.method == 'POST':
       name = request.post.get('name')
       if len(name) < 10:
          flash('name too short')
       else:
         flash('Hello %s'%name)
    return render('form.html')

use ``get_flash_messages`` in the template

::

   # form.html

   {% for message in get_flash_messages %}
      <p> {{message}} </p>
   {% endfor %}
   <form method='POST'>
      <input type='text' name='name'>
      <button>go</button>
   <form>

Working With Request Data
----------------------------
Request object contains current request data. Such as request headers, method, cookies, HTML form data and files sent to the server.

HTML form;

::

    <form method='POST'>
       <input type='text' name='username'>
       <input type='password' name='password'>

    </form>

.. code:: python

   from glass import request
   @app.route('/home',methods=['GET','POST'])
   def home():
       if request.method == 'POST':
           name = request.post.get('username')
           return 'Hello %s'%name
       return 'this is home'

Working With Files
-----------------------
To upload files, dont forget to set ``enctype="multipart/form-data"`` in your html form.

::

   <form  enctype="multipart/form-data" method="POST">
      <input type='file' name='userpic'>
      <button> go</button>
    </form>

.. code:: python

    from glass import request
    @app.route('/home',methods=['GET','POST'])
    def home():
       if request.method == 'POST':
           file = request.files.get('userpic')
           # get the filename
           # name = file.filename
           if file:
               file.save_as('/location/on/filesytem')
       return 'Hello'

.. note::

    ``request`` is made as global object. Despite being global,the object is thread safe. The request relies on **WSGI** ``environ`` which is attached to the ``request`` with  ``threading.local``.

Read more on :class:`~glass.requests.Request` for other methods.


Configuration
-----------------

The configuration pattern used is similar to flask. All the config values are stored in dict.

Glass has some predefined configurations.
Read more at :doc:`configuration <config>`

.. code:: python

    app = GlassApp()

    class CONFIG:
      DEBUG = True
      KEY = 'value'
      DB_ENGINE = 'postgresql://user:password@localhost:5432/glass'

    app.config.from_object(CONFIG)

    # config from dict
    config = {'DEBUG':True,'KEY':'value'}
    app.config.from_dict(config)
    # config from json
    app.config.from_json('path/to/file.json')

    # the configurations can be accesed as
    app.config['DEBUG']
    app.config['KEY']



current app

   The current app object can accessed from anywhere.

::

  from glass import current_app
  # this only works with active http request
  def connect_db():
     db = current_app.config['DB_ENGINE']
     do_something(db)


Static Files
-----------------------

Glass will look for ``static`` folder in the current working to serve static files (css,js,images,...). You can set another directory to find static files.

::

      app = GlassApp()
      app.config['STATIC_FOLDER'] ='/path/to/files'

Like flask and django, default url for static files is ``/static/``.


.. _using-template:

Template
--------------
Glass comes with template engine. The docs here show how to use the template engine with Glass. The full docs is available in the template :doc:`documentation <template>`.

Template Quickstart
~~~~~~~~~~~~~~~~~~~~~~
The template syntax is very similar to django template.

.. code:: python

     from glass import render_template as render, import render_string
     from glass.response import Response
     @app.route('/')
     def home():
       return render('index.html',context={})

     @app.route('/<user>')
     def get_user(user):
         template = '''
            Hello <b> {{user}} </b>
        '''
         return render_string(template,user=user)
     @app.route('/login',methods=['GET',"POST"])
     def login():
        name = email = ''
        if request.method == 'POST':
            name = request.post.get('name')
            email = request.post.get('email')
        res = render('login.html',name=name,email=email)
        return Response(res)

.. code:: html

      <!-- file login.html -->
      <body>
        {% if name %}
          <div> Hello {{name}} </div>
          <div> Your email is {{email}} </div>
        {%else %}
           Hello guest
        {% endif %}
      <body>



Glass will look for  **templates** folder in the current working directory to load templates. You can set another directory for templates.

.. code:: python

   app = GlassApp()
   app.config['TEMPLATES_FOLDER'] = '/path/to/templates'

set multiple directories;

::

   app.config['TEMPLATES_FOLDER'] = ('/path/1/templates','/path/2/templates')


The template is configured with the following global variables. They can be accessed in the template.

   - request
       :class:`~glass.requests.Request`
   - session
       :class:`~glass.sessions.Session`
   - app
       *current app*


create global variable;

::

  from datetime import datetime as dt
  app.template_env.globals['date'] = dt.now

in the template file;
::

   <b> {{date}} </b>

Template Filters
~~~~~~~~~~~~~~~~~~
Filters are python function which modify variable in the template.

::

   <b> {{name|upper}} </b>

The filter here is ``upper`` which modifies the value of ``name``.

New template filter can be added to the template.

using decorator;

.. code:: python

   app = GlassApp()

   @app.template_env.filter('upper')
   def upper(value):
     return value.upper()

   @app.template_env.filter('secret')
   def secret(value):
      return value[:5]+'******'


manually register the filter;

::

   def secret(value):
      return  value[:5]+'******'

   app.template_env.filters['secret'] = secret



in the template file;

::

   <div> {{user.username|upper}}</div>
   <b> {{user.email|secret}}</b>



Tags
~~~~~~~~

Tags are like keywords. They are delimited by ``{%  %}``.


::

   <body> {% if user %} <b> Hello {{user}} {% endif %}
   </body>

::

   {% for post in posts %}
     <b> {{post.title }} </b>
       author {{post.author}}
    <a href='{{post.url}}'> read more </a>
   {% endfor %}

You can create custom tag to extends the bultin tags.
Once the created tag is registered, it will be available for use in the template.

::

   {% mytag arg1 arg2 %}

::

  {% myblocktag arg1 arg2 %}
     body
  {% end %}


Use decorator :attr:`~glass.app.GlassaApp.template_env` to register tags;

.. code:: python

    @app.template_env.tag('mytag')
    def tag_parser(parser):
      # parse the tag here

    @app.template_env.tag('myblocktag')
    def parse_tag(parser):
       # parse the tag here

or register manually;

::

   def tag_parser(parse):
      # parse the tag here

   app.template_env.tags['mytag'] = tag_parser


Read on how to parse custom tags in the template :ref:`documentation <custom-tag>`.

The template full docs is :doc:`available here <template>`.

Logging
~~~~~~~~~~~

Glass emits messages when incidents that need attention occur in the app. Such as unhandle exceptions.
By default, Glass writes logs to process stdout. You can log app messages to another stream using logging module.

::

    # this will log all app messages to file 'app.log'.
    import logging
    # the logger name used is 'glass.app'
    logger = logging.getLogger('glass.app')
    handler = logging.FileHandler('app.log')
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s:%(levelname)s: %(message)s', datefmt='%d/%m/%Y %H:%M:%S %p')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    app = GlassApp()
    @app.route('/')
    def home():
       return "Hello"

    @app.error(500)
    def error(e):
       logger.info('error occurs')
       return render('500.html')

check Python logging module `documentation <https://docs.python.org/3/library/logging.html>`_.


Using Jinja2
~~~~~~~~~~~~~

If you want to use jinja2 instead of the builtin template, there is wrapper method for jinja2 API.

::

   # configure your app to use jinja2
   app = GlassApp()
   app.config['TEMPLATE_BACKEND'] = 'jinja'

``app.jinja_env`` returns ``JinjaEnvironment`` which is subclass of ``jinja2.Environment``.  

Create a filter for jinja2

::

    @app.jinja_env.register_filter('split')
    def join(value,param=''):
      return value.split(param)

::

   {{name | split(param=',')}}

Global Value
---------------
::

  app.jinja_env.globals['name'] = 'global_value'




Working with database
-----------------------

Glass does not come with ORM. You can use sqlalchemy,ponyorm,sqlobject or use pure SQL using sqlite3 .


Full example
-----------------

.. code:: python

    from glass import GlassApp, request,session
    from glass.response import Redirect as redirect
    from glass.templating import render_template
    from glass import flash

    app = GlassApp()
    app.config['SECRET_KEY'] = 'some secrete'

    @app.route('/')
    def home():
       return render_template('index.html')

    @app.route('/logout')
    def logout():
       session.pop('user_id')
       return redirect('/')

    @app.route('/login',methods=['GET','POST'])
    def login():
      error = ''
      if request.method == 'POST':
         name = request.post.get('username')
         if name:
            user = db.get(name)
            if user:
               login_user(user)
               return redirect('/')
            else:
               error = 'invalid username'
         else:
                error = 'provide username to login'
      if error:
          flash(error)
      return render_template('login.html')

    def login_user(user):
        session['user_id'] = user.id


    @app.before_request
    def load_user():
     # to avoid getting attribute error
     # make sure to set request.user = value
     user_id = session.get('user_id')
     if user_id:
        # get user from db
        # you have to implement your own db
        # either using sqlalchemy or other orm
        user = db.get(id=user_id)
        if user:
            request.user =  user
        else:
            request.user = None
     else:
       request.user = None


    
    def login_require(func):
       def inner(*args,**kwargs):
          if request.user is None:
             return redirect('/login')
          return func(*args,**kwargs)
       return inner


    @app.route('/secret')
    @login_require
    def view():

       return 'Hello, you are authenticated'


