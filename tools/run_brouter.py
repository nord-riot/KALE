#!/usr/bin/env python3
"""Launch local BRouter server; routes are calculated only from installed rd5."""
import os
import shutil
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/'data/routing';JAR=DIR/'brouter.jar';SEGS=DIR/'segments4';PROFILES=DIR/'profiles2';CUSTOM=DIR/'customprofiles'

def main():
    java=shutil.which('java')
    if not java:raise SystemExit('Java eksik. Termux: pkg install openjdk-17')
    if not JAR.is_file() or not (PROFILES/'lookups.dat').is_file():
        raise SystemExit('BRouter yüklenmedi. Önce: python3 tools/turkiye_full.py engine')
    if not list(SEGS.glob('*.rd5')):raise SystemExit('Rota bölgesi yok. Önce: python3 tools/turkiye_full.py segments')
    CUSTOM.mkdir(parents=True,exist_ok=True)
    cmd=[java,'-Xms64m','-Xmx384m','-DmaxRunningTime=300','-DuseRFCMimeType=false',
         '-cp',str(JAR),'btools.server.RouteServer',str(SEGS),str(PROFILES),str(CUSTOM),'17777','1','127.0.0.1']
    print('BRouter sadece 127.0.0.1:17777 üzerinden çalışıyor. Çıkış Ctrl+C.',flush=True)
    os.execv(java,cmd)
if __name__=='__main__':main()
