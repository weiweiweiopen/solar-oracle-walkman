import unittest,sys,tempfile,threading,json,csv,io,datetime as dt,urllib.request,urllib.error
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import publish_site as pub
import wifi_receiver as rx
rx.TOKEN = "test-fixture-only"

class DualTests(unittest.TestCase):
 def test_report_boundaries_and_raw_preservation(self):
  pub.select_channel(pub.CONFIG['channels'][0])
  source='timestamp,raw,voltage_mV,voltage_V,ambient_temp_C,humidity_pct,pressure_hPa,lux,mcu_temp_C\n'
  for day in ['2026-10-02T23:59:59+08:00','2026-10-03T00:00:00+08:00','2026-10-13T23:59:59+08:00','2026-10-14T12:00:00+08:00']:
   source+=day+',1234,500,0.5,25,50,1000,100,30\n'
  rows=pub.parse_readings(source.encode())
  self.assertEqual([r['valid'] for r in rows],[True,False,False,False])
  output=list(csv.DictReader(io.StringIO(pub.serialize_public_readings(rows).decode())))
  self.assertTrue(all(r['raw']=='1234' and r['voltage_mV']=='500' for r in output))
  daily,_,_=pub.derive_daily(rows,dt.datetime(2026,10,15,tzinfo=pub.TAIPEI))
  self.assertTrue(all(r['valid_samples']==0 and r['retention_pct'] is None and r['moving_7d_median_pct'] is None for r in daily[1:]))
 def test_reconnection_confirmation_boundary_and_ranges(self):
  pub.select_channel(pub.CONFIG['channels'][0])
  self.assertEqual(pub.CHANNEL['confirmed_reconnected_at'],'2026-10-14T18:33:00+08:00')
  source='timestamp,raw,voltage_mV,voltage_V,ambient_temp_C,humidity_pct,pressure_hPa,lux,mcu_temp_C\n'
  for timestamp,voltage in [('2026-10-14T18:32:59+08:00',500),('2026-10-14T18:33:00+08:00',500),('2026-10-14T10:33:00Z',1300)]:
   source+=f'{timestamp},1234,{voltage},0.5,25,50,1000,100,30\n'
  rows=pub.parse_readings(source.encode())
  self.assertEqual([r['valid'] for r in rows],[False,True,False])
  self.assertEqual([r['quality_reason'] for r in rows],['sensor_disconnected_invalid_measurement','included','invalid_sensor_range_or_missing'])
  self.assertFalse(pub.disconnected_at(rows[1]['timestamp']))
  self.assertFalse(pub.disconnected_at(rows[2]['timestamp']))
  output=list(csv.DictReader(io.StringIO(pub.serialize_public_readings(rows).decode())))
  self.assertEqual([r['voltage_mV'] for r in output],['500','500','1300'])
  daily,_,_=pub.derive_daily(rows,dt.datetime(2026,10,15,tzinfo=pub.TAIPEI))
  self.assertEqual(daily[0]['valid_samples'],1)
  pub.select_channel(pub.CONFIG['channels'][1])
  self.assertTrue(all(r['valid'] for r in pub.parse_readings(source.encode())[:2]))
  pub.select_channel(pub.CONFIG['channels'][0])
 def test_b_no_invented_history(self):
  pub.select_channel(pub.CONFIG['channels'][1])
  with tempfile.TemporaryDirectory() as d:
   pub.SOURCE_CSV=Path(d)/'absent.csv'
   self.assertEqual(pub.read_source(),(b'',[]))
  pub.select_channel(pub.CONFIG['channels'][0])
 def test_receiver_channel_isolation_duplicate_legacy_and_rejection(self):
  with tempfile.TemporaryDirectory() as d:
   rx.BASE=Path(d);rx.LOG=Path(d)/'a.csv';rx.B_LOG=Path(d)/'b.csv';rx.STATUS_LOG=Path(d)/'status.jsonl';rx.LAST_EVENT_KEY=None
   server=rx.ThreadingHTTPServer(('127.0.0.1',0),rx.Handler)
   thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
   def post(payload):
    req=urllib.request.Request('http://127.0.0.1:%s/readings'%server.server_port,data=json.dumps(payload).encode(),headers={'X-DSSC-Token':rx.TOKEN,'Content-Type':'application/json'})
    try:
     with urllib.request.urlopen(req) as response:return response.status
    except urllib.error.HTTPError as e:
     code=e.code;e.close();return code
   data=dict(zip(rx.FIELDS,[111,100,0.1,25,50,1000,100,30]))
   data.update(boot_id=123,report_sequence=1,schema_version=2,device_id=rx.DEVICE_ID,sample_id=rx.SAMPLE_A,gpio=3,channels=[dict(sample_id=rx.SAMPLE_B,gpio=2,raw=222,voltage_mV=700,voltage_V=0.7)])
   try:
    self.assertEqual(post(data),204);self.assertEqual(post(data),204)
    aa=list(csv.DictReader(io.StringIO(rx.LOG.read_text())));bb=list(csv.DictReader(io.StringIO(rx.B_LOG.read_text())))
    self.assertEqual(len(aa),1);self.assertEqual(len(bb),1)
    self.assertEqual(aa[0]['raw'],'111');self.assertEqual(bb[0]['raw'],'222')
    self.assertEqual(bb[0]['voltage_mV'],'700');self.assertEqual(bb[0]['temp_source'],'sht20')
    data['channels'][0]['sample_id']=rx.SAMPLE_A
    self.assertEqual(post(data),400)
    legacy={k:data[k] for k in rx.FIELDS};legacy.update(boot_id=123,report_sequence=2)
    self.assertEqual(post(legacy),204)
    self.assertEqual(len(list(csv.DictReader(io.StringIO(rx.LOG.read_text())))),2)
    self.assertEqual(len(list(csv.DictReader(io.StringIO(rx.B_LOG.read_text())))),1)
   finally:server.shutdown();server.server_close();thread.join()

if __name__=='__main__': unittest.main(verbosity=2)
