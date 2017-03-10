# collect_service_ip_port_to_yed
====
收集服务信息导入数据库，然后根据连接socket情况分析导出为EXCEL，使用yed自动生成服务架构图。
----

----
        收集信息=》存储
        yum install -y python-netifaces MySQL-python
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
初步解决：
    程序匹配更多的项目类型，不仅限于java类的tomcat
未解决：
    ss效率问题
