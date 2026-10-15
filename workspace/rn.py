import paramiko,sys
c=paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("192.255.151.85",username="root",key_filename="/home/box/.ssh/id_ed25519",timeout=15,allow_agent=False,look_for_keys=False)
cmd=sys.stdin.read()
i,o,e=c.exec_command(cmd,get_pty=False,timeout=900)
for l in iter(o.readline,""): sys.stdout.write(l)
err=e.read().decode(); sys.stdout.write(err)
sys.exit(o.channel.recv_exit_status())
