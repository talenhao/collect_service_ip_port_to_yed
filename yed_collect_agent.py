#!/bin/env python
# -*- coding:utf-8 -*-

# ******************************************************
# Author       : tianfei hao
# Create Time  : 2017-03-20
# Last modified: 2017-03-21
# Email        : talenhao@gmail.com
# Description  : collect listen ip port and connect socket.
# Version      : 2.0
# ******************************************************

"""
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
未解决：
    使用psutil模块代替ps,ss收集信息。
"""

from Application_operation import applicationOperation as AppOp
import subprocess
import shlex
import sys
# import os
import re
import netifaces
import ConfigParser
import psutil
import datetime
import time

version = "2017-03-21"


def help_check(func):
    def wrapper(*args, **kwargs):
        run_data_time = time.time()
        print("Current datetime is : %s" % datetime.datetime.fromtimestamp(run_data_time))
        if sys.version_info < (2, 7):
            # raise RuntimeError('At least Python 3.4 is required')
            print('友情提示：当前系统版本低于2.7，建议升级python版本。')
        if len(sys.argv) < 2:
            print('没有匹配规则配置文件')
            sys.exit()
        if sys.argv[1].startswith('-'):
            option = sys.argv[1][1:]
            # print(option)
            # fetch the first option without '-'.
            if option == '-version':
                print('Version %s' % version)
            elif option == '-help':
                print('''
                   This program prints collect information to mysql.
                   Please specified a re file to pattern.
                   Options:
                   --version : Prints the version number
                   --help    : Display this help
                   -c file   : Config file.
                ''')
            elif option == 'c' and sys.argv[2]:
                print('Config file is %s' % sys.argv[2])
                return func(*args, **kwargs)
            else:
                print('Unknown option.')
                sys.exit()
        else:
            print("No Config file.")
            sys.exit()
    return wrapper()


@help_check
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

    @staticmethod
    def config_file_parser(config_file):
        """
        处理进程匹配文件
        :param config_file: 
        :return: 
        """
        config_file = config_file
        config = ConfigParser.ConfigParser()
        config.read(config_file)
        pattern_list = "|".join(map(lambda x: x[1], config.items('patterns')))
        return pattern_list

    def project_list(self):
        """
        加载服务列表
        :return: project list
        """
        sql_cmd = "SELECT projectname from %s" % self.projecttable  # self.projecttable来自AppOp
        # print(sql_cmd)
        self.resultCursor.execute(sql_cmd)
        for self.row in self.resultCursor.fetchall():
            print("project name: %s" % self.row)
            self.projects_name_list.append(self.row[0])
        return self.projects_name_list

    def pid_create_time(self, project, pid):
        pid = pid
        project = project
        run_date_time = time.time()
        finded_pid = int(pid[0])
        pid_create_time = psutil.Process(pid=finded_pid).create_time()
        if pid_create_time > run_date_time:
            print("%s 的进程%s已经被其它程序使用，数据失效，丢弃..." % (project, finded_pid))
            return None
        else:
            print("%s 的进程%s数据有效，正在查找监听..." % (project, finded_pid))
            return finded_pid

    def collect_pid_list(self, project, pattern_string):
        """
        查找指定程序的PID
        :param project:
        :return:
        """
        self.pid_lists = []
        self.project = project
        self.pattern_s = pattern_string
        # print("Find out %s pid number." % self.project)
        # ps aux |grep -E '[D]catalina.home=/data/wire/tomcat'|awk '{print $2}'
        # 1.内容
        # 1命令
        ps_aux_cmd = 'ps aux'
        # 2执行
        ps_aux_result = subprocess.Popen(shlex.split(ps_aux_cmd), stdout=subprocess.PIPE)
        # 3结果
        ps_aux_result_text = ps_aux_result.communicate()[0]  # .decode('utf-8')
        # 2.pattern&compile
        # version1: ps_aux_pattern_string = 'Dcatalina.home=/[-\w]+/%s/tomcat' % self.project
        # version2: ps_aux_pattern_string = 'Dcatalina.home=/[-\w]+/%s/(?:tomcat|server|log)' \
        #                            '|\./bin/%s\ (?:-c\ conf/%s\.conf)?' \
        #                            '|java -D%s.*\.jar.*/conf/zoo.cfg.*'\
        #                            '|%s: [\w]+ process'\
        #                            '|%s: pool www' \
        #                            '|java -cp /etc/%s/conf' \
        #                            % (self.project, self.project, self.project, self.project, self.project,
        #                               self.project, self.project)
        # version3:
        ps_aux_pattern_string = self.pattern_s.format(projectname = self.project)
        ps_aux_compile = re.compile(ps_aux_pattern_string)
        # try:
        # 3.match object
        for ps_aux_result_line in ps_aux_result_text.splitlines():
            ps_aux_re_find = ps_aux_compile.findall(ps_aux_result_line)
            if ps_aux_re_find:
                filename = '/tmp/collect_service_ip_port_to_yed-ps-aux-%s-%s' % (self.project, datetime.datetime.now())
                file = open(filename, 'w')
                file.write(ps_aux_result_text)
                file.close()
                print("Pattern is %s" % ps_aux_pattern_string)
                print("Get： %s " % ps_aux_re_find)
                pid = int(ps_aux_result_line.split()[1])
                print('%s has a pid number %s ...' % (self.project, pid))
                self.pid_lists.append(pid)
        # except subprocess.CalledProcessError:
        if self.pid_lists:
            print("project %s pid：%s" % (self.project, self.pid_lists))
        else:
            print('%s is not in this host!' % self.project)
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
        # self.card_ip_list_all = self.card_ip_list.remove('127.0.0.1')
        print("Local collect IP: %s" % self.card_ip_list)
        return self.card_ip_list

    def listen_ports(self, project, pids):
        """
        接收列表[pids]
        :param pids:
        :return:
        """
        self.pidlist = pids
        project = project
        # pid collect time: if the collection time is less than the creation time, the process has been killed and
        # the PID number is attached to the new process, then will drop this PID number.
        run_date_time = time.time()
        if not self.pidlist:
            return None
        self.portlists = []
        # 1.内容
        # ss_cmd = "ss -lntp -4 |grep %s |awk -F: '{print $2}'|awk '{print $1}'" % ipid
        ss_cmd = 'ss -l -n -p -t'
        ss_cmd_result = subprocess.Popen(shlex.split(ss_cmd), stdout=subprocess.PIPE)
        ss_cmd_result_text = ss_cmd_result.communicate()[0]  # .decode('utf-8')
        # print("ss -l结果： %s" % ss_cmd_result_text)
        filename = '/tmp/collect_service_ip_port_to_yed-ss-lnpt-%s-%s' % (project, datetime.datetime.now())
        file = open(filename, 'w')
        file.write(sscmd_result_text)
        file.close()
        # 2.pattern&compile
        ss_cmd_pattern_pid = '|'.join(format(n) for n in self.pidlist)
        print("pattern is :%s" % ss_cmd_pattern_pid)
        ss_cmd_compile = re.compile(ss_cmd_pattern_pid)
        # 3.match object
        for ss_cmd_result_line in ss_cmd_result_text.splitlines():
            ss_cmd_re_findpid = ss_cmd_compile.findall(ss_cmd_result_line)
            if ss_cmd_re_findpid:
                finded_pid = int(sscmd_re_findpid[0])
                print("sscmd_re_findpid is %s " % finded_pid)
                pid_create_time = psutil.Process(pid=finded_pid).create_time()
                if pid_create_time > run_date_time:
                    print("%s 的进程%s已经被其它程序使用，数据失效，丢弃..." % (project, finded_pid))
                    continue
                else:
                    print("%s 的进程%s数据有效，正在查找监听..." % (project, finded_pid))
                    self.listenport = sscmd_result_line.split()[3].split(':')[-1].strip()
                    # print(self.listenport)
                    self.portlists.append(self.listenport)
        print("监听端口接收到的监听列表%s" % self.portlists)
        return self.portlists

    def connectpools(self, project, ports, pids):
        """
        :param ports:
        :param pids:
        :return: 连接池
        """
        ports = ports
        pids = pids
        project = project
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
        filename = '/tmp/collect_service_ip_port_to_yed-ps-aux-%s-%s' % (project, datetime.datetime.now())
        file = open(filename, 'w')
        file.write(ssntpcmd_result_text)
        file.close()
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
            # print(sql_cmd)
            self.resultCursor.execute(sql_cmd)
            self.DBcon.commit()
        else:
            print("%s is not have socket." % self.project)

    @staticmethod
    def start_line(self, info):
        info = info
        print(">" * 80 + "\n process project start : %s \n" % info)

    @staticmethod
    def end_line(self, info):
        info = info
        print("\n process project finish : %s \n" % info + "<" * 80)


def app_l_collect():
    app_listen_instance = AppListen()
    # 取出应用名称
    # 初始化实例
    print("开始收集...")
    # Get project list
    app_listen_con_db_project_list = app_listen_instance.project_list()
    pattern_string = app_listen_instance.config_file_parser(sys.argv[2])
    # some values
    listen_table = "listentable"
    listen_ipport_column = 'lipport'
    connectpooltable = "pooltable"
    connectpool_ipport_column = 'conipport'
    projectcolumn = 'projectname'
    local_ip_list = app_listen_instance.get_localhost_ip_list()
    #
    for project_item in app_listen_con_db_project_list:  # project name
        to_db_ipport_project = []
        to_db_conipport_project = []
        # rows, columns = os.popen('stty size', 'r').read().split()
        # print("=" * int(columns) + "\n 1.process project : %s \n" % project_item)
        # Split line
        app_listen_instance.start_line(project_item)
        # pid list
        from_db_pid_list = app_listen_instance.collect_pid_list(project_item, pattern_string)
        if not from_db_pid_list:
            # print("Have no project %s" % project_item)
            app_listen_instance.end_line(project_item)
            continue
        else:
            # port list
            from_db_ports = app_listen_instance.listen_ports(project_item, from_db_pid_list)
            if not from_db_ports:
                print("Have no project listenports %s" % project_item)
                app_listen_instance.end_line(project_item)
                continue
            else:
                # print("2.查询到的pid列表：%s" % from_db_pid_list)
                # 生成监听信息
                for port in from_db_ports:
                    # 导入监听表
                    # 监听信息需要提前合成
                    for ip in local_ip_list:
                        ipport = str(ip)+':'+str(port)
                        linfo = "('"+ipport+"','"+project_item+"')"
                        to_db_ipport_project.append(linfo)
                # print("%s listen infomation ok" % project_item)
                # 生成连接池表
                collect_con_ipport_list = app_listen_instance.connectpools(project_item, from_db_ports, from_db_pid_list)
                # 生成连接池信息
                for con in collect_con_ipport_list:
                    # ','.join(map(lambda x: "('" + x[0] + "'," + str(int(x[1])) + ')', listen_group_id_project_name))
                    cinfo = "('"+con+"','"+project_item+"')"
                    # print("cinfo is :%s" % cinfo)
                    to_db_conipport_project.append(cinfo)
                # print("%s connect pool infomation ok" % project_item)
        # print("导入ip列表%s" % to_db_ipport_project)
        app_listen_instance.import2db(listen_table, listen_ipport_column, projectcolumn, to_db_ipport_project)
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

    """
    RunDateTime = time.time()
    print("Current datetime is : %s" % datetime.datetime.fromtimestamp(RunDateTime))
    if sys.version_info < (2, 7):
        # raise RuntimeError('At least Python 3.4 is required')
        print('友情提示：当前系统版本低于2.7，建议升级python版本。')

    if len(sys.argv) < 2:
        print('没有匹配规则配置文件')
        sys.exit()

    if sys.argv[1].startswith('-'):
        option = sys.argv[1][1:]
        # print(option)
        # fetch the first option without '-'.
        if option == '-version':
            print('Version %s' % version)
        elif option == '-help':
            print('''
               This program prints collect information to mysql.
               Please specified a re file to pattern.
               Options:
               --version : Prints the version number
               --help    : Display this help
               -c file   : Config file.
            ''')
        elif option == 'c' and sys.argv[2]:
            print('Config file is %s' % sys.argv[2])
            app_l_collect()
        else:
            print('Unknown option.')
            sys.exit()
    else:
        print("No Config file.")
        sys.exit()
"""
