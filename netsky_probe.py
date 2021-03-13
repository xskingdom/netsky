# netsky
# version:1.0
# author: zhangzhenhui
# email: 639188185@qq.com

import requests
import os
import threading
#import sqlite3
import shlex
from subprocess import Popen, PIPE
import re
import numpy
from datetime import datetime
import time
import pymysql

paras = {
    'ISP': {
        'CU': '中国联通',
        'CT': '中国电信',
        'CM': '中国移动',
        'Ali': '阿里云'
    },
    'provs': {
        'sichuan': '四川',
        'jiangxi': '江西',
        'hebei': '河北',
        'henan': '河南',
        'yunnan': '云南',
        'beijing': '北京',
        'tianjin': '天津',
        'shanghai': '上海',
        'chongqing': '重庆',
        'neimenggu': '内蒙古',
        'guangxi': '广西',
        'xizang': '西藏',
        'ningxia': '宁夏',
        'xinjiang': '新疆',
        'shanxi': '山西',
        'shannxi': '陕西',
        'liaoning': '辽宁',
        'jilin': '吉林',
        'heilongjiang': '黑龙江',
        'jiangsu': '江苏',
        'zhejiang': '浙江',
        'anhui': '安徽',
        'fujian': '福建',
        'shandong': '山东',
        'hubei': '湖北',
        'hunan': '湖南',
        'guangdong': '广东',
        'hainan': '海南',
        'guizhou': '贵州',
        'gansu': '甘肃',
        'qinghai': '青海',
    },
    'pushgatewayurl': 'http://***9091',
    'CU_ipdata_dir': '/Users/zhangzhenhui/Desktop/python/fping/ipdata/CU/',
    'CM_ipdata_dir': '/Users/zhangzhenhui/Desktop/python/fping/ipdata/CM/',
    'CT_ipdata_dir': '/Users/zhangzhenhui/Desktop/python/fping/ipdata/CT/',
    'Ali_ipdata_dir': '/Users/zhangzhenhui/Desktop/python/fping/ipdata/Ali/'
}

####Setting maxmum threading number#####
threads_max_num = 31
########################################

def get_fping_output(exec_cmd):
    args = shlex.split(exec_cmd)
    proc = Popen(args, stdout=PIPE, stderr=PIPE, encoding='utf8')
    out, err = proc.communicate()
    exitcode = proc.returncode
    return exitcode, out, err

def get_ipfile(ISP):  # ISP == ['CU', 'CT', 'CM', 'Ali']
    filelist = []
    filename = []
    global isp_name
    isp_name = ISP
    fping_dir = os.getcwd()
    for i in os.listdir(fping_dir + '/ipdata/' + ISP):
        if not i.startswith('.'):
            filelist.append(fping_dir + '/ipdata/' + ISP + '/' + i)
            filename.append(i)
    return filelist, filename
    # print(get_ipfile('CU'))

isp_name = ''
def exec_fping(ipfile, ipfilename):
    nowtime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    timestamp = time.time()
    exec_cmd = '/usr/local/fping/sbin/fping -C 1 -A -i 2 -t500 -q -f {0}'.format(ipfile)
    aliveip_list = []
    deadip_list = []
    latency_list = []
    exitcode, out, results = get_fping_output(exec_cmd)
    total_ip_num = results.count('\n')
    for i in results.splitlines():
        i = i.split(':')
        ip = i[0].strip()
        ip_latency = i[1].strip()
        if '-' not in ip_latency and 'duplicate' not in ip_latency:
            latency_list.append(float(ip_latency))
            aliveip_list.append(ip)
        else:
            deadip_list.append(ip)
    aliveip_num = len(aliveip_list)
    deadip_num = len(deadip_list)
    avg_latency = round(numpy.mean(latency_list), 2)
    loss_rate = round(deadip_num / total_ip_num * 100, 2)
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mysql_name_lossrate = 'netsky_%s_%s_lossrate' % (isp_name, ipfilename)
    mysql_value_lossrate = loss_rate
    mysql_province = ipfilename
    db = pymysql.connect(host='***', user='***', password='***', port=3306, db='netsky_{}'.format(isp_name.lower()))
    cursor = db.cursor()
    lossrate_data = {
        'name': '"{}"'.format(mysql_name_lossrate),
        'value': str(mysql_value_lossrate),
        'province': '"{}"'.format(paras['provs'][ipfilename]),
        'update_time': '"{}"'.format(update_time)
    }
    mysql_table = 'netsky_lossrate'
    cols = lossrate_data.keys()
    vals = lossrate_data.values()
    sql_statement = 'INSERT INTO {0} ({1}) VALUES ({2})'.format(mysql_table, ','.join(cols), ','.join(vals))
    cursor.execute(sql_statement)
    db.commit()
    mysql_name_latency = 'netsky_%s_%s_latency' % (isp_name, ipfilename)
    mysql_value_latency = avg_latency
    latency_data = {
        'name': '"{}"'.format(mysql_name_latency),
        'value': str(mysql_value_latency),
        'province': '"{}"'.format(paras['provs'][ipfilename]),
        'update_time': '"{}"'.format(update_time)
    }
    mysql_table = 'netsky_latency'
    cols = latency_data.keys()
    vals = latency_data.values()
    sql_statement = 'INSERT INTO {0} ({1}) VALUES ({2})'.format(mysql_table, ','.join(cols), ','.join(vals))
    cursor.execute(sql_statement)
    db.commit()
    mysql_name_latency = 'netsky_%s_%s_latency' % (isp_name, ipfilename)
    mysql_value_latency = avg_latency
    metrics_list = []
    metrics_lossrate = 'netsky_%s_%s_lossrate{IDC=\"DC01\", ISP=\"***出口\", Target_province=\"%s\", Monitor_item = \"丢包率\"} %s' %(isp_name, ipfilename, paras['provs'][ipfilename], loss_rate)
    metrics_list.append(metrics_lossrate)
    metrics_latency = 'netsky_%s_%s_latency{IDC=\"DC01\", ISP=\"***出口\", Target_province=\"%s\", Monitor_item = \"平均时延\"} %s' %(isp_name, ipfilename, paras['provs'][ipfilename], avg_latency)
    metrics_list.append(metrics_latency)
    headers = {'X-Requested-With': 'netsky requests', 'Content-type': 'text/xml'}
    for metrics in metrics_list:
        pushgateway = '%s/metrics/job/netsky_%s_%s/instance/%s' % (paras['pushgatewayurl'], isp_name, ipfilename, isp_name)
        request_code = requests.post(pushgateway, data='{0}\n'.format(metrics).encode('utf-8'), headers=headers)

def get_cu_fping_results():
    threads = []
    n = 1
    filelist, filename = get_ipfile('CU')
    for ipfile, ipfilename in zip(filelist, filename):
        threads.append(threading.Thread(target=exec_fping, args=(ipfile, ipfilename)))
        if n % threads_max_num == 0:
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            threads = []
        n = n + 1
        if n - 1 == len(filename):
            for t in threads:
                t.start()
            for t in threads:
                t.join()

def get_cm_fping_results():
    threads = []
    n = 1
    filelist, filename = get_ipfile('CM')
    for ipfile, ipfilename in zip(filelist, filename):
        threads.append(threading.Thread(target=exec_fping, args=(ipfile, ipfilename)))
        if n % threads_max_num == 0:
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            threads = []
        n = n + 1
        if n - 1 == len(filename):
            for t in threads:
                t.start()
            for t in threads:
                t.join()

def get_ct_fping_results():
    threads = []
    n = 1
    filelist, filename = get_ipfile('CT')
    for ipfile, ipfilename in zip(filelist, filename):
        threads.append(threading.Thread(target=exec_fping, args=(ipfile, ipfilename)))
        if n % threads_max_num == 0:
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            threads = []
        n = n + 1
        if n - 1 == len(filename):
            for t in threads:
                t.start()
            for t in threads:
                t.join()

while True:
    get_cu_fping_results()
