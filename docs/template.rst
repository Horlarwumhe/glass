
Template Engine
=================================
.. _glass: glass.html

Contents

.. .. contents::
..    :depth: 2
..    :local:
   

This is the template that comes with :doc:`Glass <glass>`.

Example
---------

>>> from glass.template import Template
>>> t = Template('hello {{user}}')
>>> t.render({'user':'horlarwumhe'})
'hello horlarwumhe'
>>> t = Template('hello {{user.upper}}')
>>> t.render({'user':'horlarwumhe'})
'hello HORLARWUMHE'


That is simple introduction on how to use the template.
To use the full capabilites of the template, use :func:`~glass.template.main.Environment` .
Using ``Environment`` allows template to be configured.
Such as;

  - creating custom template loader
  - creating a filter
  - creating a tag
  - caching the template

>>> from glass.template import Environment
>>> env = Environment()
>>> # the env only needs to be created once
>>> s = """
...   {% for user in users %}
...     {{user.name}}  {{user.email}}
... {% endfor %}
... 
...
... """
>>> users = [
...    {'name':'ola','email':'ola@mail.com'},
...   {'name':'wumhe','email':'wumhe@mail.com'}
...   ]
>>> t = env.from_string(s)
>>> out = t.render({'users':users})
>>> print(out)

::

    ola  ola@mail.com

    wumhe  wumhe@mail.com

Filters
--------
Filters are python function that modify value(s) of variables in the template. Values after ``|`` are filters. They take the variable as argument.

see :ref:`create custom filter <custom-filter>` to create new template filter.

::

   def lower(name):
      return name.lower()

::

     {{user.name |lower}}

using multiple filters;

::

    {{user.name | upper | lower | escape}}



Passing arguments to filters

::

   {{var|func(arg1 arg2 arg3)}}

::

Note:
   No ``,`` between the function arguments

::

  def func(var,arg1,arg2,arg3):
      return var+arg1+arg2+arg3


::

    {{text|split("\n") }}

::

   def split(text,s):
      return "".join(text.split(s))

::

  def format_price(price,currency):
      return "%s%s"%(currency,price)


::

   {{price|fromat_price("$")}}


::

   {% filter upper %}
     everyting here with be in upper case
        including {{user}}
   {% end %}
 but not this, it is outside the filter node

Using Python ``dict`` or ``list`` in the template.

::
   
   {{ dict.key }} # dict[key]

   {{list.0}} list[0]

   {{ list.2.upper }} # list[2].upper()

using block filter tag;


>>> from glass.template  import Environment
>>> e = Environment()
>>> s = '''{% filter upper %}
...        everyting here with be in upper case
...        including {{user}}
... {% end %}
... but not this, it is outside the filter node
... '''
>>> t = e.from_string(s)
>>> out = t.render({"user":'Horlar'})
>>> print(out)

::

       EVERYTING HERE WITH BE IN UPPER CASE
       INCLUDING HORLAR

    but not this, it is outside the filter node



Loading template from file
------------------------------

::

    from glass.template import Environment
    env = Environment()
    out = env.render_template('index.htm',{'user':'username'})


The default template loader, class :class:`~glass.template.main.FileLoader`, will look for the templates in the current working directory and  folder ``templates``  in the current working directory.

You can set different directory to find templates.

::

   from glass.template import FileLoader
   from glass.template import Environment
   env = Environment(loader=FileLoader('/path/to/templates'))
   # using multiple directories
   env = Environment(loader=FileLoader(['/path/to/templates','/path/to/other/template']))
   template = env.get_template('index.html')
   template.render({})



You can  create custom template loader.
The loader class must define two methods, ``load_template`` and ``check_if_modified``.
``load_template`` returns the template source to render while ``check_if_modified`` returns True if the template has been modified, False if not


>>> class MyLoader:
...  def load_template(self,name):
...     return templates[name]
...  def check_if_modified(self,name):
...    # check if the template has been modified or not
...
...    return True
...
>>> templates = {'index.html':'this is index','faq.html':'this is faq'}
>>> env = Environment(loader=MyLoader())
>>> env.render_template('index.html',{})
'this is index'
>>> env.render_template('faq.html',{})
'this is faq'
>>> t = env.get_template('index.html')
>>> t.render({})
'this is index'
>>> 

Template Caching
------------------------------

When rendering a template involve 3 major things.

   - tokenizing
      ``lexer(text).tokenize()`` which returns  all tokens in the template
   - parsing
     ``parser(tokens).parse()`` parses the tokens and return nodes/ast
   - rendering
      ``nodes.render()``

Rather than repeating the steps all time, the template is compiled once and the result is cached to speed up the rendering process.

The approach use in this template can explained with this code

.. code:: python

      caches = {}
      template = 'index.html'
      file = open('index.html')

      tokens = lexer(file.read()).tokenize()
      file.close()
      nodes = Parser.parse(tokens)

      # the template is now compiled, then cache the result
      caches[template] = nodes
      # anytime, the template needs to be rendered

      # the loader that loads this template will be called

      # to check if the file has been modified,

      #eg, the default loader , FileLoader(), will use os.stat(template).st_mtime
      # to check last time it was modified, 
      # if the loader return False , indicating the file is the same,
      #then the cache is check,
      nodes = caches.get(template)
      if nodes:
         # render , without parsing again
         return nodes.render({})
      else:
         #
         # parse the template
         # and cache the result


create cache class;

::

    class MyCache(dict):
        # define set() and get()
        def set(self,template,nodes):
           self[template] = nodes
        def get(self,template):
          return super().get(template)

pass the cache as argument to ``Environment`` instance.

>>> env = Environment(cache=MyCache())
>>> env.render_template('index.html',{})


Builtin Tags
--------------

if
~~~~~~

::

       {% if user.is_admin %}
          hello admin
       {% elif user.name == 'user' %}
            hello user
       {% else %}
            hello guest
       {% endif %}

for
~~~~~
::

      {% for user in users %}
         <b> {{user.name}} </b>
      {% endfor %}

      {% for user in users %}
        <b> {{user.name}} </b>
      {% else %}
        no user available
     {% endfor %}


.. versionadded:: 0.0.6

Special variables

When using the for tag, special special variables are added to the context.

:func:`LoopCounter`

Attributes.

**loop.index**
   
   current iteration index (1 based indexing) of the loop

**loop.index_0**

  same as loop.index, but use 0 based indexing

**loop.first**

  returns True if this is the first iteration

**loop.last**

  returns True if this is the last iteration

::

    {% for user in  users %}

      item number {{lopp.index}} is {{user.name}}
      {% if loop.first %}
          First iteration
      {% elif loop.last %}
         {{user.name}} Last item
      {% endif %}
    {% endfor %}

Example.

set color blue for first 3 items, red for last item and yellow for others.


::

    {% for user in users %}
      {% if loop.index < 4 %}
          {% set style="color:blue" %}

      {% elif loop.last %}
         {% set style="color:red" %}
      {% else %}
         {% set style="color:yellow" %}
      {% endif %}

    <p style="{{style}}">
    {{user.name}}
    </p>
    {% endfor %}

filter
~~~~~~~

:: 

    {% filter escape %}
         <b> {{name}} </b>
    {% end %}


extends
~~~~~~~~~

.. code:: html

    <!-- file index.html --> 
   {% extends 'base.html' %}
   {% block title %} page title {% endblock %}

   {% block content %}
      {% for post in posts %}
         {{post.title}}
      {% endfor %}
    {% endblock %}

.. code:: html

   <!-- file base.html --> 

   <title> {% block title %}{% endblock %}</title>
   <body>{%block content %} {% endblock %}</body>


block
~~~~~~~

.. code:: html

     {% block main %}
         main content
     {% endblock %}

set
~~~~~~

Use set tag to set variable in the template.

::

   {% set name="glass" id="id" %}

   Hello {{name}}
Using extends tag
----------------------

.. code:: html

   <!-- base.html --> 
  
   <title> {% block title %}{% endblock %}</title>
   {% block css %}
      <style> // css code here </style>
   {% endblock %}
   <body>
       {%block content %}
          <div> from base.html</div>
        {% endblock %}
   </body>



``base.html`` file can be extended by other templates and override any ``block`` tags.

.. code:: html

   <!-- file index.html --> 


   {% extends 'base.html' %}

   {% block title %} page title {% endblock %}
   {% block content %}
      <div>this is content from index.html</div>
    {% endblock %}

The ``index.html`` will override ``block title`` and ``block content`` but not  ``block css``.

.. code:: html

   <title> page title </title>
   <style> // css code here </style>
   <body>

     <div>this is content from index.html</div>

   </body>

However, if the block tag in the ``base.html`` needs to be rendered, you can use *super* directive. For example, you have javascript code in ``base.html`` which is required by ``index.html``.


.. code:: html

   <!-- base.html --> 
   <title> {% block title %} {% endblock %} </title>

   <body>
       {% block content %}
          <div> from base.html</div>
       {% endblock %}
   </body>
   {% block js %}
      <script src='js/navbar.js'>
          //javascript from base.html
      </script>
   {% endblock %}

If you want to include ``src='js/navbar.js'`` in the child template (``index.html``), use ``super``.


.. code:: html

    {% extends 'base.html' %}

    {% block title %} page title {% endblock %}

    {% block content %}
     <div> this is content from index.html<div>
    {% endblock %}
    {% block js super %}
      <script src='js/form.js'>
         //javascript from index.html
      </script>
    {% endblock %}

    

The above example will render ``block js`` in both ``base.html`` and ``index.html``

.. code:: html

       <title>  page title </title>
       <body>
           <div> this is content from index.html<div>       
       </body>

      <script src='js/navbar.js'>
          //javascript from base.html
      </script>
      <script src='js/form.js'>
          //javascript from index.html
      </script>

The above example rendered ``block js`` in parent template(``base.html``) before child template (``index.html``). If you want to render child template before the parent template, put *super* at the ``endblock`` tag.


.. code:: html

    {% extends 'base.html' %}

    {% block title %} page title {% endblock %}

    {% block content %}
     <div> this is content from index.html<div>
    {% endblock %}
    {% block js  %}
      <script src='js/form.js'>
          //javascript from index.html
      </script>
    {% endblock super %}

Output.

.. code:: html

   <title>  page title </title>
   <body>
      <div> this is content from index.html</div>    
   </body>
   <script src='js/form.js'>
       //javascript from index.html
   </script>

   <script src='js/navbar.js'>
       //javascript from base.html
   </script>

.. _custom-filter:

Custom Template Filter
------------------------
You can write filter(s) to use in the template(s).

::

     def secret(value):
        return  value[:5]+'********'

     def lower(value):
        return value.lower()

     def split_words(text,count=3):
         return " ".join(text.split()[:count])+'....'

     s = '''{% filter secret %}{{email}}{%end%}'''
     filters = {'secret':secret,'lower':lower,'split_words':split_words }
     env = Environment(filters=filters)
     t = env.from_string(s)
     out = t.render({'email':'usermail@gmail.com'})
     print(out)
       # userm********

     out = env.from_string("{{email|secret}}")
     print(out.render({'email':'usermail@gmail.com'}))
     #userm********
     
     t = env.from_string("{{post | split_words}}")
     print(t.render({'post':'this is a long text and another text'}))
     # this is a....

     t = env.from_string("{{post | split_words(5)}}")
     print(t.render({'post':'this is a long text and another text'}))
      # this is a long text....

or using decorator;

.. code-block:: python

     @env.filter('upper')
     def func(value):
        return value.upper()

     @env.filter("split_words")
     def split_words(text,count=3):
         return " ".join(text.split()[:count])+'....'


.. _custom-tag:

Custom Template Tag
----------------------

It is possible to create a tag to add to the bultin tags.

Creating a tag requires creating a function to call when the tag is found. The function takes one argument
``glass.template.parser.Parser``. The function should return ``Node`` object.

The tag can be registered with the code example.

.. code:: python

   env = Environment()
   @env.tag('tagname')
   def tag_parser(parser):
      # parse the tag here

   # or manually register the tag
   def tag_parser(parser):
       pass

  env = Environment(tags={'tagname':tag_parser})


lets create a simple tag that shows current time.

::

     {% time as now %}
         {{now}}



Using the :func:`Parser` class.

:func:`parser.get_next_token` returns next token and remove
the token from token list, while :func:`parser.next_token`  returns next token without removing it. 

>>> from glass.template.main import Parser, Lexer
>>> source = '''
...    {% if user.name %}
...     Hello {{user.name.title }}
...  {% else %}
...     Hello Guest
...  {% endfor %}
... '''
>>> tokens = Lexer(source).tokenize()
>>> parser = Parser(tokens)
>>> parser.tokens
...     [<Token BLOCK {% endfor %}, <Token TEXT Hello Guest,
...      <Token BLOCK {% else %}, <Token VAR {{ user.name.title }},
...       <Token TEXT Hello, <Token BLOCK {% if user.name %}
...     ]
>>> parser.next_token()
<Token BLOCK {% if user.name %}
>>> parser.tokens
...     [<Token BLOCK {% endfor %}, <Token TEXT Hello Guest,
...      <Token BLOCK {% else %}, <Token VAR {{ user.name.title }},
...       <Token TEXT Hello, <Token BLOCK {% if user.name %}
...     ]
>>> parser.get_next_token()
<Token BLOCK {% if user.name %}
>>> parser.tokens
...     [<Token BLOCK {% endfor %}, <Token TEXT Hello Guest,
...      <Token BLOCK {% else %}, <Token VAR {{ user.name.title }},
...       <Token TEXT Hello
...     ]
>>> parser.get_next_token()
<Token TEXT Hello
>>> parser.tokens
...     [<Token BLOCK {% endfor %}, <Token TEXT Hello Guest,
...      <Token BLOCK {% else %}, <Token VAR {{ user.name.title }}
...       
...     ]
>>> parser.get_next_token()
<Token VAR {{ user.name.title }}
>>> parser.tokens
...     [<Token BLOCK {% endfor %}, <Token TEXT Hello Guest,
...      <Token BLOCK {% else %}
...       
...     ]
>>> parser.next_token()
<Token BLOCK {% else %}
>>> parser.tokens
...     [<Token BLOCK {% endfor %}, <Token TEXT Hello Guest,
...      <Token BLOCK {% else %}
...       
...     ]
>>> parser.get_next_token()
<Token BLOCK {% else %}
>>> parser.tokens
[<Token BLOCK {% endfor %}, <Token TEXT Hello Guest]
>>> parser.next_token()
<Token TEXT Hello Guest
>>> parser.tokens
[<Token BLOCK {% endfor %}, <Token TEXT Hello Guest]
>>> parser.get_next_token()
<Token TEXT Hello Guest
>>> parser.tokens
[<Token BLOCK {% endfor %}]
>>> parser.next_token()
<Token BLOCK {% endfor %}
>>> parser.tokens
[<Token BLOCK {% endfor %}]
>>> parser.get_next_token()
<Token BLOCK {% endfor %}
>>> parser.tokens
[]
>>>
>>> source = '''
... {% if name == 'Firstname Lastname' %}
...     Hello
... {% endif %}
...
... '''
>>> parser = Parser(Lexer(source).tokenize())
>>> token = parser.get_next_token()
>>> token
<Token BLOCK {% if name == 'Firstname Lastname' %}
>>> cmd,args = token.clean_tag()
>>> cmd
'if'
>>> args
"name == 'Firstname Lastname'"
>>> args.split()
['name', '==', "'Firstname", "Lastname'"]
>>> token.split_args()
['name', '==', "'Firstname Lastname'"]
>>> # use token.split_args() to split content
...
>>>

.. code:: python

       # create function to parse the tag
       def time_parser(parser):
        cmd,args = parser.get_next_token().clean_tag()
        # or 
        # token = parser.get_next_token()
        # cmd ,args = token.clean_tag()
        ### print(cmd,args)
        ###    'time', 'as now'
        ### 
        _, var = args.split()
        return TimeNode(var)


.. code:: python

     # create the tag Node
     import datetime as dt

     class TimeNode:

        def __init__(self,var):
            self.var = var

        def render(self,context,env=None):
            context[self.var] = str(dt.datetime.now())
            return ''

Register the tag function.

>>> env = Environment(tags={'time':time_parser})
>>> out = env.from_string('''
...  {% time as now %}
...  date is    {{now}}
...
''')
>>> print(out.render({})
      )

::

     date is    2021-04-20 09:26:42.902343


create another tag ``match`` tag

::

    {% for user in users %}
        {% match user.status %}
           {% case 'verified' %}
                <b>{{user.name}}</b> is verified
           {% case 'pending' %}
               <b>{{user.name}}</b> is pending
           {% case 'suspend' %}
              <b>{{user.name}}</b> is suspended
           {% default %}
               <b>{{user.name}}</b> status is unknown
        {% end %}
    {% endfor %}

.. code :: python

    from glass.template import Environment
    from glass.template.nodes import VarNode

    env = Environment()

    @env.tag('match')
    def match_parse(parser):
        match_,test = parser.get_next_token().clean_tag()
        test = VarNode.parse(test)# return VarNode object
        # skip all token till {% case %}, {% default %} or
        # {% end %} is reached 
        parser.skip_untill(('end','case','default'))
        cases = case_parse(parser)
        default = parse_default(parser)
        end,_ = parser.next_token().clean_tag()
        if end != 'end':
            raise ValueError('match tag expect end')
        #skip {% end %} tag
        parser.skip_token(1)
        return MatchNode(test,cases,default)

    def case_parse(parser):
        # case tag is not registered, since
        # {% case %} cant stand alone, it must be 
        # part of {% match %} tag
        cases = []
        cmd,_ = parser.next_token().clean_tag()
        while cmd == 'case':
            cmd,value = parser.get_next_token().clean_tag()
            # or
            # token = parser.get_next_token()
            # cmd,test = token.clean_tag()
            body = parser.parse(stop_at=('end','case','default'))
            value = VarNode.parse(value)# return VarNode object
            node = CaseNode(value,body)
            cmd,_ = parser.next_token().clean_tag()
            cases.append(node)
        return cases

    def parse_default(parser):
        cmd,_ = parser.next_token().clean_tag()
        if cmd == 'default':
            _= parser.get_next_token()
            body = parser.parse(stop_at=('end',))
            return DefaultNode(body)


create *Node* object

.. code :: python

    from glass.template.nodes import Node

    class MatchNode(Node):
        #{% match test %}
        def __init__(self,test,cases,default):
            self.test = test
            self.cases = cases
            self.default = default

        def render(self,context,env=None):
            test_value = self.test.eval(context,env)
            for case in self.cases:
                case_value = case.value.eval(context,env)
                if test_value == case_value:
                    return case.render(context,env)
            if self.default is not None:
                return self.default.render(context,env)
            return ''

    class CaseNode(Node):
      # {% case value %}
      def __init__(self,value,body):
          self.value = value
          self.body = body

      def render(self,context,env=None):
          return self.body.render(context,env)

    class DefaultNode(Node):
        # {% default %}
        def __init__(self,body):
            self.body = body
        def render(self,context,env=None):
            return self.body.render(context,env)

use the tag;

>>> source = '''
...    {% for user in users %}
...       {% match user.status %}
...         {% case 'verified' %}
...             <b>{{user.name}}</b> is verified
...         {% case 'pending' %}
...            <b>{{user.name}}</b> is pending
...        {% case 'suspend' %}
...           <b>{{user.name}}</b> is suspended
...        {% default %}
...            <b>{{user.name}}</b> status is unknown
...      {% end %}
...     {% endfor %}
...  '''
>>> ctx = {'users':[
            {'name':'Horlarwumhe','status':'suspend'},
            {'name':'Horlar','status':'pending'},
            {'name':'Olawumi','status':'verified'},
            {'name':'Hor','status':''},
        ]
    }
>>> t = env.from_string(source)
>>> print(t.render(context))

::

    <b>Horlarwumhe</b> is suspended

    <b>Horlar</b> is pending

    <b>Olawumi</b> is verified

    <b>Hor</b> status is unknown

See the  ``Environment`` API here :class:`Environment <glass.template.main.Environment>`.

Using With :doc:`Glass <glass>`
---------------------------------

To use the ``Environment`` class with Glass, use :attr:`app.template_env <glass.app.GlassApp.template_env>`.

see :ref:`Glass doc <using-template>` on how to use the template engine with Glass app.



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
