#!/bin/env python
# coding=utf-8

# -*- coding:utf-8 -*-

# ******************************************************
# Author       : tianfei hao
# Create Time  : 2017-02-25
# Last modified:
# Email        : talenhAppOp@gmail.com
# Description  : collect listen ip port and connect socket.
# ******************************************************

"""
执行前需要清空的表：pooltable,nodes
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
    使用配置文件添加项目匹配。

"""


from Application_operation import applicationOperation as AppOp
import subprocess
import shlex
import sys
# import os
import re
import netifaces


if sys.version_info < (2, 7):
    # raise RuntimeError('At least Python 3.4 is required')
    print('友情提示：当前系统版本低于2.7，建议升级python版本。')


class AppListen(AppOp):
    """
    收集监听IP及port信息
    收集连接池信息
    """
    
    def __init__(self):
        AppOp.__init__(self)
        # self.projecttable = "application"
        # self.group_table = "appgroup"
        self.projects_name_list = []
    def project_list(self):
        """
        :return: project list
        """
        sql_cmd = "SELECT projectname from %s" % self.projecttable  # self.projecttable来自AppOp
        # print(sql_cmd)
        self.resultCursor.execute(sql_cmd)
        for self.row in self.resultCursor.fetchall():
            print("project name: %s" % self.row)
            self.projects_name_list.append(self.row[0])
        return self.projects_name_list
    
    def collect_pid_list(self, project):
        """
        查找指定程序的PID
        :param project:
        :return:
        """
        self.pid_lists = []
        self.project = project
        print("Find out %s pid number." % self.project)
        # ps aux |grep -E '[D]catalina.home=/data/wire/tomcat'|awk '{print $2}'
        # 1.内容
        # 1命令
        ps_aux_cmd = 'ps aux'
        # 2执行
        ps_aux_result = subprocess.Popen(shlex.split(ps_aux_cmd), stdout=subprocess.PIPE)
        # 3结果
        ps_aux_result_text = ps_aux_result.communicate()[0]  # .decode('utf-8')
            # 2.pattern&compile
            # ps_aux_pattern_tomcat = 'Dcatalina.home=/[-\w]+/%s/tomcat' % self.project
        ps_aux_pattern_tomcat = 'Dcatalina.home=/[-\w]+/%s/(tomcat|server|log)' \
                                    '|\./bin/%s\ -c\ conf/%s\.conf' \
                                    '|./bin/%s'\
                                    '|java\ .*%s-.*\.jar.*zoo.cfg.*'\
                                    '|%s: [\w]+ process'\
                                    '|%s: pool www' \
                                    '|java -cp /etc/%s/conf' \
                                    % (self.project, self.project, self.project, self.project, self.project, self.project, self.project, self.project)
        print("Pattern is %s" % ps_aux_pattern_tomcat)
        ps_aux_compile = re.compile(ps_aux_pattern_tomcat)
        # try:
        # 3.match object
        for ps_aux_result_line in ps_aux_result_text.splitlines():
            ps_aux_re_find = ps_aux_compile.findall(ps_aux_result_line)
            if ps_aux_re_find:
                print("Get： %s " % ps_aux_re_find)
                self.pid = int(ps_aux_result_line.split()[1])
                print('%s has a pid number %s ...' % (self.project, self.pid))
                self.pid_lists.append(self.pid)
            else:
        # except subprocess.CalledProcessError:
                print('%s is not in this host!' % self.project)
        print("project %s pid：%s" % (self.project, self.pid_lists))
        return self.pid_lists
    
    def get_localhost_ip_list(self):
        """
        获取本机所有IP信息
        """
        print('Collect localhost IP addresses.')
        self.card_ip_list = []
        for interface_card in netifaces.interfaces():
            try:
                card_ip_address = netifaces.ifaddresses(interface_card)[netifaces.AF_INET][0]['addr']
            except KeyError:
                print("%s is not have ip" % interface_card)
            else:
                self.card_ip_list.append(card_ip_address)
        # 如果服务监听端口无重复可以打开
        self.card_ip_list_all = self.card_ip_list.remove('127.0.0.1')
        print("Local collect IP: %s" % self.card_ip_list)
        return self.card_ip_list

    def listen_ports(self, pids):
        """
        接收列表[pids]
        :param pids:
        :return:
        """
        self.pidlist = pids
        if not self.pidlist:
            return None
        self.portlists = []
        # 1.内容
        # sscmd = "ss -lntp -4 |grep %s |awk -F: '{print $2}'|awk '{print $1}'" % ipid
        sscmd = 'ss -l -n -p -t'
        sscmd_result = subprocess.Popen(shlex.split(sscmd), stdout=subprocess.PIPE)
        sscmd_result_text = sscmd_result.communicate()[0]  # .decode('utf-8')
        # print("ss -l结果： %s" % sscmd_result_text)
        # 2.pattern&compile
        sscmd_pattern_pid = '|'.join(format(n) for n in self.pidlist)
        print("pattern is :%s" % sscmd_pattern_pid)
        sscmd_compile = re.compile(sscmd_pattern_pid)
        # 3.match object
        for sscmd_result_line in sscmd_result_text.splitlines():
            sscmd_re_findpid = sscmd_compile.findall(sscmd_result_line)
            if sscmd_re_findpid:
                # print(sscmd_result_line)
                self.listenport = sscmd_result_line.split()[3].split(':')[-1].strip()
                # print(self.listenport)
                self.portlists.append(self.listenport)
        print("监听端口接收到的监听列表%s" % self.portlists)
        return self.portlists

    def connectpools(self, ports, pids):
        """

        :param ports:
        :param pids:
        :return: 连接池
        """
        ports = ports
        pids = pids
        self.poollists = []
        print("处理连接池，接收参数端口：%s，进程号：%s" % (ports, pids))
        self.sportline = ["sport neq :%s" % n for n in ports]
        self.sportjoin = ' and '.join(self.sportline)
        # 1.内容
        # ss_cmd = ss -ntp -o state established \'( sport != :%s )\'|grep -E %s|\
        # awk \'{print $4}\'|awk -F \':\' \'{print $(NF-1)\":\" $NF}\'' % (self.port,self.pid)
        ssntpcmd = 'ss -ntp -o state established \\( %s \\)' % self.sportjoin
        print("Begin to execute ss command: %s" % ssntpcmd)
        ssntpcmd_result = subprocess.Popen(shlex.split(ssntpcmd), stdout=subprocess.PIPE)
        ssntpcmd_result_text = ssntpcmd_result.communicate()[0]  # .decode('utf-8')
        # print("ssntpcmd_result_text is %s" % ssntpcmd_result_text)
        # 2.pattern&compile
        ssntpcmd_pattern_pid = ',%s,' % self.pid
        ssntpcmd_compile = re.compile(ssntpcmd_pattern_pid)
        # 3.match object
        for ssntpcmd_result_line in ssntpcmd_result_text.splitlines():
            ssntpcmd_re_findpid = ssntpcmd_compile.findall(ssntpcmd_result_line)
            if ssntpcmd_re_findpid:
                # print("当前连接池匹配行：%s" % ssntpcmd_result_line)
                # print("当前pid匹配结果：%s" % ssntpcmd_re_findpid)
                self.connect_to_ipportlist = ssntpcmd_result_line.split()[3].split(':')[-2:]
                # print("过滤出的连接池IP：port %s" % self.connect_to_ipportlist)
                self.ipportmessage = ':'.join(self.connect_to_ipportlist)
                self.poollists.append(self.ipportmessage)
        print("处理连接池，列表：%s" % self.poollists)
        return self.poollists

    def import2db(self, table, ipportcolumn, projectcolumn, message):
        """
        :param table:
        :param ipportcolumn:
        :param projectcolumn:
        :param message:
        :return:
        """
        if len(message) > 0:
            self.message = message
            self.ipportcolumn = ipportcolumn
            self.table = table
            self.projectcolumn = projectcolumn
            sql_cmd = "INSERT ignore INTO %s (%s,%s) VALUES %s" % (
                self.table,
                self.ipportcolumn,
                self.projectcolumn,
                ','.join(self.message)
            )
            print(sql_cmd)
            self.resultCursor.execute(sql_cmd)
            self.DBcon.commit()
        else:
            print("%s is not have socket." % self.project)

    def start_line(self,info):
        info = info
        print("=" * 80 + "\n process project start : %s \n" % info)

    def end_line(self,info):
        info = info
        print("\n process project finish : %s \n" % info + "=" * 80)

def app_l_collect():
    # 取出应用名称
    # 初始化实例
    print("开始收集...")
    app_listen_instance = AppListen()
    # Get project list
    app_listen_con_db_project_list = app_listen_instance.project_list()
    # some values
    listentable = "listentable"
    listen_ipport_column = 'lipport'
    connectpooltable = "pooltable"
    connectpool_ipport_column = 'conipport'
    projectcolumn = 'projectname'

    #
    for project_item in app_listen_con_db_project_list:  # project name
        to_db_ipport_project = []
        to_db_conipport_project = []
        # rows, columns = os.popen('stty size', 'r').read().split()
        # print("=" * int(columns) + "\n 1.process project : %s \n" % project_item)
        # Split line
        app_listen_instance.start_line(project_item)
        # pid list
        from_db_pid_list = app_listen_instance.collect_pid_list(project_item)
        if not from_db_pid_list:
            print("Have no project %s" % project_item)
            app_listen_instance.end_line(project_item)
            continue
        else:
            # port list
            from_db_ports = app_listen_instance.listen_ports(from_db_pid_list)
            if not from_db_ports:
                print("Have no project listenports %s" % project_item)
                app_listen_instance.end_line(project_item)
                continue
            else:
                print("2.查询到的pid列表：%s" % from_db_pid_list)
                # 生成监听信息
                for port in from_db_ports:
                    # 导入监听表
                    # 监听信息需要提前合成
                    for ip in app_listen_instance.get_localhost_ip_list():
                        ipport = str(ip)+':'+str(port)
                        linfo = "('"+ipport+"','"+project_item+"')"
                        to_db_ipport_project.append(linfo)
                print("%s listen infomation ok" % project_item)
                # 生成连接池表
                collect_con_ipport_list = app_listen_instance.connectpools(from_db_ports, from_db_pid_list)
                # 生成连接池信息
                for con in collect_con_ipport_list:
                    cinfo = "('"+con+"','"+project_item+"')"
                    # print("cinfo is :%s" % cinfo)
                    to_db_conipport_project.append(cinfo)
                print("%s connect pool infomation ok" % project_item)
        # print("导入ip列表%s" % to_db_ipport_project)
        app_listen_instance.import2db(listentable, listen_ipport_column, projectcolumn, to_db_ipport_project)
        # print("导入connect列表%s" % to_db_conipport_project)
        app_listen_instance.import2db(connectpooltable,
                                      connectpool_ipport_column,
                                      projectcolumn,
                                      to_db_conipport_project
                                      )
        app_listen_instance.end_line(project_item)
    app_listen_instance.finally_close_connect()

if __name__ == "__main__":
    app_l_collect()