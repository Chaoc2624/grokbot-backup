import json,sys,urllib.request,os
A="RDpbLfCPsJZ7fiv"
C="yLwVl0zKqws7LgKPRQ84Mdt708T1qQ3Ha7xv3H7NyU84p21BriUWBU43odz3iP4rBL3cD02KZciXTysVXiV8ngg6vL48rPJyAUw0HurW20xqxv9aYb4M9wK1Ae0wlro510qXeU07kV57fQMc8L6aLgMLwygtc0F10a0Dg70TOoouyFhdysuRMO51yY5ZlOZZLEal1h0t9YQW0Ko7oBwmCAHoic4HYbUyVeU3sfQ1xtXcPcf1aT303wAQhv66qzW"
def enc(a,b,c):
    d="";f=len(a);g=len(b);h=len(c);e=max(f,g)
    for l in range(e):
        k=m=187
        if l>=f: m=ord(b[l])
        elif l>=g: k=ord(a[l])
        else: k=ord(a[l]); m=ord(b[l])
        d+=c[(k^m)%h]
    return d
def post(url,data):
    r=urllib.request.Request(url,json.dumps(data).encode(),{"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(r,timeout=10).read())
pw=open(os.path.join(os.path.dirname(__file__),"p")).read()
r=post("http://192.168.0.1/",{"method":"do","login":{"password":enc(A,pw,C)}})
stok=r.get("stok")
if not stok: print("login fail",r); sys.exit(1)
ds="http://192.168.0.1/stok=%s/ds"%stok
for req in json.loads(sys.argv[1]):
    try: print(json.dumps(post(ds,req),ensure_ascii=False)[:6000])
    except Exception as e: print("ERR",req,e)
