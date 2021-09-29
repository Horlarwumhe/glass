Glass Documentation
====================

Glass is a mini WSGI routing library for building web applications.
It comes with bultin template engine. It is micro-framework because it comes with limited tools for web development. But it is extensible.

Glass  comes with builtin development server.

What does it look like ?

::

   from glass import GlassApp

   app = GlassApp()
   @app.route('/')
   def index():
       return 'Hello'


.. toctree::
   glass
   template
   :maxdepth: 2


Changelog

.. toctree::
   changelog
   :maxdepth: 2
   