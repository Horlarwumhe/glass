from glass import GlassApp, session

app = GlassApp()

@app.route('/')
def home():
    session['l'] = 'sa'
    return "Welcome to glass"

app.config['SESSION_COOKIE_EXPIRE'] = 60*60
app.config['SESSION_COOKIE_MAXAGE'] = 60*5
app.run(host='localhost',port=8000,auto_reload=True)
