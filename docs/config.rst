
.. _mozilla: https://developer.mozilla.org/en/docs/web/HTTP/Cookies

Glass Configuration
======================
Glass application can be configured to change the behaviour of the app. 

The app can be configured by using following methods;


Config From Dict
------------------

::

     app = GlassApp()
     conf = {
         'DB_URI':'<database-uri>',
         'TESTING':True
         'DEBUG':False
         }
     app.config.from_dict(conf)

Config From Object
~~~~~~~~~~~~~~~~~~~~~

::

   class Config:

     DEBUG = True
     DB_URI = '<database-uri>'
     TESTING  = True
     TEMPLATES_FOLDER = '/path/to/template'

   app = GlassApp()
   app.config.from_obj(Config)

Config From Json
~~~~~~~~~~~~~~~~~

::

      app = GlassApp()
      app.config.from_json('/path/to/file.json')

Config With ``setitem``
~~~~~~~~~~~~~~~~~~~~~~~~~

::

    app = GlassApp()
    app.config['TEMPLATES_FOLDER'] = '/path/to/template'
    app.config['DEBUG'] = False
    app.config['DB_URI'] = '<database-uri>'


Using The Configuration Values;

::

     db = app.config['DB_URI']
     connect_db(db)

     test = app.config['TESTING']
     if test:
         do_something()


Internally used config values;


*DEBUG*
   enable debug mode.

   - default ``True``

*SESSION_COOKIE_NAME*

    name of session cookie, default to ``session``
        check `mozilla`_

*SESSION_COOKIE_DOMAIN*

  domain to use for session cookie. default to ``None``
     check `mozilla`_


*SESSION_COOKIE_SECURE*

    session cookie over https only. default to ``False``

      check `mozilla`_


*SESSION_COOKIE_PATH*

  ``path`` for session cookie. default to ``/``

     check `mozilla`_

*SESSION_COOKIE_HTTPONLY*

  mark session cookie as ``HttpOnly``. default to ``False``.
       
       check `mozilla`_

*SESSION_COOKIE_SAMESITE*

   cookie ``SameSite`` attribute.

        check `mozilla`_

*SECRET_KEY*

   app secret key, use for signing cookie.


*MAX_CONTENT_LENGTH*

  maximum ``Content-Length``. If request Content-Length is greater than this value ``419 Request Too large`` is returned.

     default to ``None``


*STATIC_FOLDER*
 
   directory to find static files. 
      default to folder `static` in the current directory

*TEMPLATES_FOLDER*

   directory for templates
      default to **templates** folder in the current directory.

::

    app.config['TEMPLATES_FOLDER'] = '/path/to/template'

    app.config['TEMPLATES_FOLDER'] = ('/path/to/template','/path/to/other/template')
