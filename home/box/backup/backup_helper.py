#!/usr/bin/env python3
"""grokbot-backup helper: select -> stage -> redact -> strict scan.
Usage: backup_helper.py stage <repo_dir> | scan <repo_dir>"""
import os, re, sys, shutil
HOME = '/home/box'
ROOTS = ['/workspace/xbm', '/workspace/tg', '/workspace/handoff', '/workspace/kb-devices', '/workspace/wechat',
         '/workspace/f50', '/workspace/router', '/workspace/xinci', '/workspace/ufiweb', '/workspace/tgfix',
         '/workspace/tp', '/workspace/tpl', '/workspace/lpx', '/workspace/play', '/workspace/xray',
         '/workspace/neko-agent', '/workspace/ufi', '/workspace/uploads',
         HOME + '/sand-data/workflows', HOME + '/.pi/agent', HOME + '/agent-tools', HOME + '/reference',
         HOME + '/.bashrc', HOME + '/.profile', HOME + '/backup/sync.sh', HOME + '/backup/backup_helper.py', HOME + '/backup/askpass.sh', HOME + '/backup/notify_fail.sh']
TOP_KEEP = {'/workspace/loon_fixed_v3.lcf'}
EXC = re.compile(r'(/venv/|/\.venv/|node_modules|__pycache__|\.pyc$|/\.cache/|/(build|dist|out|out2|bundle|pkg)/'
    r'|\.bak|\.(log|err|zip|tgz|tar\.gz|gz|dex|dat|mmdb|db|so|pdf|png|jpg|jpeg|gif|webp|lcf|b64|out)$'
    r'|\.env$|/\.env|/sessions/|\.jsonl$|/\.git/|/repo/|/src_'
    r'|^/workspace/tg/(data|archive)/|^/workspace/router/oc/|^/workspace/subtask/'
    r'|^/workspace/f50/subs/|^/workspace/f50/config\.yaml$|^/workspace/router/t/config\.yaml$'
    r'|install-command|/raw-[^/]*\.(json|txt)$|bookmarks-raw\.json$|ufi_rg_out'
    r'|(^|/)[^/]*(secret|credential|creds|token|session|cookie)[^/]*$|\.pem$|\.pw$|auth\.json'
    r'|^/home/box/agent-tools/[^/]*/out|/\.config/grokbot-backup/)', re.I)
ALLOW_TOKEN_EXT = {'freetoken-bots'}  # dir names containing "token" that are fine
REDACT_FILES = ('/workspace/tp/tp.py', '/workspace/shared.md', '/workspace/tg/digests/', '/workspace/loon_fixed_v3.lcf', '/workspace/handoff/anytls-nodes.md')
WEAK = re.compile(r'''(password|passwd|pwd|secret|api_?key|token)(["']?\s*[:=]\s*["']?)([^"'\s,${}<>`]{6,})''', re.I)
STRONG = re.compile(r'sk-[A-Za-z0-9_-]{16,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}'
                    r'|xox[bpa]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY')
BEARER = re.compile(r'[Bb]earer [A-Za-z0-9._-]{20,}')
PLACEHOLDER = re.compile(r'(<REDACTED>|os\.(environ|getenv)|re\.compile|your[_-]|~/|\$|xxx|<|None|null|true|false|process\.env)', re.I)
# reviewed: weak-pattern hits here are code variables / docs, not secrets (strong patterns still enforced)
ALLOWLIST = re.compile(r'^(workspace/wechat/(src/|ilink\.py|forwarder\.py|reply\.py|common\.py|status\.sh|RESEARCH\.md)'
    r'|workspace/xbm/.*(tg-login\.html|xbm_tg\.py)$|workspace/tg/qr_login\.py$|workspace/tg/igoropaniuk_teledigest\.md$'
    r'|workspace/f50/research/store/|workspace/tg/[A-Za-z0-9]+_[^/]*\.md$|home/box/backup/|workspace/xinci/report\.md$)')

def excluded(p):
    m = EXC.search(p)
    if m and not any(a in m.group(0) for a in ALLOW_TOKEN_EXT): return True
    return False

def select():
    out = []
    files = [os.path.join('/workspace', f) for f in os.listdir('/workspace') if os.path.isfile('/workspace/' + f)]
    for r in ROOTS:
        if os.path.isfile(r): files.append(r)
        elif os.path.isdir(r):
            for d, dirs, fs in os.walk(r):
                dirs[:] = [x for x in dirs if x not in ('venv', '.venv', 'node_modules', '__pycache__', '.git')]
                files += [os.path.join(d, f) for f in fs]
    for p in sorted(set(files)):
        if os.path.islink(p): continue
        if p not in TOP_KEEP and excluded(p): continue
        try:
            s = os.path.getsize(p)
            if s >= (3 << 20 if p in TOP_KEEP else 1 << 20): continue
            if b'\0' in open(p, 'rb').read(8192): continue
        except OSError: continue
        out.append(p)
    return out

def stage(repo):
    sel = select()
    for top in ('workspace', 'home'):
        shutil.rmtree(os.path.join(repo, top), ignore_errors=True)
    total = 0
    for p in sel:
        dst = os.path.join(repo, p.lstrip('/'))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(p, dst)
        if p.startswith(REDACT_FILES):
            t = open(dst, encoding='utf-8', errors='surrogateescape').read()
            t2 = WEAK.sub(lambda m: m.group(1) + m.group(2) + '<REDACTED>', t)
            if t2 != t: open(dst, 'w', encoding='utf-8', errors='surrogateescape').write(t2)
        total += os.path.getsize(dst)
    print(f'staged {len(sel)} files, {total/1048576:.2f} MB')

def scan(repo):
    hits = []
    for d, dirs, fs in os.walk(repo):
        dirs[:] = [x for x in dirs if x != '.git']
        for f in fs:
            p = os.path.join(d, f); rel = os.path.relpath(p, repo)
            try: lines = open(p, encoding='utf-8', errors='ignore').read().splitlines()
            except OSError: continue
            for i, l in enumerate(lines, 1):
                if STRONG.search(l): hits.append(f'{rel}:{i} [strong]')
                elif not ALLOWLIST.match(rel) and (BEARER.search(l) or
                        any(not PLACEHOLDER.match(m.group(3)) for m in WEAK.finditer(l))):
                    hits.append(f'{rel}:{i} [weak]')
    if hits:
        print('SECRET SCAN FAILED:'); print('\n'.join(hits)); sys.exit(3)
    print('secret scan: clean')

if __name__ == '__main__':
    {'stage': stage, 'scan': scan}[sys.argv[1]](sys.argv[2])
