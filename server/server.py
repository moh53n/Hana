import flask
from flask import request, jsonify, abort
import peewee as pw
import datetime
import random
import traceback

db = pw.SqliteDatabase('server.db', pragmas={
    'journal_mode': 'wal',
    'cache_size': -1024 * 64})

class BaseModel(pw.Model):
    """A base model that will use our MySQL database"""
    class Meta:
        database = db

class sensors(BaseModel):
    sid = pw.CharField()
    shash = pw.CharField()
    register_date = pw.DateTimeField()
    ip = pw.CharField()
    asn = pw.CharField()
    region = pw.CharField()
    city = pw.CharField()
    last_update = pw.DateTimeField()

class secdns_test(BaseModel):
    date = pw.DateTimeField()
    sid = pw.CharField()
    register_date = pw.DateTimeField()
    resolver = pw.CharField()
    mode = pw.CharField()
    result = pw.CharField()

class host_test(BaseModel):
    date = pw.DateTimeField()
    sid = pw.CharField()
    register_date = pw.DateTimeField()
    host = pw.CharField()
    sec_resolver = pw.CharField()
    sec_resolved = pw.CharField()
    norm_resolved = pw.CharField()
    norm_google_resolved = pw.CharField()
    sec_latency = pw.CharField()
    norm_latency = pw.CharField()

app = flask.Flask(__name__)
app.config["DEBUG"] = True


@app.route('/api/v1/dns-outage', methods=['GET'])
def dns_outage(): 
    results = []
    hosts = []
    yesterday = datetime.datetime.now() - datetime.timedelta(hours = 24)
    dnses = ['DoT/DoH', 'UDP ISP', 'UDP Google']
    for dns in dnses:
        this = {}
        this['name'] = dns
        dps = []
        done = 0
        pos = 0
        host_test.sec_resolved, host_test.norm_resolved, host_test.norm_google_resolved
        if dns == 'DoT/DoH':
            test = host_test.sec_resolved
        elif dns == 'UDP ISP':
            test = host_test.norm_resolved
        elif dns == 'UDP Google':
            test = host_test.norm_google_resolved
        for item in host_test.select(host_test.date, test).where((host_test.date >= yesterday)):
            if dns == 'DoT/DoH':
                test = item.sec_resolved
            elif dns == 'UDP ISP':
                test = item.norm_resolved
            elif dns == 'UDP Google':
                test = item.norm_google_resolved
            if test == 'False':
                l = 1
            else: l = 0
            t = int(datetime.datetime.strptime(str(item.date), "%Y-%m-%d %H:%M:%S.%f").replace(second=0).timestamp())
            if done == 0:
                done = t
            if t == done or t < done + 120:
                pos += l
            else:
                dps.append({'x': done, 'y': pos})
                pos = l
                done = t
        this['dps'] = dps
        results.append(this)
    res = jsonify(results)
    res.headers.add('Access-Control-Allow-Origin', '*')
    return res


@app.route('/api/v1/daily-ping', methods=['GET'])
def ping_chart():
    if 'sensor' in request.args:
        sid = int(request.args['sensor'])
    else:
        return "Error: No sensor field provided. Please specify a sensor."
    
    results = []
    hosts = []
    yesterday = datetime.datetime.now() - datetime.timedelta(hours = 24)
    for item in host_test.select(host_test.host).distinct().where(host_test.date >= yesterday):
        hosts.append(item.host)
    for host in hosts:
        this = {}
        this['name'] = host
        dps = []
        for item in host_test.select(host_test.date, host_test.norm_latency).where((host_test.date >= yesterday) & (host_test.host == host) & (host_test.sid == sid)):
            if item.norm_latency != 'False':
                l = item.norm_latency
            else: l = 0
            dps.append({'x': int(datetime.datetime.strptime(str(item.date), "%Y-%m-%d %H:%M:%S.%f").replace(second=0).timestamp()), 'y': float(l)})
        this['dps'] = dps
        results.append(this)
    res = jsonify(results)
    res.headers.add('Access-Control-Allow-Origin', '*')
    return res


@app.route('/api/v1/submit', methods=['POST'])
def submit():
    if not request.json:
        abort(400)
    for s in request.json:
        if s['type'] == 'secdns':
            secdns_test.create(
                date = datetime.datetime.fromtimestamp(s['date']), 
                sid = sensors.select(sensors.sid).distinct().where(sensors.shash == s['shash'])[0].sid,
                register_date = datetime.datetime.now(),
                resolver = s['resolver'],
                mode = s['mode'],
                result = s['result']
            )
        elif s['type'] == 'host':
            host_test.create(
                date = datetime.datetime.fromtimestamp(s['date']), 
                sid = sensors.select(sensors.sid).distinct().where(sensors.shash == s['shash'])[0].sid,
                register_date = datetime.datetime.now(),
                host = s['host'],
                sec_resolver = s['sec_resolver'],
                sec_resolved = s['sec_resolved'],
                norm_resolved = s['norm_resolved'],
                norm_google_resolved = s['norm_google_resolved'],
                sec_latency = s['sec_latency'],
                norm_latency = s['norm_latency']
            )
        else: abort(400)
    sensors.update(last_update=datetime.datetime.now()).where((sensors.shash == request.json[0]['shash'])).execute()
    return "OK", 201

@app.route('/api/v1/register', methods=['GET'])
def register():
    if 'shash' in request.args and 'ip' in request.args and 'asn' in request.args and 'region' in request.args and 'city' in request.args:
        shash = request.args['shash']
        ip = request.args['ip']
        asn = request.args['asn']
        region = request.args['region']
        city = request.args['city']
    else:
        traceback.print_exc()
        abort(400)
    try:
        sid = sensors.select(sensors.sid).distinct().where(sensors.shash == shash)[0].sid
    except:
        traceback.print_exc()
        abort(400)
    try:
        sensors.create(sid=sid, shash=shash, register_date=datetime.datetime.now(), ip=ip, asn=asn, region=region, city=city, last_update=datetime.datetime.now())
        return "OK", 201
    except:
        traceback.print_exc()
        abort(500)

@app.route('/api/v1/register-new', methods=['GET'])
def register_new():
    if 'ip' in request.args and 'asn' in request.args and 'region' in request.args and 'city' in request.args:
        ip = request.args['ip']
        asn = request.args['asn']
        region = request.args['region']
        city = request.args['city']
    else:
        abort(400)
    try:
        sid = sensors.select(sensors.sid).order_by(sensors.sid.desc())
        #print(sid)
        if len(sid) > 0:
            sid = int(sid[0].sid)
        else: sid = 0
        shash = str(random.getrandbits(128))
        sensors.create(sid=sid+1, shash=shash, register_date=datetime.datetime.now(), ip=ip, asn=asn, region=region, city=city, last_update=datetime.datetime.now())
        return shash, 201
    except:
        traceback.print_exc()
        abort(500)


db.connect()
db.create_tables([sensors, secdns_test, host_test])
app.run(host='0.0.0.0')
