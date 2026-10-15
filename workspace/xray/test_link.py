#!/usr/bin/env python3
import sys,json,subprocess,time,urllib.parse,os,random
link=sys.argv[1]
u=urllib.parse.urlparse(link); q=dict(urllib.parse.parse_qsl(u.query))
uid,hp=u.netloc.split("@"); host,port=hp.rsplit(":",1)
lp=random.randint(20000,30000)
cfg={"log":{"loglevel":"warning"},"inbounds":[{"listen":"127.0.0.1","port":lp,"protocol":"socks","settings":{"udp":False}}],
"outbounds":[{"protocol":"vless","settings":{"vnext":[{"address":host,"port":int(port),"users":[{"id":uid,"encryption":"none","flow":q.get("flow","")}]}]},
"streamSettings":{"network":q.get("type","tcp"),"security":"reality","realitySettings":{"serverName":q["sni"],"fingerprint":q.get("fp","chrome"),"publicKey":q["pbk"],"shortId":q.get("sid",""),"spiderX":urllib.parse.unquote(q.get("spx","/"))}}}]}
fn=f"/tmp/xc_{lp}.json"; open(fn,"w").write(json.dumps(cfg)); os.chmod(fn,0o600)
p=subprocess.Popen(["/workspace/xray/xray","run","-c",fn],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
time.sleep(1.5)
r=subprocess.run(["curl","-s","-o","/dev/null","-m","15","-w","%{http_code} %{time_total}s","-x",f"socks5h://127.0.0.1:{lp}","https://www.gstatic.com/generate_204"],capture_output=True,text=True)
ip=subprocess.run(["curl","-s","-m","15","-x",f"socks5h://127.0.0.1:{lp}","https://api.ipify.org"],capture_output=True,text=True).stdout
p.terminate(); err=p.stderr.read().decode()[-300:]; os.remove(fn)
print(urllib.parse.unquote(u.fragment), "->", r.stdout, "exit_ip", ip, ("ERR "+err) if r.stdout[:3]!="204" else "")
