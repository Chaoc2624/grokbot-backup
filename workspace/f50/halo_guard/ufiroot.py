import hashlib,hmac,json,sys,time,urllib.request,os
B="http://192.168.0.1:2333"; K=b"minikano_kOyXz0Ciz4V7wR0IeKmJFYFQ20jd"
PW=os.environ.get("UFIPW","admin")
def sign(m,p,t):
    h=hmac.new(K,("minikano"+m+p+str(t)).encode(),hashlib.md5).digest()
    return hashlib.sha256(hashlib.sha256(h[:8]).digest()+hashlib.sha256(h[8:]).digest()).hexdigest()
def root(cmd,timeout=300000):
    t=int(time.time()*1000); p="/api/root_shell"
    r=urllib.request.Request(B+p,data=json.dumps({"command":cmd,"timeout":timeout}).encode(),method="POST",headers={"Content-Type":"application/json","kano-t":str(t),"kano-sign":sign("POST",p,t),"authorization":hashlib.sha256(PW.encode()).hexdigest()})
    return json.load(urllib.request.urlopen(r,timeout=timeout/1000+20))
if __name__=="__main__":
    cmd=sys.argv[1] if len(sys.argv)>1 else "whoami"
    if cmd.startswith("@"): cmd=open(cmd[1:]).read()
    try: res=root(cmd)
    except Exception as e: print("ERR",e); sys.exit(1)
    r=res.get("result",res); print(r.get("content",r) if isinstance(r,dict) else r)
