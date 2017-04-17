# collect_service_ip_port_to_yed
====
收集服务信息导入数据库，然后根据连接socket情况分析导出为EXCEL，使用yed自动生成服务架构图。
使用saltstack推送。
----
![image](https://github.com/talenhao/collect_service_ip_port_to_yed/blob/master/screenshots/Screenshot_20170328_164815.png?raw=true)
![image](https://github.com/talenhao/collect_service_ip_port_to_yed/blob/master/screenshots/Screenshot_20170328_164828.png?raw=true)
![image](https://github.com/talenhao/collect_service_ip_port_to_yed/blob/master/screenshots/Screenshot_20170328_164843.png?raw=true)
![image](https://github.com/talenhao/collect_service_ip_port_to_yed/blob/master/screenshots/Screenshot_20170328_164854.png?raw=true)
![image](https://github.com/talenhao/collect_service_ip_port_to_yed/blob/master/screenshots/Screenshot_20170328_165002.png?raw=true)
![image](https://github.com/talenhao/collect_service_ip_port_to_yed/blob/master/screenshots/Screenshot_20170417_135813.png?raw=true)
----
        收集信息=》存储

        2017-02-27
            2.6.6版本不支持subprocess.check_out,修改为subprocess.Popen(["ls", "-a"], stdout=subprocess.PIPE).communicate()[0]
        2017-02-28
            使用re重写shell命令部分
            重写数据导入方法
            优化端口扫描方式，节省2/3时间
        2017-03-01
            解决插入数据重复问题
            改写appcolect为类方法
            调整数据录入逻辑
            ip地址不同版本系统获取问题
        2017-03-10
            去掉127.0.0.1监听地址防止端口相同的业务出现错误
        2017-03-13
            程序匹配更多的项目类型，不仅限于java类的tomcat
        2017-03-14
            使用配置文件添加项目匹配。
        2017-03-15
            添加帮助，版本，配置文件等信息
        2017-03-16
            修复porjectname过长被truncate的问题
        2017-03-21
            添加记录原始数据日志功能
            收集完监听pid未处理连接池之间，进程重启有一定机率匹配到其它启动起来占用原来pid，造成匹配信息错误。
            添加pid创建日期判断
        2017-03-22
            listen port, pool ip port去重，节约处理时间
        2017-03-27
            使用multi-threads多线程处理
        2017-03-28
            添加pool列表pid有效判断
            去掉多余self
            部分方法修改成静态方法
            添加网卡ip提示
            修改listen匹配出错问题
            2.6版本release
        2017-03-29
            3.0版本，添加日志模块
        2017-04-07:
            添加twemproxy nutcracker匹配
        2017-04-10
            添加命令行参数处理模块
        2017-04-11
            Centos 6 版本ss命令-o选项不支持超过7个的匹配，升级到最新版本解决。
            创建ss.sls
        2017-04-12
            自动更新数据库信息
        计划添加功能：
            使用psutil模块代替ps,ss收集信息。
            脚本报错发邮件
