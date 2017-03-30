#!/bin/env python
# -*- coding:utf-8 -*-


"""
Collect socket information.
Copyright (C) 2017-2018 Talen Hao. All Rights Reserved.
"""

__author__ = "Talen Hao(天飞)<talenhao@gmail.com>"
__status__ = "develop"
__version__ = "3.1"
__create_date__ = "2017/02/20"
__last_date__ = "2017/03/29"


from Application_operation import applicationOperation as AppOp
import collect_common
import collect_log
import logging
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
import multiprocessing
import multiprocessing.dummy
# import threading
# from Queue import Queue
# from itertools import repeat

version = "2017-03-28"
LogPath = '/tmp/collect2yed.log.%s' % datetime.datetime.now().strftime('%Y-%m-%d,%H.%M.%S')
clogger = collect_log.GetLogger(LogPath, __name__, logging.DEBUG).get_l()


# 提示，帮助等装饰器。
def help_check(func):
    def wrapper(*args, **kwargs):
        run_data_time = time.time()
        clogger.info("Current datetime is : %s", datetime.datetime.fromtimestamp(run_data_time))
        if sys.version_info < (2, 7):
            # raise RuntimeError('At least Python 3.4 is required')
            clogger.warning('友情提示：当前系统版本低于2.7，建议升级python版本。')
            
        if len(sys.argv) < 2:
            clogger.error('没有匹配规则配置文件')
            sys.exit()
            
        if sys.argv[1].startswith('-'):
            option = sys.argv[1][1:]
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
                clogger.info("Config file is %s", sys.argv[2])
                return func(*args, **kwargs)
            else:
                clogger.error('Unknown option.')
                sys.exit()
        else:
            clogger.warning("No Config file.")
            sys.exit()
    return wrapper

def spend_time(func):
    def warpper(*args, **kwargs):
        start_time = datetime.datetime.now()
        clogger.info("Time start %s", start_time)
        func(*args, **kwargs)
        end_time = datetime.datetime.now()
        clogger.info("Time over %s,spend %s", end_time, end_time - start_time)
    return warpper

def logfile(cmd_id, project, cmd_context):
    filename = '/tmp/collect_service_ip_port_to_yed-%s-%s-%s' % (cmd_id, project, datetime.datetime.now())
    log_file = open(filename, 'w')
    log_file.write(cmd_context)
    log_file.close()


class AppListen(AppOp):
    """
    收集监听IP及port信息
    收集连接池信息
    """
    def __init__(self):
        AppOp.__init__(self)
        # self.projecttable = "application"
        # self.group_table = "appgroup"

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
        clogger.debug(pattern_list)
        return pattern_list

    def project_list(self):
        """
        加载服务列表
        :return: projects_name_list
        """
        projects_name_list = []
        sql_cmd = "SELECT projectname from %s" % self.projecttable  # self.projecttable来自AppOp
        clogger.debug(sql_cmd)
        self.resultCursor.execute(sql_cmd)
        for row in self.resultCursor.fetchall():
            clogger.debug("Fetch project name from database : %s", row)
            projects_name_list.append(row[0])
        clogger.info(projects_name_list)
        return projects_name_list

    @staticmethod
    def collect_pid_list(project, pattern_string):
        """
        查找指定程序的PID
        :param project
        :param pattern_string:
        :return:
        """
        pid_lists = []
        # ps aux |grep -E '[D]catalina.home=/data/wire/tomcat'|awk '{print $2}'
        # 1.内容
        ps_aux_cmd = 'ps aux'
        ps_aux_result = subprocess.Popen(shlex.split(ps_aux_cmd), stdout=subprocess.PIPE)
        ps_aux_result_text = ps_aux_result.communicate()[0]  # .decode('utf-8')
        # clogger.debug(ps_aux_result_text)
        # 2.pattern&compile
        ps_aux_pattern_string = pattern_string.format(projectname=project)
        clogger.debug(ps_aux_pattern_string)
        ps_aux_compile = re.compile(ps_aux_pattern_string)
        # 3.match object
        for ps_aux_result_line in ps_aux_result_text.splitlines():
            clogger.debug(ps_aux_result_line)
            ps_aux_re_find = ps_aux_compile.findall(ps_aux_result_line)
            clogger.debug(ps_aux_re_find)
            if ps_aux_re_find:
                logfile('ps_aux', project, ps_aux_result_text)
                clogger.info("Pattern is %s", ps_aux_pattern_string)
                clogger.info("Get： %s ", ps_aux_re_find)
                pid = int(ps_aux_result_line.split()[1])
                clogger.debug(pid)
                clogger.info('%s has a pid number %s ...', project, pid)
                pid_lists.append(pid)
        # except subprocess.CalledProcessError:
        # pid一般不会重复
        # pid_lists = collect_common.unique_list(pid_lists)
        if pid_lists:
            clogger.info("project %s pid：%s", project, pid_lists)
        else:
            time.sleep(1)
            clogger.info('%s is not in this host!', project)
        clogger.debug(pid_lists)
        return pid_lists

    @staticmethod
    def get_localhost_ip_list():
        """
        获取本机所有IP信息
        """
        clogger.info('Collect localhost IP addresses.')
        card_ip_list = []
        for interface_card in netifaces.interfaces():
            clogger.debug(interface_card)
            try:
                card_ip_address = netifaces.ifaddresses(interface_card)[netifaces.AF_INET][0]['addr']
                clogger.debug(card_ip_address)
            except KeyError:
                clogger.info("%s is not have ip", interface_card)
            else:
                clogger.info("%s is have ip %s", interface_card, card_ip_address)
                card_ip_list.append(card_ip_address)
        # 如果服务监听端口无重复可以打开
        # card_ip_list_all = card_ip_list.remove('127.0.0.1')
        clogger.info("Local collect IP: %s", card_ip_list)
        return card_ip_list

    @staticmethod
    def listen_ports(project, pid_list):
        """
        :param pid_list
        :param project:
        :return:
        """
        # pid collect time: if the collection time is less than the creation time, the process has been killed and
        # the PID number is attached to the new process, then will drop this PID number.
        run_date_time = time.time()
        if not pid_list:
            clogger.debug("%s is None, so return None", pid_list)
            return None
        port_list = []
        # 1.内容
        # ss_cmd = "ss -lntp -4 |grep %s |awk -F: '{print $2}'|awk '{print $1}'" % ipid
        ss_cmd = 'ss -l -n -p -t'
        ss_cmd_result = subprocess.Popen(shlex.split(ss_cmd), stdout=subprocess.PIPE)
        ss_cmd_result_text = ss_cmd_result.communicate()[0]  # .decode('utf-8')
        # clogger.debug(ss_cmd_result_text)
        logfile("ss_lnpt", project, ss_cmd_result_text)
        # 2.pattern&compile
        # 修复359会匹配23592造成数据错误问题
        ss_cmd_pattern_pid = '|'.join(",{0},".format(n) for n in pid_list)
        clogger.info("pattern is :%s", ss_cmd_pattern_pid)
        ss_cmd_compile = re.compile(ss_cmd_pattern_pid)
        # 3.match object
        for ss_cmd_result_line in ss_cmd_result_text.splitlines():
            clogger.debug(ss_cmd_result_line)
            ss_cmd_re_findpid = ss_cmd_compile.findall(ss_cmd_result_line)
            clogger.debug(ss_cmd_re_findpid)
            if ss_cmd_re_findpid:
                found_pid = int(ss_cmd_re_findpid[0].split(',')[1])
                clogger.info("ss_cmd_re_findpid is %s ", found_pid)
                pid_create_time = psutil.Process(pid=found_pid).create_time()
                clogger.debug(pid_create_time)
                if pid_create_time > run_date_time:
                    clogger.info("%s 的进程%s已经被其它程序使用，数据失效，丢弃...", project, found_pid)
                    continue
                else:
                    clogger.info("%s 的进程%s数据有效，正在查找监听...", project, found_pid)
                    listen_port = ss_cmd_result_line.split()[3].split(':')[-1].strip()
                    clogger.info("找到监听端口：%s", listen_port)
                    port_list.append(listen_port)
        # 监听端口去重
        clogger.debug("ununiq list %s", port_list)
        port_list = collect_common.unique_list(port_list)
        clogger.debug("uniq list %s", port_list)
        clogger.info("监听端口接收到的监听列表%s", port_list)
        return port_list
    
    @staticmethod
    def connect_pool(project, ports, pid_list):
        """
        :param ports:
        :param pid_list:
        :param project:
        :return: pool_list
        """
        run_date_time = time.time()
        pool_list = []
        clogger.info("处理连接池，接收参数端口：%s，进程号：%s", ports, pid_list)
        s_port_line = ["sport neq :%s" % n for n in ports]
        clogger.debug(s_port_line)
        s_port_join = ' and '.join(s_port_line)
        clogger.debug(s_port_join)
        # 1.内容
        # ss_cmd = ss -ntp -o state established \'( sport != :%s )\'|grep -E %s|\
        # awk \'{print $4}\'|awk -F \':\' \'{print $(NF-1)\":\" $NF}\'' % (self.port,self.pid)
        ss_ntp_cmd = 'ss -ntp -o state established \\( %s \\)' % s_port_join
        clogger.info("Begin to execute ss connection command: %s", ss_ntp_cmd)
        ss_ntp_cmd_result = subprocess.Popen(shlex.split(ss_ntp_cmd), stdout=subprocess.PIPE)
        ss_ntp_cmd_result_text = ss_ntp_cmd_result.communicate()[0]  # .decode('utf-8')
        # clogger.debug(ss_ntp_cmd_result_text)
        logfile("ss_ntp", project, ss_ntp_cmd_result_text)
        # 2.pattern&compile
        ss_ntp_cmd_pattern_pid = '|'.join(",{0},".format(n) for n in pid_list)
        clogger.debug(ss_ntp_cmd_pattern_pid)
        ss_ntp_cmd_compile = re.compile(ss_ntp_cmd_pattern_pid)
        # 3.match object
        for ss_ntp_cmd_result_line in ss_ntp_cmd_result_text.splitlines():
            ss_ntp_cmd_re_findpid = ss_ntp_cmd_compile.findall(ss_ntp_cmd_result_line)
            clogger.debug(ss_ntp_cmd_re_findpid)
            if ss_ntp_cmd_re_findpid:
                clogger.info("当前连接池匹配行：%s", ss_ntp_cmd_result_line)
                clogger.info("当前pid匹配结果：%s", ss_ntp_cmd_re_findpid)
                # 判断pid是否有效
                found_pid = int(ss_ntp_cmd_re_findpid[0].split(',')[1])
                clogger.info("检查连接池传入的PID. Import pid is %s", found_pid)
                pid_create_time = psutil.Process(pid=found_pid).create_time()
                clogger.debug(pid_create_time)
                if pid_create_time > run_date_time:
                    clogger.info("%s 的进程%s已经被其它程序使用，数据失效，丢弃...", project, found_pid)
                else:
                    clogger.info("%s 的进程%s数据有效，放入pattern列表...", project, found_pid)
                    clogger.info("找到有效PID：%s" % found_pid)
                    connect_ip_port_list = ss_ntp_cmd_result_line.split()[3].split(':')[-2:]
                    clogger.debug("过滤出的连接池IP：port %s", connect_ip_port_list)
                    ip_port_message = ':'.join(connect_ip_port_list)
                    clogger.debug(ip_port_message)
                    pool_list.append(ip_port_message)
            else:
                clogger.debug("project %s ss_ntp_cmd_re_findpid is none.", project)
        # 连接池列表去重
        clogger.debug("ununiq list %s", pool_list)
        pool_list = collect_common.unique_list(pool_list)
        clogger.debug("uniq list %s", pool_list)
        clogger.info("处理连接池，列表：%s", pool_list)
        return pool_list

    def import2db(self, table, ip_port_column, project_column, message, project_name):
        """
        :param table:
        :param ip_port_column:
        :param project_column:
        :param project_name:
        :param message:
        :return:
        """
        clogger.debug(message)
        if len(message) > 0:
            sql_cmd = "INSERT ignore INTO %s (%s,%s) VALUES %s" % (
                table,
                ip_port_column,
                project_column,
                ','.join(message)
            )
            clogger.debug(sql_cmd)
            self.resultCursor.execute(sql_cmd)
            self.DBcon.commit()
        else:
            clogger.debug("%s is not have socket.", project_name)
            pass

    @staticmethod
    def start_line(info):
        print("\n" + ">" * 50 + "process project start : %s" % info)

    @staticmethod
    def end_line(info):
        print("\n" + "<" * 50 + "process project finish : %s " % info)


def do_collect(project_name, instance, pattern_string, local_ip_list):
    # 导入数据库的两个列表
    clogger.debug("当前执行：%s, %s", project_name, pattern_string)
    clogger.info("当前执行：%s", project_name)
    to_db_ip_port_project = []
    to_db_con_ip_port_project = []
    # 初始变量
    listen_table = "listentable"
    listen_ipport_column = 'lipport'
    connectpooltable = "pooltable"
    connectpool_ipport_column = 'conipport'
    project_column = 'projectname'
    # rows, columns = os.popen('stty size', 'r').read().split()
    # clogger.info("=" * int(columns) + "\n 1.process project : %s \n" % project_name)
    # Split line
    instance.start_line(project_name)
    # pid list
    from_db_pid_list = instance.collect_pid_list(project_name, pattern_string)
    clogger.debug(from_db_pid_list)
    if not from_db_pid_list:
        clogger.debug("Have no project %s", project_name)
        instance.end_line(project_name)
    else:
        # port list
        from_db_ports = instance.listen_ports(project_name, from_db_pid_list)
        clogger.debug(from_db_ports)
        if not from_db_ports:
            clogger.info("Have no project listen ports %s", project_name)
            instance.end_line(project_name)
        else:
            # 生成监听信息
            for port in from_db_ports:
                clogger.debug(port)
                # 导入监听表
                # 监听信息需要提前合成
                for ip in local_ip_list:
                    ip_port = str(ip) + ':' + str(port)
                    clogger.debug(ip_port)
                    listen_info = "('" + ip_port + "','" + project_name + "')"
                    clogger.debug(listen_info)
                    to_db_ip_port_project.append(listen_info)
            clogger.debug("%s listen information ok", project_name)
            # 生成连接池表
            collect_con_ip_port_list = instance.connect_pool(project_name, from_db_ports, from_db_pid_list)
            clogger.debug(collect_con_ip_port_list)
            # 生成连接池信息
            for con in collect_con_ip_port_list:
                # ','.join(map(lambda x: "('" + x[0] + "'," + str(int(x[1])) + ')', listen_group_id_project_name))
                clogger.debug(con)
                con_info = "('" + con + "','" + project_name + "')"
                clogger.debug(con_info)
                to_db_con_ip_port_project.append(con_info)
            instance.end_line(project_name)
    instance.import2db(listen_table,
                       listen_ipport_column,
                       project_column,
                       to_db_ip_port_project,
                       project_name)
    instance.import2db(connectpooltable,
                       connectpool_ipport_column,
                       project_column,
                       to_db_con_ip_port_project,
                       project_name)

# 老式方法，放弃
# def _collect_worker():
#     thread_list = []
#     app_listen_instance = AppListen()
#     app_listen_con_db_project_list = app_listen_instance.project_list()
#     loop = len(app_listen_con_db_project_list)
#     for project_item in app_listen_con_db_project_list:  # project name
#         thread_instance = threading.Thread(target=do_collect, args=(project_item,))
#         thread_list.append(thread_instance)
#     # 启动线程
#     for instance_item in range(loop):
#         thread_list[instance_item].start()
#     # 等待所有线程结束
#     for instance_item in range(loop):
#         thread_list[instance_item].join()
#     clogger.info("All collect thread finished.")
# 
  
# class CollectWorker(threading.Thread):
#     def __init__(self, queue):
#         threading.Thread.__init__(self)
#         self.queue = queue
# 
#     def run(self):
#         while True:
#             # 从队列中获取项目名
#             project_item = self.queue.get()
#             do_collect(project_item)
#             self.queue.task_done()
  
  
# def main():
#     app_listen_instance = AppListen()
#     app_listen_con_db_project_list = app_listen_instance.project_list()
#     for worker in range(cpu_count()/6):
#         worker = CollectWorker(Queue)
#         worker.setDaemon(True)
#         worker.start()
#     for project_item in app_listen_con_db_project_list:
#         Queue.put(project_item)
#     Queue.join()
#     clogger.info("All worker finished.")


@spend_time
@help_check
def main():

    thread_num = multiprocessing.cpu_count()/6
    # thread_num = multiprocessing.cpu_count()
    clogger.info("There have %s Threads", thread_num)
    app_listen_instance = AppListen()
    pattern_string = app_listen_instance.config_file_parser(sys.argv[2])
    clogger.debug(pattern_string)
    local_ip_list = app_listen_instance.get_localhost_ip_list()
    clogger.debug(local_ip_list)
    app_listen_con_db_project_list = app_listen_instance.project_list()
    clogger.debug(app_listen_con_db_project_list)
    # Make the Pool of workers
    pool = multiprocessing.dummy.Pool(processes=thread_num)
    # Process collect project in their own threads
    for project_item in app_listen_con_db_project_list:
        clogger.debug(project_item)
        pool.apply_async(do_collect, args=(project_item, app_listen_instance, pattern_string, local_ip_list))
    # close the pool and wait for the work to finish
    pool.close()
    pool.join()


if __name__ == "__main__":
    main()
