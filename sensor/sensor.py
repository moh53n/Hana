import os
import requests

import dns.message
import dns.query
import dns.rdatatype
import random
from time import sleep
import peewee as pw
from datetime import datetime, timezone
import threading
import traceback
import json

global sec_working
sec_working = []




db = pw.SqliteDatabase('sensor.db', pragmas={
    'journal_mode': 'wal',
    'cache_size': -1024 * 64})

class BaseModel(pw.Model):
    """A base model that will use our MySQL database"""
    class Meta:
        database = db

class secdns_test(BaseModel):
    date = pw.DateTimeField()
    resolver = pw.CharField()
    mode = pw.CharField()
    result = pw.CharField()
    sent = pw.CharField()

class test(BaseModel):
    date = pw.DateTimeField()
    host = pw.CharField()
    sec_resolver = pw.CharField()
    sec_resolved = pw.CharField()
    norm_resolved = pw.CharField()
    norm_google_resolved = pw.CharField()
    sec_latency = pw.CharField()
    norm_latency = pw.CharField()
    sent = pw.CharField()

class sensor(BaseModel):
    shash = pw.CharField()


def ip():
    raw = requests.get("https://ipinfo.io")
    raw = raw.json()
    return (raw["ip"], raw["org"], raw['region'], raw['city'])

def ping(host):
    response = os.popen("ping -c 5 " + host).read()
    #print(response)
    if 'time=' in response:
        pingstatus = response.split("rtt min/avg/max/mdev = ")[1].split("/")[1]
    else:
        pingstatus = False

    return pingstatus

def doh(host, provider="cloudflare"):
    if provider == "cloudflare":
        where = 'https://cloudflare-dns.com/dns-query'
    elif provider == "google":
        where = 'https://dns.google/dns-query'
    elif provider == "quad9":
        where = 'https://dns.quad9.net/dns-query'
    else: raise()
    qname = host
    with requests.sessions.Session() as session:
        q = dns.message.make_query(qname, dns.rdatatype.A)
        r = dns.query.https(q, where, session=session, timeout=10.0)
    if len(r.answer) == 0:
        raise()
    return r

def dot(host, provider="cloudflare"):
    if provider == "cloudflare":
        where = '1.1.1.1'
    elif provider == "google":
        where = '8.8.8.8'
    elif provider == "quad9":
        where = '9.9.9.9'
    else: raise()
    qname = host
    q = dns.message.make_query(qname, dns.rdatatype.A)
    r = dns.query.tls(q, where, timeout=10.0)
    if len(r.answer) == 0:
        raise()
    return r

def normal_dns(host, provider="cloudflare", proto="udp"):
    if provider == "cloudflare":
        where = '1.1.1.1'
    elif provider == "google":
        where = '8.8.8.8'
    elif provider == "quad9":
        where = '9.9.9.9'
    elif provider == "system":
        where = '192.168.1.1'
    else: raise()
    qname = host
    q = dns.message.make_query(qname, dns.rdatatype.A)
    if proto == "udp":
        r = dns.query.udp(q, where, timeout=10.0)
    elif proto == "tcp":
        r = dns.query.tcp(q, where, timeout=10.0)
    if len(r.answer) == 0:
        raise()
    return r

def insert(result, mode):
    if mode == "secdns_stat":
        for r in result.keys():
            secdns_test.create(
                date = datetime.now(),
                resolver = str(r).split('_')[0], 
                mode = str(r).split('_')[1], 
                result = str(result[str(r)]), 
                sent = '0'
            )
    elif mode == "test":
        for r in result.keys():
            test.create(
                date = datetime.now(),
                host = str(r),
                sec_resolver = str(result[str(r)]['sec_resolver']),
                sec_resolved = str(result[str(r)]['sec_dns']),
                norm_resolved = str(result[str(r)]['norm_dns']),
                norm_google_resolved = str(result[str(r)]['norm_google_dns']),
                sec_latency = str(result[str(r)]['sec_latency']),
                norm_latency = str(result[str(r)]['norm_latency']),
                sent = '0'
            )
    else: raise()

def register():
    server = "http://127.0.0.1:5000"
    while True:
        try:
            ipp = ip()
            shash = sensor.select()
            query = "?ip=" + ipp[0] + "&asn=" + ipp[1] + "&region=" + ipp[2] + "&city=" + ipp[3]
            if len(shash) > 0:
                shash = shash[0].shash
                query += "&shash=" + shash
                status = requests.get(server + "/api/v1/register" + query)
            else:
                status = requests.get(server + "/api/v1/register-new" + query)
                sensor.create(shash=status.text)
        except: traceback.print_exc()
        sleep(random.uniform(3400,3800))

def report():
    server = "http://127.0.0.1:5000"
    while True:
        sleep(random.uniform(300,500))
        print("report")
        try:
            s = secdns_test.select().where(secdns_test.sent == '0')
            if len(s) > 0:
                pack = []
                final = []
                shash = sensor.select()[0].shash
                for item in s:
                    obj = {}
                    obj['type'] = 'secdns'
                    obj['date'] = (item.date).timestamp()
                    obj['shash'] = shash
                    obj['resolver'] = item.resolver
                    obj['mode'] = item.mode
                    obj['result'] = item.result
                    final.append(obj)
                    pack.append(item.id)
                status = requests.post(server + "/api/v1/submit", json=final)
                if status.status_code == 201:
                    for i in pack:
                        secdns_test.update(sent='1').where(secdns_test.id == i).execute()
                else:
                    raise "err"
            s = test.select().where(test.sent == '0')
            if len(s) > 0:
                pack = []
                final = []
                shash = sensor.select()[0].shash
                for item in s:
                    obj = {}
                    obj['type'] = 'host'
                    obj['date'] = (item.date).timestamp()
                    obj['shash'] = shash
                    obj['host'] = item.host
                    obj['sec_resolver'] = item.sec_resolver
                    obj['sec_resolved'] = item.sec_resolved
                    obj['norm_resolved'] = item.norm_resolved
                    obj['norm_google_resolved'] = item.norm_google_resolved
                    obj['sec_latency'] = item.sec_latency
                    obj['norm_latency'] = item.norm_latency
                    final.append(obj)
                    pack.append(item.id)
                status = requests.post(server + "/api/v1/submit", json=final)
                if status.status_code == 201:
                    for i in pack:
                        test.update(sent='1').where(test.id == i).execute()
                else:
                    raise "err"
        except: traceback.print_exc()
        

def do_dns(host, mode):
    if mode == "cloudflare_doh":
        return doh(host, 'cloudflare')
    elif mode == "google_doh":
        return doh(host, 'google')
    elif mode == "quad9_doh":
        return doh(host, 'quad9')
    elif mode == "cloudflare_dot":
        return dot(host, 'cloudflare')
    elif mode == "google_dot":
        return dot(host, 'google')
    elif mode == "quad9_dot":
        return dot(host, 'quad9')
    else: raise()

def get_secdns_stat():
    global sec_working
    while (True):
        result = {}
        temp_working = []
        rand = [random.uniform(1,5) for i in range(6)]
        try:
            doh("google.com", 'cloudflare')
            result['cloudflare_doh'] = True
            temp_working.append("cloudflare_doh")
        except:
            result['cloudflare_doh'] = False
        sleep(rand[0])
        try:
            doh("google.com", 'google')
            result['google_doh'] = True
            temp_working.append("google_doh")
        except:
            result['google_doh'] = False
        sleep(rand[1])
        try:
            doh("google.com", 'quad9')
            result['quad9_doh'] = True
            temp_working.append("quad9_doh")
        except:
            result['quad9_doh'] = False
        sleep(rand[2])
        try:
            dot("google.com", 'cloudflare')
            result['cloudflare_dot'] = True
            temp_working.append("cloudflare_dot")
        except:
            result['cloudflare_dot'] = False
        sleep(rand[3])
        try:
            dot("google.com", 'google')
            result['google_dot'] = True
            temp_working.append("google_dot")
        except:
            result['google_dot'] = False
        sleep(rand[4])
        try:
            dot("google.com", 'quad9')
            result['quad9_dot'] = True
            temp_working.append("quad9_dot")
        except:
            result['quad9_dot'] = False
        sec_working = temp_working
        insert(result, "secdns_stat")
        sleep(random.uniform(3600,4000))

def host_test(hosts):
    global sec_working
    while (True):
        #print(sec_working)
        result = {}
        random.shuffle(hosts)
        if len(sec_working) == 0:
            sec = False
        else: sec = sec_working[0]
        for host in hosts:
            try:
                sec_dns = do_dns(host, sec).answer
                sec_dns = [str(x).split(' ')[-1] for x in sec_dns]
                sec_dns = ",".join(sec_dns)
            except:
                traceback.print_exc()
                sec_dns = False
            #print(sec_dns)
            sleep(random.uniform(0.5,1.5))
            try:
                norm_dns = normal_dns(host, 'system').answer
                norm_dns = [str(x).split(' ')[-1] for x in norm_dns]
                norm_dns = ",".join(norm_dns)
            except:
                traceback.print_exc()
                norm_dns = False
            sleep(random.uniform(0.5,1.5))
            try:
                norm_google_dns = normal_dns(host, 'google').answer
                norm_google_dns = [str(x).split(' ')[-1] for x in norm_google_dns]
                norm_google_dns = ",".join(norm_google_dns)
            except:
                traceback.print_exc()
                norm_google_dns = False
            sleep(random.uniform(0.5,1.5))
            if sec_dns != False:
                sec_latency = ping(sec_dns)
            else: sec_latency = False
            if norm_dns != False:
                norm_latency = ping(norm_dns)
            else: norm_latency = False
            #traceroute
            result[host] = {
                'sec_resolver' : sec,
                'sec_dns' : sec_dns,
                'norm_dns' : norm_dns,
                'norm_google_dns' : norm_google_dns,
                'sec_latency' : sec_latency,
                'norm_latency' : norm_latency
            }
            sleep(random.uniform(1,3))
        insert(result, "test")
        sleep(random.uniform(40,60))

def main():
    """print(ping("8.8.8.8"))
    print(doh("google.com", 'cloudflare'))
    print(doh("google.com", 'google'))
    print(doh("google.com", 'quad9'))
    print(dot("google.com", 'cloudflare'))
    print(dot("google.com", 'google'))
    print(dot("google.com", 'quad9'))
    print(normal_dns("google.com", 'cloudflare', 'udp'))
    print(normal_dns("google.com", 'google', 'udp'))
    print(normal_dns("google.com", 'quad9', 'udp'))
    print(normal_dns("google.com", 'system', 'udp'))
    print(normal_dns("google.com", 'cloudflare', 'tcp'))
    print(normal_dns("google.com", 'google', 'tcp'))
    print(normal_dns("google.com", 'quad9', 'tcp'))"""
    hosts = [
        "google.com",
        "instagram.com",
        "digikala.com",
        "twitch.tv",
        "aparat.ir",
        "wikipedia.com",
        "whatsapp.com"
    ]
    db.connect()
    db.create_tables([secdns_test, test, sensor])
    reg = threading.Thread(target=register, args=())
    reg.start()
    rep = threading.Thread(target=report, args=())
    rep.start()
    x = threading.Thread(target=get_secdns_stat, args=())
    x.start()
    sleep(90)
    print("Startng main test thread")
    y = threading.Thread(target=host_test, args=(hosts,))
    y.start()

if __name__ == '__main__':
    main()
