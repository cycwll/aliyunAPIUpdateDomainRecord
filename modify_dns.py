#!/usr/bin/env python
#coding: utf-8
import sys,os
import urllib,urllib2
import base64
import hmac
import hashlib
from hashlib import sha1
import time
import uuid
import json
import random
import subprocess

'''
Access Key ID和Access Key Secret由阿里云官方颁发给用户，需严格保密。
RecordId 解析记录的ID ，此参数在添加解析时会返回，在获取域名解析列表时会返回
DomainName 为一级域名
server_ip_list 为可指向的服务器ip，如多个SLB的ip
url 网站首页，如http://www.17wacai.com
'''
access_key_id = "LTAIg1r2ZIQSEs1g"
access_key_secret = "vG5AMtZohEkDk424XInWA14Qi4agY1"
server_address = 'http://alidns.aliyuncs.com/'

global current_server_ip
def percent_encode(encodeStr):
    encodeStr = str(encodeStr)
    res = urllib.quote(encodeStr.decode('utf8').encode('utf8'), '')
    res = res.replace('+', '%20')
    res = res.replace('*', '%2A')
    res = res.replace('%7E', '~')
    return res

def compute_signature(parameters, access_key_secret):
    sortedParameters = sorted(parameters.items(), key=lambda parameters: parameters[0])
    canonicalizedQueryString = ''
    for (k,v) in sortedParameters:
        canonicalizedQueryString += '&' + percent_encode(k) + '=' + percent_encode(v)
    stringToSign = 'GET&%2F&' + percent_encode(canonicalizedQueryString[1:])
    h = hmac.new(access_key_secret + "&", stringToSign, sha1)
    signature = base64.encodestring(h.digest()).strip()
    return signature

def compose_url(user_params):
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time()))
    parameters = { \
            'Format': 'JSON', \
            'Version': '2015-01-09', \
            'AccessKeyId': access_key_id, \
            'SignatureVersion': '1.0', \
            'SignatureMethod': 'HMAC-SHA1', \
            'SignatureNonce': str(uuid.uuid1()), \
            #'RegionId': 'cn-hangzhou',
            'Timestamp': timestamp\
    }
    for key in user_params.keys():
        parameters[key] = user_params[key]
    signature = compute_signature(parameters, access_key_secret)
    parameters['Signature'] = signature
    url = server_address + "/?" + urllib.urlencode(parameters)
    return url

def make_request(user_params, quiet=False):
    global current_server_ip
    url = compose_url(user_params)
    request = urllib2.Request(url)
    try:
        conn = urllib2.urlopen(request)
        response = conn.read()
    except urllib2.HTTPError, e:
        print(e.read().strip())
        raise SystemExit(e)
    try:
        obj = json.loads(response)
        if quiet:
            return obj
    except ValueError, e:
        raise SystemExit(e)
    json.dump(obj, sys.stdout, sort_keys=True, indent=2)
    #获取指定域名当前指向的ip
    current_server_ip = obj["Value"]
    sys.stdout.write('\n')
#print sys.stdin.encoding

def make_modify_request(modify_user_params, quiet=False):
    global current_server_ip
    url = compose_url(modify_user_params)
    request = urllib2.Request(url)
    try:
        conn = urllib2.urlopen(request)
        response = conn.read()
    except urllib2.HTTPError, e:
        print(e.read().strip())
        raise SystemExit(e)
    try:
        obj = json.loads(response)
        if quiet:
            return obj
    except ValueError, e:
        raise SystemExit(e)
    json.dump(obj, sys.stdout, sort_keys=True, indent=2)
    sys.stdout.write('\n')
    print(current_server_ip,server_ip)

if __name__ == '__main__':
    url = 'http://www.17wacai.com/'
    for x in range(1):
        try:
            stat = urllib2.urlopen(url).code
        except urllib2.HTTPError, e:
            stat = e.code
        except urllib2.URLError, e:
            stat = e.reason
    if stat != 200:
        # 定义获取当前dns指向的参数
        serch_user_params = {'Action': 'DescribeDomainRecordInfo', 'RecordId': '3392072854705152'}
        make_request(serch_user_params)
        if os.name == 'nt':
            p = subprocess.Popen(['ping', current_server_ip], stdout=subprocess.PIPE)
            ping_stat = p.stdout.read().find('0%')
        else:
            p = subprocess.Popen(['/bin/ping', '-c 5', current_server_ip], stdout=subprocess.PIPE)
            ping_stat = p.stdout.read().find('5 received')
        if ping_stat == -1:
            # 定义修改DNS指向的参数
            server_ip_list = ["58.211.8.206", "58.211.8.205", "58.211.8.207", "58.211.8.208"]
            server_ip = server_ip_list[random.randint(0, 3)]
            modify_user_params = {'Action': 'UpdateDomainRecord', 'DomainName': 'hlhgy.cn',
                                  'RecordId': '3392072854705152',
                                  "RR": "richtest", "Type": "A", "Value": server_ip}
            while server_ip == current_server_ip:
                server_ip = server_ip_list[random.randint(0, 3)]
            make_modify_request(modify_user_params)