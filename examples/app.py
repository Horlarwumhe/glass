from glass import GlassApp, Response, redirect, request

app = GlassApp()

@app.route('/c')
def home():
    return redirect('/c')
    return "Welcome to glass"

@app.route('/')
def home():
   r = Response("Hello, welcome",status_code=200)
   r.set_header("Header-Name","value")
   r.set_header("Another-Header","anothe-value")
   # set cookie
   print(request.headers)
   if "Accept" in request.headers:
        print("accept present")

   else:
    print("no found")
   r.set_cookie("cookie-name","value")
   # r.set_cookie("cookie-name","value",path='/',expires=time()+60,httponly=true)
   return r
app.run(host='localhost',port=8000,auto_reload=True)
