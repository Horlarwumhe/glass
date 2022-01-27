from glass import GlassApp

app = GlassApp()

@app.route('/')
def home():
    return "Welcome to glass"

app.run(host='localhost',port=8000,auto_reload=True)
