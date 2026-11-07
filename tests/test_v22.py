"""KALE v2.2 device status, Android boot script and private admin security."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from urllib import error, request
from unittest.mock import Mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from device_monitor import DeviceMonitor, cpu_percent, memory_stats, parse_battery, get_battery, number
import server


class DeviceUnitTests(unittest.TestCase):
    def test_termux_battery_numeric_and_comma_temperature(self):
        data=parse_battery({'percentage':87,'temperature':'32,5','current':-200000,
                            'charge_counter':2000000,'status':'DISCHARGING','plugged':'UNPLUGGED'})
        self.assertTrue(data['available'])
        self.assertEqual(data['temperature_c'],32.5)
        self.assertEqual(data['remaining_hours_estimate'],10)
        self.assertFalse(parse_battery({'percentage':150})['available'])
        self.assertIsNone(parse_battery({'percentage':70,'current':0,'charge_counter':3000000})['remaining_hours_estimate'])
        self.assertIsNone(number('nan'))

    def test_battery_missing_optional_no_fake_numbers(self):
        self.assertFalse(get_battery(command='')['available'])
        fake=Mock(returncode=0,stdout=json.dumps({'percentage':42,'status':'CHARGING','temperature':28.8}))
        runner=Mock(return_value=fake)
        result=get_battery(command='/fake/termux-battery-status',runner=runner)
        self.assertEqual(result['percentage'],42)
        runner.assert_called_once()
        self.assertEqual(runner.call_args.kwargs['timeout'],3)
        self.assertIsNone(result['remaining_hours_estimate'])

    def test_cpu_and_memory_measurement_helpers(self):
        self.assertEqual(cpu_percent((100,30),(200,70)),60)
        self.assertIsNone(cpu_percent((100,30),(100,30)))
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'meminfo'
            p.write_text('MemTotal: 4000000 kB\nMemAvailable: 1000000 kB\n')
            self.assertEqual(memory_stats(p)['percent'],75)
            self.assertEqual(memory_stats('/nonexistent-kale-mem-file')['percent'],None)

    def test_monitor_sampling_cadence(self):
        tick=[100.0]
        battery=Mock(return_value={'available':True,'percentage':60})
        obj=DeviceMonitor(clock=lambda:tick[0],battery=battery)
        self.assertEqual(obj.snapshot(chat_users=3)['online_chat_users'],3)
        self.assertEqual(battery.call_count,1)
        tick[0]=115
        obj.snapshot();self.assertEqual(battery.call_count,1)  # 35s eco cadence
        tick[0]=136
        obj.snapshot();self.assertEqual(battery.call_count,2)
        self.assertFalse(obj.set_eco(False))
        tick[0]=149
        obj.snapshot();self.assertEqual(battery.call_count,3)
        with self.assertRaises(ValueError):obj.set_eco('false')

    def test_admin_remote_acl_header_spoof_rejected(self):
        self.assertTrue(server.admin_allowed('127.0.0.1','127.0.0.1:8090'))
        self.assertTrue(server.admin_allowed('::1','localhost:8090'))
        self.assertFalse(server.admin_allowed('192.168.43.7','127.0.0.1:8090'))
        self.assertFalse(server.admin_allowed('127.0.0.1','evil.example:8090'))
        self.assertFalse(server.admin_allowed('192.168.43.7','localhost:8090'))

    def test_termux_script_and_precache(self):
        p=(ROOT/'deploy/install-24x7.sh').read_text()
        self.assertIn('~/.termux/boot',p)
        self.assertIn('Termux:Boot',p)
        self.assertNotIn('su -c',p)
        self.assertIn('termux-wake-lock',(ROOT/'tools/kale_supervisor.py').read_text())
        sw=(ROOT/'web/sw.js').read_text()
        self.assertIn('kale-v2.3.0',sw)
        for f in ('/yonetim.html','/assets/device.js','/assets/device.css'):
            self.assertIn(f,sw)
            self.assertTrue((ROOT/'web'/f.lstrip('/')).exists())

    def test_supervisor_status_atomic_write(self):
        from tools.kale_supervisor import write_status
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'s.json'
            write_status(path,state='restarting',restarts=2)
            self.assertEqual(json.loads(path.read_text())['restarts'],2)
            self.assertEqual(path.stat().st_mode & 0o777,0o600)


class ServerRuntimeIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from http.server import ThreadingHTTPServer
        cls.srv=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        cls._old_port=server.PORT
        server.PORT=cls.srv.server_address[1]
        cls.t=threading.Thread(target=cls.srv.serve_forever,daemon=True)
        cls.t.start()
        cls.base=f'http://127.0.0.1:{server.PORT}'

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown();cls.srv.server_close();cls.t.join(timeout=2)
        server.PORT=cls._old_port

    def test_admin_status_and_no_data_leak(self):
        with request.urlopen(self.base+'/api/device/status') as x:
            d=json.load(x)
        self.assertTrue(d['server_running'])
        self.assertIn('battery',d)
        self.assertIn('online_chat_users',d)
        self.assertIsNone(d['hotspot_clients'])
        with request.urlopen(self.base+'/yonetim.html') as x:
            self.assertIn('Sunucu durumu',x.read().decode())

    def test_local_eco_write_and_cross_site_forbidden(self):
        payload=b'{"enabled":false}'
        req=request.Request(self.base+'/api/device/eco',data=payload,headers={
            'Origin':self.base,'Content-Type':'application/json'},method='POST')
        with request.urlopen(req) as x:
            self.assertEqual(json.load(x)['enabled'],False)
        try:
            req=request.Request(self.base+'/api/device/eco',data=payload,headers={
               'Origin':'http://evil.test','Content-Type':'application/json'},method='POST')
            with self.assertRaises(error.HTTPError) as cm:request.urlopen(req)
            self.assertEqual(cm.exception.code,403)
        finally:
            req=request.Request(self.base+'/api/device/eco',data=b'{"enabled":true}',headers={
                'Origin':self.base,'Content-Type':'application/json'},method='POST')
            request.urlopen(req).close()

    def test_admin_host_header_rebinding_forbidden(self):
        req=request.Request(self.base+'/api/device/status',headers={'Host':'evil.example:8090','X-Forwarded-For':'127.0.0.1'})
        with self.assertRaises(error.HTTPError) as cm:request.urlopen(req)
        self.assertEqual(cm.exception.code,403)

if __name__=='__main__':unittest.main()
