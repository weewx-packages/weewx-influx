import base64
import http.server
import io
import queue
import ssl
import threading
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

import pytest
import weewx
import weewx.restx
import influx
import backfill


def test_unit_labels_follow_each_record_and_preserve_overrides():
    worker = influx.InfluxThread(queue.Queue(), database='x', create_database=False)
    for units, temperature, field in [(weewx.US,32,'outTemp_F=32.0'),
                                      (weewx.METRIC,0,'outTemp_C=0.0'),
                                      (weewx.US,32,'outTemp_F=32.0')]:
        body = worker.get_post_body({'dateTime':1700000000,'usUnits':units,'outTemp':temperature})[0]
        assert field in body
    worker = influx.InfluxThread(queue.Queue(), database='x', create_database=False,
                                 inputs={'outTemp':{'units':'degree_C','name':'outside'}}, obs_to_upload='inputs')
    for units, temperature in [(weewx.US,32),(weewx.METRIC,0)]:
        body = worker.get_post_body({'dateTime':1700000000,'usUnits':units,'outTemp':temperature})[0]
        assert 'outside=0.0' in body


def test_thread_normalizes_configobj_booleans_for_backfill():
    worker = influx.InfluxThread(queue.Queue(), database='x', create_database=False,
                                 augment_record='false', append_units_label='false')
    class UnusedArchive:
        def getSql(self, *args):
            pytest.fail('augment_record=false must not query the archive')
    record = worker.get_record({'dateTime':1700000000,'usUnits':weewx.US,'outTemp':0}, UnusedArchive())
    assert 'outTemp=0.0' in worker.get_post_body(record)[0]


@pytest.fixture
def receiver():
    received=[]

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            received.append((self.path, dict(self.headers), self.rfile.read(int(self.headers['Content-Length'])).decode()))
            self.send_response(200 if self.path.startswith('/query?') else 204)
            self.end_headers()
            if self.path.startswith('/query?'):
                self.wfile.write(b'{"results":[{}]}')

        def log_message(self,*args):
            pass

    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        yield 'http://127.0.0.1:%d'%server.server_port,received
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_v1_hyphen_database_admin_auth_and_204_write(receiver):
    url,received=receiver
    worker=influx.InfluxThread(queue.Queue(),database='weewx-docker',server_url=url,username='writer',password='write',dbadmin_username='admin',dbadmin_password='create',tags=['station=A','field=C'])
    path,headers,_=received[0]
    assert parse_qs(urlsplit(path).query)['q']==['CREATE DATABASE "weewx-docker"']
    assert headers['Authorization']=='Basic '+base64.b64encode(b'admin:create').decode()
    record={'dateTime':1700000000,'usUnits':weewx.US,'outTemp':0,'binding':'archive'}
    worker.process_record(record,None)
    path,headers,body=received[1]
    assert parse_qs(urlsplit(path).query)['db']==['weewx-docker']
    assert headers['Authorization']=='Basic '+base64.b64encode(b'writer:write').decode()
    assert ',station=A,field=C ' in body
    assert 'outTemp_F=0.0' in body
    assert body.endswith('1700000000000000000')
    assert record['binding']=='archive'


def test_v2_token_encoded_names_and_loop_bucket(receiver):
    url,received=receiver
    worker=influx.InfluxThread(queue.Queue(),version='2',org='rain & sun',bucket='Weather/archive',loop_bucket='Weather/loop',token='local-token',server_url=url)
    worker.process_record({'dateTime':1700000000,'usUnits':weewx.US,'outTemp':32,'binding':'loop'},None)
    assert len(received)==1
    path,headers,body=received[0]
    assert urlsplit(path).path=='/api/v2/write'
    assert parse_qs(urlsplit(path).query)=={'org':['rain & sun'],'bucket':['Weather/loop'],'precision':['ns']}
    assert headers['Authorization']=='Token local-token'
    assert ',binding=loop ' in body


def test_history_preserves_each_timestamp(receiver):
    url,received=receiver
    worker=influx.InfluxThread(queue.Queue(),database='Weather',server_url=url,create_database=False)
    records=[{'dateTime':1600000000+i*300,'usUnits':weewx.US,'outTemp':i} for i in range(3)]
    assert backfill.replay(worker,records)==3
    assert [int(body.rsplit(' ',1)[1]) for _,_,body in received]==[r['dateTime']*10**9 for r in records]


@pytest.mark.parametrize('status,error',[(401,weewx.restx.BadLogin),(403,weewx.restx.BadLogin),(404,weewx.restx.AbortedPost),(405,weewx.restx.AbortedPost)])
def test_permanent_errors_report_actual_http_status(status,error):
    worker=influx.InfluxThread(queue.Queue(),database='x',create_database=False)
    response=HTTPError('http://localhost/write',status,'fixture',{},io.BytesIO(b'{"error":"fixture"}'))
    with pytest.raises(error):
        worker.handle_exception(response,1)


def test_tls_verifies_by_default(monkeypatch):
    worker=influx.InfluxThread(queue.Queue(),database='x',create_database=False,server_url='https://localhost:443')
    contexts=[]
    monkeypatch.setattr(influx,'urlopen',lambda *args,**kw:contexts.append(kw['context']))
    worker.post_request(worker.get_request(worker.format_url({})),'x value=0 1700000000')
    assert contexts[0].verify_mode==ssl.CERT_REQUIRED
    assert contexts[0].check_hostname


@pytest.mark.parametrize('options',[{'version':2},{'version':3},{'database':'x','server_url':'host:8086'}])
def test_invalid_config_fails_before_thread_start(options):
    with pytest.raises(ValueError):
        influx.InfluxThread(queue.Queue(),create_database=False,**options)


def test_real_tls_rejects_unknown_ca_and_accepts_explicit_ca(tmp_path):
    import subprocess
    cert=tmp_path/'cert.pem'
    key=tmp_path/'key.pem'
    subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(cert),'-days','1','-subj','/CN=localhost','-addext','subjectAltName=IP:127.0.0.1'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    received=[]

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            received.append(self.rfile.read(int(self.headers['Content-Length'])))
            self.send_response(204)
            self.end_headers()

        def log_message(self,*args):
            pass

    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
    context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert,key)
    server.socket=context.wrap_socket(server.socket,server_side=True)
    thread=threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        url='https://127.0.0.1:%d'%server.server_port
        worker=influx.InfluxThread(queue.Queue(),database='x',server_url=url,create_database=False,timeout=1)
        from urllib.error import URLError
        with pytest.raises(URLError):
            worker.post_request(worker.get_request(worker.format_url({})),'outTemp value=0 1')
        worker.ca_file=str(cert)
        with worker.post_request(worker.get_request(worker.format_url({})),'outTemp value=0 1') as response:
            assert response.status==204
        assert received==[b'outTemp value=0 1']
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_prerelease_of_newer_weewx_is_supported():
    assert influx._version_key('5.2.0b1') > influx._version_key('3.5.0')
    assert influx._version_key('3.5.0b1') < influx._version_key('3.5.0')


def test_klimalogg_binding_and_custom_values_reach_receiver(receiver,monkeypatch,tmp_path):
    import configobj
    from types import SimpleNamespace
    url,received=receiver
    config=configobj.ConfigObj({'StdRESTful':{'Influx':{'database':'klima','server_url':url,'create_database':False,'data_binding':'kl_binding'}},'DataBindings':{'kl_binding':{'database':'kl_sqlite'}},'Databases':{'kl_sqlite':{'driver':'weedb.sqlite','root':str(tmp_path),'database_name':'weewx-kl.sdb'}}})

    class Engine:
        def bind(self,*args):
            pass

    monkeypatch.setattr(influx.InfluxThread,'start',lambda self:None)
    service=influx.Influx(Engine(),config)
    assert service.archive_thread.manager_dict['database_dict']['database_name']=='weewx-kl.sdb'
    service.new_archive_record(SimpleNamespace(record={'dateTime':1700000000,'usUnits':weewx.METRIC,'temp0':0,'humidity0':44}))
    service.archive_thread.process_record(service.archive_queue.get_nowait(),None)
    assert 'temp0=0.0' in received[0][2]
    assert 'humidity0=44.0' in received[0][2]
