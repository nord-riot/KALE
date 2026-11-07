#!/usr/bin/env python3
"""Stop only KALE processes owned by this user and based in this repository.

No blanket pkill, no privileged operations. On Android some /proc records may be
hidden; an unidentifiable process is never killed.
"""
from pathlib import Path
import os
import signal
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
EXPECTED={'tools/kale_supervisor.py','server.py'}

def candidates(proc_root=Path('/proc'),cwd_root=ROOT):
    self_pid=os.getpid()
    found=[]
    for folder in proc_root.iterdir():
        if not folder.name.isdigit() or int(folder.name)==self_pid:continue
        try:
            pid=int(folder.name)
            cmd=(folder/'cmdline').read_bytes().split(b'\0')
            tokens=[t.decode('utf-8','replace') for t in cmd if t]
            if len(tokens)<2 or not any(token in EXPECTED for token in tokens[1:]):continue
            cwd=(folder/'cwd').resolve(strict=True)
            if cwd!=cwd_root.resolve(strict=True):continue
            found.append((pid,tokens))
        except (OSError,ValueError,PermissionError):continue
    return found

def main():
    found=candidates()
    if found:
        print('Aynı KALE dizininde çalışan eski süreçler durduruluyor:',[x[0] for x in found])
    for pid,_cmd in found:
        try:os.kill(pid,signal.SIGTERM)
        except (OSError,ProcessLookupError):pass
    for _ in range(30):
        if not candidates():return 0
        time.sleep(.2)
    print('Bazı KALE işlemleri kapatılamadı; açık Termux oturumunda Ctrl+C uygula.',file=sys.stderr)
    return 1

if __name__=='__main__':sys.exit(main())
