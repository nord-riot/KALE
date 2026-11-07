#!/usr/bin/env python3
"""Termux KALE foreground supervisor (optional boot launcher).

Runs KALE in a subprocess; restarts on unexpected exit. Nothing accesses the
Internet. Designed for Android without root or custom background privileges.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
HOME=Path.home()
STOP=[False]


def write_status(path,**data):
    path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
    os.chmod(tmp,0o600);os.replace(tmp,path)


def signal_handler(_sig,_frame):STOP[0]=True


def health_wait(process,seconds):
    """Delay in small steps so SIGTERM can be honored without orphaning child."""
    until=time.monotonic()+seconds
    while not STOP[0] and process.poll() is None and time.monotonic()<until:time.sleep(.2)


def run(cache_dir=None,python=None):
    cache=Path(cache_dir) if cache_dir else HOME/'.cache'/'kale'
    cache.mkdir(parents=True,mode=0o700,exist_ok=True)
    os.chmod(cache,0o700)
    lock=(cache/'supervisor.lock').open('a+')
    try:fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:
        print('KALE 7/24 zaten çalışıyor. İkinci sunucu başlatılmadı.',file=sys.stderr)
        return 2
    status=cache/'supervisor.json';logfile=cache/'supervisor.log'
    signal.signal(signal.SIGTERM,signal_handler);signal.signal(signal.SIGINT,signal_handler)
    wake=shutil.which('termux-wake-lock')
    unlock=shutil.which('termux-wake-unlock')
    if wake:
        try:subprocess.run([wake],timeout=5,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
        except (subprocess.TimeoutExpired,OSError):pass
    restarts=0
    proc=None;router=None;router_log=None
    env={**os.environ,'KALE_HOST':'0.0.0.0','KALE_PORT':os.environ.get('KALE_PORT','8090'),
         'KALE_SUPERVISOR_STATUS':str(status)}
    # BRouter (heavy Java process) is explicitly OPT-IN for battery conservation.
    try:
        if env.get('KALE_ENABLE_BROUTER','0')=='1':
            jar=ROOT/'data/routing/brouter.jar'
            lookups=ROOT/'data/routing/profiles2/lookups.dat'
            if jar.is_file() and lookups.is_file() and shutil.which('java'):
                router_log=(cache/'brouter.log').open('ab')
                router=subprocess.Popen([python or sys.executable,'tools/run_brouter.py'],cwd=ROOT,env=env,
                              stdout=router_log,stderr=subprocess.STDOUT,start_new_session=True)
        delay=3
        while not STOP[0]:
            # Retain at most a small bounded service log; no query data is logged by KALE.
            if logfile.exists() and logfile.stat().st_size>1048576:
                logfile.rename(cache/'supervisor.log.previous')
            started=time.monotonic()
            with logfile.open('a',encoding='utf-8') as output:
                print(f'[{datetime.now(timezone.utc).isoformat()}] KALE service starting',file=output,flush=True)
                proc=subprocess.Popen([python or sys.executable,'-u','server.py'],cwd=ROOT,env=env,
                           stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT)
                write_status(status,state='running',pid=proc.pid,restarts=restarts,
                             last_start=datetime.now(timezone.utc).isoformat())
                while not STOP[0] and proc.poll() is None:time.sleep(.4)
                if STOP[0]:
                    proc.terminate()
                    try:proc.wait(timeout=6)
                    except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
                    break
                elapsed=time.monotonic()-started
                restarts+=1
                write_status(status,state='restarting',pid=None,restarts=restarts,
                             last_exit_code=proc.returncode,last_failure=datetime.now(timezone.utc).isoformat())
                print(f'KALE terminated, exit={proc.returncode}; restarting',file=output,flush=True)
            if elapsed>=120:delay=3
            else:delay=min(60,max(3,delay*2))
            until=time.monotonic()+delay
            while not STOP[0] and time.monotonic()<until:time.sleep(.2)
        write_status(status,state='stopped',pid=None,restarts=restarts)
        return 0
    finally:
        if proc and proc.poll() is None:
            proc.terminate()
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
        if router and router.poll() is None:
            router.terminate()
            try:router.wait(timeout=4)
            except subprocess.TimeoutExpired:router.kill();router.wait(timeout=5)
        if router_log is not None:router_log.close()
        if unlock:
            try:subprocess.run([unlock],timeout=5,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
            except (OSError,subprocess.TimeoutExpired):pass
        lock.close()


def main():
    p=argparse.ArgumentParser(description='KALE Android 24/7 supervisor')
    p.add_argument('--cache-dir',type=Path,default=None)
    a=p.parse_args()
    return run(a.cache_dir)

if __name__=='__main__':sys.exit(main())
