from glass import GlassApp, Response, redirect, request,session
from glass.sessions import RedisSessionManager as R

r = R(host="192.168.56.101",db=1)
app = GlassApp()
app.session_cls = r
app.config['SECRET_KEY'] = 'abcd'
@app.route('/')
def home():
    
    return "Welcome to glass"

@app.route('/set/<name>')
def add(name):
    session['name'] = name
    return "done....."

@app.route('/get')
def get():
    return session.session_data

@app.route('/pop')
@app.route('/pop/<key>')
def pop(key=None):
    if key:
        session.pop(key)
    else:
        session.clear()
    return "popedd....."

@app.route('/<key>/<value>')
def set(key,value):
    session[key] = value
    return "done......"

app.run(port=8000,auto_reload=True,debug=True)

