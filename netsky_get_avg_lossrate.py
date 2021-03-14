# netsky
# version:1.0
# author: zhangzhenhui
# email: 639188185@qq.com

#from apscheduler.schedulers.blocking import BlockingScheduler
import pymysql
import re
import time
from datetime import datetime

province_list = ['sichuan', 'jiangxi', 'hebei', 'henan', 'yunnan', 'beijing', 'tianjin', 'shanghai', 'chongqing', 'neimenggu', 'guangxi', 'xizang', 'ningxia', 'xinjiang', 'shanxi', 'shannxi', 'liaoning', 'jilin', 'heilongjiang', 'jiangsu', 'zhejiang', 'anhui', 'fujian', 'shandong', 'hubei', 'hunan', 'guangdong', 'hainan', 'guizhou', 'gansu', 'qinghai']
mysql_cu_lossrate_name_list = []
mysql_cu_latency_name_list = []
mysql_cm_lossrate_name_list = []
mysql_cm_latency_name_list = []
mysql_ct_lossrate_name_list = []
mysql_ct_latency_name_list = []

for i in province_list:
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

def get_avg_lossrate(isp):
    mysql_lossrate_table = 'netsky_lossrate'
    mysql_latency_table = 'netsky_latency'
    avg_lossrate_dict = {}
    avg_lossrate_data = {}
    lossrate_name_list = []
    avg_values_list = []
    db = pymysql.connect(host='***', user='***', password='***', port=3306, db='netsky_{}'.format(isp))
    cursor = db.cursor()
    if isp == 'cu':
        lossrate_name_list = mysql_cu_lossrate_name_list
    elif isp == 'cm':
        lossrate_name_list = mysql_cm_lossrate_name_list
    elif isp == 'ct':
        lossrate_name_list = mysql_ct_lossrate_name_list
    for i in lossrate_name_list:
        sql_last_12hour_lossrate = "select CAST(AVG(value) AS DECIMAL(10,2)) from netsky_lossrate where update_time >=  NOW() - interval 12 hour and name='{}'".format(i)
        cursor.execute(sql_last_12hour_lossrate)
        avg_values = float(re.findall('(?<=\').*?(?=\')', str(cursor.fetchall()))[0])
        avg_values_list.append(avg_values)
        avg_lossrate_dict = dict(zip(lossrate_name_list, avg_values_list))
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(avg_lossrate_dict)
    cursor.close()
    for k,v in avg_lossrate_dict.items():
        avg_lossrate_data = {
            'name': '"{}"'.format(k),
            'value': str(v),
            'update_time': '"{}"'.format(update_time)
        }
        avg_table = 'netsky_avg_lossrate'
        cols = avg_lossrate_data.keys()
        vals = avg_lossrate_data.values()
        cursor = db.cursor()
        sql_update = "INSERT INTO {0} ({1}) VALUES ({2}) ON DUPLICATE KEY UPDATE value={3},update_time={4}".format(avg_table, ','.join(cols), ','.join(vals), avg_lossrate_data['value'], avg_lossrate_data['update_time'])
        cursor.execute(sql_update)
        db.commit()
    print(update_time)
    db.close()

if __name__ == '__main__':
    while True:
        get_avg_lossrate('cu')
        time.sleep(3600)
