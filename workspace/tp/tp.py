import json, sys, os, urllib.request
BASE="http://192.168.0.1"
C="yLwVl0zKqws7LgKPRQ84Mdt708T1qQ3Ha7xv3H7NyU84p21BriUWBU43odz3iP4rBL3cD02KZciXTysVXiV8ngg6vL48rPJyAUw0HurW20xqxv9aYb4M9wK1Ae0wlro510qXeU07kV57fQMc8L6aLgMLwygtc0F10a0Dg70TOoouyFhdysuRMO51yY5ZlOZZLEal1h0t9YQW0Ko7oBwmCAHoic4HYbUyVeU3sfQ1xtXcPcf1aT303wAQhv66qzW"
B="RDpbLfCPsJZ7fiv"
def enc(a,b=B,c=C):
    e="";g=len(a);h=len(b);k=len(c);f=max(g,h)
    for p in range(f):
        l=n=187
        if p>=g: n=ord(b[p])
        elif p>=h: l=ord(a[p])
        else: l=ord(a[p]); n=ord(b[p])
        e+=c[(l^n)%k]
    return e
def post(path,obj):
    req=urllib.request.Request(BASE+path,data=json.dumps(obj).encode(),headers={"Content-Type":"application/json; charset=UTF-8"})
    return json.loads(urllib.request.urlopen(req,timeout=10).read().decode("utf-8","replace"))
SF="/tmp/.tpstok"
def login():
    pw=open(os.path.expanduser("/tmp/.tppw")).read().strip()
    r=post("/",{"method":"do","login":{"password":<REDACTED>}})
    if "stok" not in r: print("LOGIN FAIL",r);sys.exit(1)
    fd=os.open(SF,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600);os.write(fd,r["stok"].encode());os.close(fd)
    return r["stok"]
def ds(obj):
    stok=open(SF).read().strip() if os.path.exists(SF) else login()
    r=post("/stok=%s/ds"%stok,obj)
    if r.get("error_code") in (-40401,"-40401"):
        stok=login(); r=post("/stok=%s/ds"%stok,obj)
    return r
if __name__=="__main__":
    for a in sys.argv[1:]:
        print(json.dumps(ds(json.loads(a)),ensure_ascii=False))
