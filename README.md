Glass is a mini WSGI routing library for building web applications.
It comes with bultin template engine. It is micro-framework because it comes with limited tools for web development. But it is extensible.

Glass  comes with builtin development server.

## Installation

 Install from pypi;

```bash

  $ pip istall glass-web

```

or upgrade to latest release ;

```bash
 $ pi install --upgrade glass-web

```
or clone from github;

```bash

  $ git clone https://github.com/horlarwumhe/glass.git
  $ cd glass
  $ pip install -r requirements.txt
  $ python setup.py install


```
##  Example

```py

  from glass import GlassApp

  app = GlassApp()
  @app.route('/')
  def home():
    return 'Hello, welcome.'

  @app.route('/greet/<name>')
  def greet(name):
      return 'Hello {}'.format(name)

  app.run()
  #app.run(host='127.0.0.1',port=8000,debug=True,auto_reload=True)

```

## Using Template

Glass template syntax is very similar to django template.


```html
  # index.html
  <html>
  <title> {% block title %} Blog {% endblock %}</title>
  <body>
    {% block content %}
       {% for post in posts %}
        <h3> {{post.title}} </h3>
        Author: <b> {{post.author}}
        <a href='{{post.url}}'> read more </a>
        {% endfor %}
       {% endblock %}
   </body>


```

```py

from glass import GlassApp
from glass import render_template,render_string
from glass import request,redirect

app = GlassApp()
@app.route('/')
def home():
  posts = get_all_posts()
  return render_template('index.html',posts=posts)

@app.route('/greet/<name>')
def greet(name):
  template = '''
  Hello {{name}}, welcome to {{request.host}}
  '''
  return render_string(template,name=name)

@app.route('/login',methods=["GET",'POST'])
def login():
  if request.method == 'POST':
    name = request.post.get('username')
    password = request.post.get('password')
    do_login(name,password)
    return redirect('/')
  else:
    return render_template('login.html')


app.run()

``` 
## Documentation
Documentation is available on [glass site](http://glass.horlarwumhe.me). It is also available on [readthedocs](https://glassapp.readthedocs.io).

