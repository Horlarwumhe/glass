Glass is a mini WSGI routing library for building web applications.
It comes with bultin template engine. It is micro-framework because it comes with limited tools for web development. But it is extensible.

Glass  comes with builtin development server.

## Installation

 Install from pypi;

<!-- Using the old project pypi name. -->
```bash

  $ pip istall glass-web

```

or upgrade to latest release;

```bash
 $ pip install --upgrade glass-web

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
# app.run()
app.run(host='127.0.0.1',port=8000,debug=True,auto_reload=True)

```

Using a WSGI web server to start Glass

```py

from glass import GlassApp

app = GlassApp()
@app.route('/')
def home():
  return 'Hello, welcome.'

```

Gunicorn

save the file as **main.py**
```bash
   $ gunicorn main:app
```

Variable url rule

```py

@app.route('/greet/<name>')
def greet(name):
    return 'Hello {}'.format(name)
@app.route('/user/<int:user_id>/profile')
def user_profile(user_id):
  user = get_user(user_id)
  return user.to_dict()
#app.run(host='127.0.0.1',port=8000,debug=True,auto_reload=True)

```

## Response

return string
```py

@app.route('/home')
def home():
  return "hello"

```

return response with status code

```py

@app.route('/badrequest')
def bad():
  return "Hoops",400

```

return response with custom headers

```py

from glass import Response
from time import time

@app.route('/')
def home():
   r = Response("Hello, welcome",status_code=200)
   r.set_header("Header-Name","value")
   r.set_header("Another-Header","anothe-value")
   # set cookie
   r.set_cookie("cookie-name","value")
   # r.set_cookie("cookie-name","value",path='/',expires=60,httponly=true)
   return r

```

## Working with HTML form

```py

from glass import GlassApp
from glass import request

app = GlassApp()

@app.route('/',methods=['GET','POST'])
def home():
   if request.method == "POST":
        name = request.post.get("username")
        email = request.post.get("email")
        do_something(name,email)
   return 'Hello, welcome.'


```

## JSON

```py

from glass import GlassApp
from glass import request

app = GlassApp()

@app.route('/',methods=['GET','POST'])
def home():
   if 'application/json' in request.headers.get("Content-Type",''):
        # json request
        data = request.get_json()
        return data
   return {"ok":False,"message":"bad request":"code":400}

```

## Sending Files

```py

    from glass.response import FileResponse

    @app.route("/files")
    def send():
      f = FileResponse("path/to/file.ext")
      # if you want to set headers
      f.set_header("Header-Name","value1")
      # set cookies
      # r.set_cookies
      return f

```
## Using Session


```py

from glass import GlassApp
from glass import redirect
from glass import render_string
from glass import request
from glass import session

app = GlassApp()
app.config["SECRET_KEY"] = "a234fcaad12121de"


FORM = '''

<form method="post">
  <input type="text" name="username" placeholder="Your name">
  <input type="text" name="email" placeholder="Email" >
  <input type="submit">
</form>
'''

@app.route('/',methods=['GET','POST'])
def home():
    if request.method == "POST":
        name = request.post.get("username")
        email = request.post.get("email")
        session['name'] = name
        session['email'] = email
        return redirect("/profile")
    return FORM

template = '''

<h3>
   Hello <b> {{name.title}} </b>, 
   Your email is <b>{{email}}</b>
</h3>

'''

@app.route('/profile')
def profile():
   name = session.get("name")
   if not name:
      return redirect('/')
   email = session.get('email')
   return render_string(template,email=email,name=name)

app.run(auto_reload=True)

```
## Using Template

Glass comes with template engine. The template syntax is very similar to django template.


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
   </html>


```

## Extending templates

*base.html*

```html

<title> Hello </title>
 <body>
  {% block main %}
  {% endblock %}
</body>
```
*index.html*
```html

{% extends "base.html"}

    {% block main %}
      <div> main </div>
    {% endblock %}

```

#### Template filters

```html

{% for user in users %
    {{user.name | upper }} {# convert user.name to uppercase #}
    {% for post in user.posts %}
        {{post.title}}
        {{post.body | truncate(5,"....")}}
    {% endfor %}
{% endfor %}

```

*truncate* function in the example above
```py

def truncate(text,size,s):
  ''' text = this is a long post with a long text
      truncate(text,5,".....") == this is a long post....
      
  '''
  text = text.split()[:size]
  return " ".join(text) + s

```

## Documentation

Documentation is available on available on [readthedocs](https://glassapp.readthedocs.io).




