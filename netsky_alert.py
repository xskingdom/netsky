# netsky
# version:1.0
# author: zhangzhenhui
# email: 639188185@qq.com

import pymysql
import requests
import re
import time
import pymysql
from datetime import datetime
 
paras = {
    'ISP': {
        'CU': '中国联通',
        'CT': '中国电信',
        'CM': '中国移动',
        'Ali': '阿里云'
    },
    'ISP_short': {
        'CU': '联通',
        'CT': '电信',
        'CM': '移动',
        'Ali': '阿里云'
    },
    'ISP_link': {
        'CU': 'https://sentry-grafana.***.cn/',
        'CT': 'https://sentry-grafana.***.cn/',
        'CM': 'https://sentry-grafana.***.cn/'
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
    'pushgatewayurl': 'http://***:9091'
}
 
provinces_list = ['sichuan', 'jiangxi', 'hebei', 'henan', 'yunnan', 'beijing', 'tianjin', 'shanghai', 'chongqing', 'neimenggu', 'guangxi', 'xizang', 'ningxia', 'xinjiang', 'shanxi', 'shannxi', 'liaoning', 'jilin', 'heilongjiang', 'jiangsu', 'zhejiang', 'anhui', 'fujian', 'shandong', 'hubei', 'hunan', 'guangdong', 'hainan', 'guizhou', 'gansu', 'qinghai']
mysql_cu_lossrate_name_list = []
mysql_cu_latency_name_list = []
mysql_cm_lossrate_name_list = []
mysql_cm_latency_name_list = []
mysql_ct_lossrate_name_list = []
mysql_ct_latency_name_list = []
 
for i in provinces_list:
    mysql_cu_lossrate_name = 'netsky_CU_{}_lossrate'.format(i)
    mysql_cu_latency_name = 'netsky_CU_{}_latency'.format(i)
    mysql_cm_lossrate_name = 'netsky_CM_{}_lossrate'.format(i)
    mysql_cm_latency_name = 'netsky_CM_{}_latency'.format(i)
    mysql_ct_lossrate_name = 'netsky_CT_{}_lossrate'.format(i)
    mysql_ct_latency_name = 'netsky_CT_{}_latency'.format(i)
    mysql_cu_lossrate_name_list.append(mysql_cu_lossrate_name)
    mysql_cu_latency_name_list.append(mysql_cu_latency_name)
    mysql_cm_lossrate_name_list.append(mysql_cm_lossrate_name)
    mysql_cm_latency_name_list.append(mysql_cm_latency_name)
    mysql_ct_lossrate_name_list.append(mysql_ct_lossrate_name)
    mysql_ct_latency_name_list.append(mysql_ct_latency_name)
 
def get_fping_data(isp):
    province_list = []
    province_ZH_list = []
    diff_lossrate_list = []
    province_list2 = []
    province_ZH_list2 = []
    diff_lossrate_list2 = []
 
    db = pymysql.connect(host='***', user='***', password='***', port=3306, db='netsky_{}'.format(isp))
    if isp == 'cu':
        lossrate_name_list = mysql_cu_lossrate_name_list
    elif isp == 'cm':
        lossrate_name_list = mysql_cm_lossrate_name_list
    elif isp == 'ct':
        lossrate_name_list = mysql_ct_lossrate_name_list
    cursor = db.cursor()
    mediumloss_province_dict = {}
    heavyloss_province_dict = {}
    for values in lossrate_name_list:
        sql_last_lossrate = "select value from netsky_lossrate where name='{0}' order by update_time desc limit 1".format(values)
        sql_last12hour_avg_lossrate = "select value from netsky_avg_lossrate where name='{0}'".format(values)
        cursor.execute(sql_last_lossrate)
        last_lossrate = float(re.findall('(?<=\(\().*?(?=,\))', str(cursor.fetchall()))[0])
        cursor.execute(sql_last12hour_avg_lossrate)
        last12hour_avg_lossrate = float(re.findall('(?<=\(\().*?(?=,\))', str(cursor.fetchall()))[0])
        diff_lossrate = round(float(last_lossrate - last12hour_avg_lossrate), 2)
        if diff_lossrate <= 0:
            diff_lossrate = 0
        province = str(values.split('_')[2])
        province_ZH = paras['provs'][province]
        metrics_diff_lossrate = 'netsky_%s_%s_diff_lossrate{IDC=\"DC01\", Out_ISP=\"世纪互联出口\", Target_ISP=\"%s\", Target_Province=\"%s\", Monitor_item=\"异常率突增\"} %s' %(isp, province, province_ZH, paras['ISP'][isp.upper()], diff_lossrate)
        headers = {'X-Requested-With': 'netsky requests', 'Content-type': 'text/xml'}
        pushgateway = '%s/metrics/job/netsky_%s_%s/instance/%s' % (paras['pushgatewayurl'], isp, province, isp)
        request_code = requests.post(pushgateway, data='{0}\n'.format(metrics_diff_lossrate).encode('utf-8'), headers=headers)
        if diff_lossrate > 5 and diff_lossrate < 10:
            province_list.append(province)
            diff_lossrate_list.append(str(diff_lossrate))
            province_ZH_list.append(province_ZH)
        elif diff_lossrate >=10:
            province_list2.append(province)
            diff_lossrate_list2.append(str(diff_lossrate))
            province_ZH_list2.append(province_ZH)
 
    if len(province_list) > 0 and len(province_list) <=3:
        string_province = ','.join([str(i) for i in province_ZH_list])
        medium_string = 'DC01世纪互联出口至全国小于4个地区{0}用户异常率大于5%。'.format(paras['ISP_short'][isp.upper()])
        headers = {'X-Requested-With': 'netsky requests', 'Content-type': 'text/xml'}
        metrics_mediumloss = 'netsky_mediumloss{IDC=\"DC01\", Out_ISP=\"世纪互联出口\", Target_ISP=\"%s\", alarm_tip=\"%s\", link=\"%s\"} 1' %(paras['ISP'][isp.upper()], medium_string, paras['ISP_link'][isp.upper()])
        pushgateway = '%s/metrics/job/netsky_mediumloss/instance/%s' % (paras['pushgatewayurl'], isp)
        request_code = requests.post(pushgateway, data='{0}\n'.format(metrics_mediumloss).encode('utf-8'),headers=headers)
        trigger_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(request_code)
        print(metrics_mediumloss, trigger_time)
    else:
        medium_string = 'DC01世纪互联出口至全国小于4个地区{0}用户异常率大于5%。'.format(paras['ISP_short'][isp.upper()])
        metrics_mediumloss_recover = 'netsky_mediumloss{IDC=\"DC01\", Out_ISP=\"世纪互联出口\", Target_ISP=\"%s\", alarm_tip=\"%s\", link=\"%s\"} 0' %(paras['ISP'][isp.upper()], medium_string, paras['ISP_link'][isp.upper()])
        pushgateway = '%s/metrics/job/netsky_mediumloss/instance/%s' % (paras['pushgatewayurl'], isp)
        request_code = requests.post(pushgateway, data='{0}\n'.format(metrics_mediumloss_recover).encode('utf-8'),headers=headers)
        print(request_code)
        print(metrics_mediumloss_recover)
 
    if len(province_list) >3:
        string_province = ','.join([str(i) for i in province_ZH_list[0:3]])
        heavy_string = 'DC01世纪互联出口至全国4个及以上地区{0}用户异常率大于5%。'.format(paras['ISP_short'][isp.upper()])
        headers = {'X-Requested-With': 'netsky requests', 'Content-type': 'text/xml'}
        metrics_heavyloss = 'netsky_heavyloss{IDC=\"DC01\", Out_ISP=\"世纪互联出口\", Target_ISP=\"%s\", alarm_tip=\"%s\", link=\"%s\"} 1' %(paras['ISP'][isp.upper()], heavy_string, paras['ISP_link'][isp.upper()])
        pushgateway = '%s/metrics/job/netsky_heavyloss/instance/%s' % (paras['pushgatewayurl'], isp)
        request_code = requests.post(pushgateway, data='{0}\n'.format(metrics_heavyloss).encode('utf-8'),headers=headers)
        trigger_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(request_code)
        print(metrics_heavyloss, trigger_time)
    else:
        heavy_string = 'DC01世纪互联出口至全国4个及以上地区{0}用户异常率大于5%。'.format(paras['ISP_short'][isp.upper()])
        headers = {'X-Requested-With': 'netsky requests', 'Content-type': 'text/xml'}
        metrics_heavyloss_recover = 'netsky_heavyloss{IDC=\"DC01\", Out_ISP=\"世纪互联出口\", Target_ISP=\"%s\", alarm_tip=\"%s\", link=\"%s\"} 0' % (
        paras['ISP'][isp.upper()], heavy_string, paras['ISP_link'][isp.upper()])
        pushgateway = '%s/metrics/job/netsky_heavyloss/instance/%s' % (paras['pushgatewayurl'], isp)
        request_code = requests.post(pushgateway, data='{0}\n'.format(metrics_heavyloss_recover).encode('utf-8'),headers=headers)
        trigger_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(request_code)
        print(metrics_heavyloss_recover,trigger_time)
    if len(province_list2) > 0:
        string_province = ','.join([str(i) for i in province_ZH_list2])
        critical_string = 'DC01世纪互联出口至若干地区{0}异常率大于10%。'.format(paras['ISP_short'][isp.upper()])
        headers = {'X-Requested-With': 'netsky requests', 'Content-type': 'text/xml'}
        metrics_criticalloss = 'netsky_criticalloss{IDC=\"DC01\", Out_ISP=\"世纪互联出口\", Target_ISP=\"%s\", alarm_tip=\"%s\", link=\"%s\"} 1' % (paras['ISP'][isp.upper()], critical_string, paras['ISP_link'][isp.upper()])
        pushgateway = '%s/metrics/job/netsky_criticalloss/instance/%s' % (paras['pushgatewayurl'], isp)
        request_code = requests.post(pushgateway, data='{0}\n'.format(metrics_criticalloss).encode('utf-8'),headers=headers)
        trigger_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(request_code)
        print(metrics_criticalloss, trigger_time)
    else:
        critical_string = 'DC01世纪互联出口至若干地区{0}异常率大于10%。'.format(paras['ISP_short'][isp.upper()])
        headers = {'X-Requested-With': 'netsky requests', 'Content-type': 'text/xml'}
        metrics_criticalloss_recover = 'netsky_criticalloss{IDC=\"DC01\", Out_ISP=\"世纪互联出口\", Target_ISP=\"%s\", alarm_tip=\"%s\", link=\"%s\"} 0' % (
        paras['ISP'][isp.upper()], critical_string, paras['ISP_link'][isp.upper()])
        pushgateway = '%s/metrics/job/netsky_criticalloss/instance/%s' % (paras['pushgatewayurl'], isp)
        request_code = requests.post(pushgateway, data='{0}\n'.format(metrics_criticalloss_recover).encode('utf-8'), headers=headers)
        trigger_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(request_code)
        print(metrics_criticalloss_recover, trigger_time)
 
if __name__ == '__main__':
    while True:
        get_fping_data('cu')
        time.sleep(10)