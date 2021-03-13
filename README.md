# netsky
## IDC多出口外网质量监控

基于python3 threading模块实现IDC出口至全国31个省、直辖市ping质量监控（10s左右可完成100w左右目标地址ping结果汇总），各地区ping丢包率和异常率存入mysql，并吐给prometheus实现告警，通过grafana实现前端展示。（后续版本会增加自动更新地址库、异常时刻自动发起traceroute，mtr方便向运营商报告障）

### 注意
每个省份会开一个线程，同一ISP默认会开31个线程，实际部署测试建议不同运营商分开部署，不同ISP只需要修改每个探测脚本中最后执行的运营商变量或执行对应运营商函数。

### 安装依赖

~~~bash
```
# 安装python3.9.2
yum install -y libffi-devel zlib* openssl-devel -y
wget https://www.python.org/ftp/python/3.9.2/Python-3.9.2.tgz
tar -zxvf Python-3.9.2.tgz
cd Python-3.9.2/
./configure --prefix=/usr/local/python3.9 --with-ssl
make && make install

# 修改软连接
ln -fs /usr/local/python3.9/bin/python3.9 /usr/bin/python3.9
ln -fs /usr/local/python3.9/bin/pip3.9 /usr/bin/pip3.9
 
# 修改yum配置文件第一行为：!/usr/bin/python2.7
vim /usr/bin/yum
vim /usr/libexec/urlgrabber-ext-down

# 安装模块
pip3.9 install requests -i http://pypi.douban.com/simple --trusted-host pypi.douban.com
pip3.9 install numpy -i http://pypi.douban.com/simple --trusted-host pypi.douban.com
pip3.9 install pymysql -i http://pypi.douban.com/simple --trusted-host pypi.douban.com

# fping5.0
wget http://www.fping.org/dist/fping-5.0.tar.gz
tar -zxvf fping-5.0.tar.gz
cd fping-5.0
./configure --prefix=/usr/local/fping
make && make install
 
vim /etc/profile
# fping-5.0
export PATH=/usr/local/fping/sbin/:$PATH
# end
source /etc/profile

# mysql5.7
wget -i -c http://dev.mysql.com/get/mysql57-community-release-el7-10.noarch.rpm
yum -y install mysql57-community-release-el7-10.noarch.rpm
yum -y install mysql-community-server
 
systemctl start mysqld.service
systemctl enable mysqld.service
 
grep "A temporary password" /var/log/mysqld.log

mysql_secure_installation
mysql -uroot -p

# 延迟丢包率表结构
CREATE DATABASE netsky_cu DEFAULT CHARSET utf8 COLLATE utf8_general_ci;
CREATE DATABASE netsky_cm DEFAULT CHARSET utf8 COLLATE utf8_general_ci;
CREATE DATABASE netsky_ct DEFAULT CHARSET utf8 COLLATE utf8_general_ci;
 
CREATE TABLE IF NOT EXISTS `netsky_lossrate`(
`netsky_lossrate_id` INT UNSIGNED AUTO_INCREMENT,
`name` varchar(40) DEFAULT NULL,
`value` FLOAT,
`province` varchar(40) DEFAULT NULL,
`update_time` datetime NOT NULL,
PRIMARY KEY ( `netsky_lossrate_id` )
)ENGINE=InnoDB DEFAULT CHARSET=utf8;
 
CREATE TABLE IF NOT EXISTS `netsky_latency`(
`netsky_latency_id` INT UNSIGNED AUTO_INCREMENT,
`name` varchar(40) DEFAULT NULL,
`value` FLOAT,
`province` varchar(40) DEFAULT NULL,
`update_time` datetime NOT NULL,
PRIMARY KEY ( `netsky_latency_id` )
)ENGINE=InnoDB DEFAULT CHARSET=utf8;
 
CREATE TABLE IF NOT EXISTS `netsky_avg_lossrate`(
`name` varchar(40) NOT NULL,
`value` FLOAT,
`update_time` datetime NOT NULL,
PRIMARY KEY ( `name` )
)ENGINE=InnoDB DEFAULT CHARSET=utf8;
 
# 创建时间维度索引
create index index_netsky_lossrate_updatetime on netsky_lossrate (update_time);
```
~~~

### 探测程序介绍

1、netsky_probe.py：netsky主程序，用于发起对目标省份的探测需求，汇总各省目标地址库的丢包率和延迟，吐给prometheus和mysql。

2、netsky_get_avg_lossrate.py：该程序用于求过去12小时各省平均丢包率，并将结果存到对应运营商的数据库内。

3、netsky_alert.py：该程序用于diff 当前和last12小时lossrate相差，并吐给prometheus。

### 修改程序中数据库信息及对应告警条目信息

### 使用

```bash
nohup python3.9 netsky_probe.py > ./netsky_probe.log 2>&1 &
nohup python3.9 netsky_get_avg_lossrate.py > ./netsky_get_avg_lossrate.log 2>&1 &
nohup python3.9 netsky_alert.py > ./netsky_alert.log 2>&1 &
```

### 效果展示
![image](https://github.com/arnohub/netksy/blob/main/example.png)
