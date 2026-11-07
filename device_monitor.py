"""KALE local-only device status. No network calls, root, storage or telemetry.

Host admin endpoints must be restricted by *remote socket peer*, not headers.
Termux:API battery reading is optional; missing readings become null, never invented.
"""
from collections import deque
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import threading
import time

STARTED_MONOTONIC = time.monotonic()


def number(value, minimum=None, maximum=None):
    try:
        if isinstance(value, str):value=value.replace(',', '.')
        val=float(value)
        if not math.isfinite(val) or (minimum is not None and val<minimum) or (maximum is not None and val>maximum):return None
        return val
    except (TypeError, ValueError, OverflowError):return None


def read_cpu_snapshot(path='/proc/stat'):
    try:
        with open(path,encoding='ascii') as f:fields=f.readline().split()
        if not fields or fields[0]!='cpu':return None
        nums=[int(x) for x in fields[1:]]
        if len(nums)<4:return None
        idle=nums[3]+(nums[4] if len(nums)>4 else 0)
        return sum(nums),idle
    except (OSError,ValueError):return None


def cpu_percent(before, after):
    if not before or not after:return None
    total=after[0]-before[0];idle=after[1]-before[1]
    return round(max(0,min(100,100*(1-idle/total))),1) if total>0 else None


def memory_stats(path='/proc/meminfo'):
    try:
        pairs={}
        with open(path,encoding='ascii') as f:
            for line in f:
                bits=line.split()
                if len(bits)>=2 and bits[0].endswith(':'):
                    pairs[bits[0][:-1]]=int(bits[1])
        total=pairs.get('MemTotal');available=pairs.get('MemAvailable')
        if not total or available is None:return {'total_mb':None,'used_mb':None,'percent':None}
        return {'total_mb':round(total/1024),'used_mb':round((total-available)/1024),
                'percent':round(max(0,min(100,100*(total-available)/total)),1)}
    except (OSError,ValueError,ZeroDivisionError):return {'total_mb':None,'used_mb':None,'percent':None}


def parse_battery(raw):
    if not isinstance(raw,dict):return {'available':False}
    p=number(raw.get('percentage'),0,100)
    temp=number(raw.get('temperature'),-30,100)
    cur=number(raw.get('current'),-20000000,20000000)
    charge=number(raw.get('charge_counter'),0,200000000)
    plugged=str(raw.get('plugged','')).upper()
    status=str(raw.get('status','')).upper()
    # µAh / µA gives hours only with positive remaining charge and measured discharge current.
    # Instantaneous current is noisy; this is indicative, not a promise of runtime.
    hours=round(charge/(-cur),1) if status=='DISCHARGING' and cur is not None and cur< -10000 and charge and charge/(-cur)<=240 else None
    return {'available':p is not None,'percentage':p,'status':status[:25] if status else None,
            'plugged':plugged[:25] if plugged else None,'temperature_c':temp,
            'remaining_hours_estimate':hours, 'estimate_note':'Anlık akım ölçümüne göre kaba tahmin; ölçüm desteklenmiyorsa boş kalır.'}


def get_battery(command=None, runner=subprocess.run):
    command = shutil.which('termux-battery-status') if command is None else command
    if not command:return {'available':False,'message':'Termux:API pil ölçümü kurulu değil. F-Droid Termux:API ve pkg install termux-api gerekli.'}
    try:
        r=runner([command],capture_output=True,text=True,timeout=3,check=False)
        if r.returncode!=0 or len(r.stdout)>12000:raise ValueError('Battery API error')
        payload=parse_battery(json.loads(r.stdout))
        if payload['available']:return payload
    except (OSError,ValueError,json.JSONDecodeError,subprocess.TimeoutExpired,TypeError):pass
    return {'available':False,'message':'Pil ölçümü alınamadı; izinleri ve Termux:API uygulamasını kontrol et.'}


class DeviceMonitor:
    def __init__(self,clock=time.monotonic, battery=get_battery):
        self.clock=clock;self.battery=battery
        self.started=self.clock();self.eco=True
        self._last=0.0;self._battery={'available':False};self._cpu=read_cpu_snapshot()
        self._cpu_usage=None
        self._events=deque(maxlen=50)
        self._lock=threading.RLock()
        self.event('KALE servis başlatıldı')

    def event(self,label):
        with self._lock:
            self._events.append({'time':datetime.now(timezone.utc).isoformat(),'message':label[:120]})

    def set_eco(self,value):
        if type(value) is not bool:raise ValueError('Tasarruf ayarı boolean olmalı.')
        with self._lock:
            self.eco=value;self.event('Panel enerji tasarruf modu '+('açıldı' if value else 'kapatıldı'))
            return self.eco

    def snapshot(self, chat_users=None, status_path=None):
        now=self.clock()
        with self._lock:
            cadence=35 if self.eco else 12
            if self._last==0 or now-self._last>=cadence:
                next_cpu=read_cpu_snapshot()
                self._cpu_usage=cpu_percent(self._cpu,next_cpu)
                self._cpu=next_cpu
                self._battery=self.battery()
                self._last=now
            mem=memory_stats()
            supervisor=None
            if status_path:
                try:
                    p=Path(status_path)
                    if p.stat().st_size<4096:
                        supervisor=json.loads(p.read_text(encoding='utf-8'))
                        if not isinstance(supervisor,dict):supervisor=None
                except (OSError,ValueError):pass
            return {'app':'KALE','server_running':True,'uptime_seconds':int(now-self.started),
                    'cpu_percent':self._cpu_usage,'cpu_cores':os.cpu_count(),
                    'memory':mem,'battery':self._battery,'energy_saving_mode':self.eco,
                    'energy_note':'Sadece KALE panelinin ölçüm/sorgu sıklığını düşürür. Android hotspot veya CPU frekansını değiştirmez.',
                    'online_chat_users':chat_users,'hotspot_clients':None,
                    'hotspot_note':'Hotspot bağlı cihaz sayısı rootsuz Android ortamında her zaman okunamaz; sohbet kullanıcı sayısı ayrıdır.',
                    'supervisor':supervisor,'events':list(self._events)}

MONITOR = DeviceMonitor()
