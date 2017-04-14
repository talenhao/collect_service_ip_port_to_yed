#!/bin/env python
# -*- coding:utf-8 -*-


"""
Collect socket information.
Copyright (C) 2017-2018 Talen Hao. All Rights Reserved.
"""


from Application_operation import ApplicationOperation as AppOp
import collect_common
import collect_log
import logging
import subprocess
import shlex
import sys
import getopt
# import os
import re
import netifaces
import ConfigParser
import psutil
import datetime
import time
import multiprocessing
import multiprocessing.dummy
import uuid
# import threading
# from Queue import Queue
# from itertools import repeat
__author__ = "Talen Hao(天飞)<talenhao@gmail.com>"
__status__ = "develop"
__version__ = "2017.04.12"
__create_date__ = "2017/02/20"
__last_date__ = "2017/03/29"
LogPath = '/tmp/collect2yed.log.%s' % datetime.datetime.now().strftime('%Y-%m-%d,%H.%M.%S')
c_logger = collect_log.GetLogger(LogPath, __name__, logging.DEBUG).get_l()
all_args = sys.argv[1:]
ss_bin = '/var/local/iproute2-4.10.0/misc/ss'
usage = '''
用法：
%s [--命令选项] [参数]

命令选项：
    --help, -h              帮助。
    --version, -V           输出版本号。
    --config, -c <文件>      使用指定而非默认的配置文件。
    --project, -p <字符串>   用户自定义的项目收集。
''' % sys.argv[0]

# 初始变量
# global listen_table
listen_table = "listentable"
# global listen_ipport_column
listen_ipport_column = 'lipport'
# global connectpooltable
connectpooltable = "pooltable"
# global connectpool_ipport_column
connectpool_ipport_column = 'conipport'
# global project_column
project_column = 'projectname'
# global server_uuid_column
server_uuid_column = 'server_uuid'
# global server_uuid
# server_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, __author__))


# 使用dmidecode命令生成（不足：需要使用root权限）。后来发现uuid模块的getnode生成的uuid竟然跟dmidecode是一样的。
# 参考http://stackoverflow.com/questions/2461141/get-a-unique-computer-id-in-python-on-windows-and-linux
def dmi_get_system_uuid():
    dmi_cmd = 'dmidecode -s system-uuid'
    dmi_result = subprocess.Popen(shlex.split(dmi_cmd), stdout=subprocess.PIPE)
    return dmi_result.communicate()[0]  # .decode('utf-8')

server_uuid = str(uuid.UUID(int=uuid.getnode()))
c_logger.info("server_uuid is: %s", server_uuid)


# def logfile(cmd_id, project, cmd_context):
#     filename = '/tmp/collect_service_ip_port_to_yed-%s-%s-%s' % (cmd_id, project, datetime.datetime.now())
#     log_file = open(filename, 'w')
#     log_file.write(cmd_context)
#     log_file.close()


# 提示，帮助等装饰器。
def help_check(func):
    def _wrapper(*args, **kwargs):
        # run_data_time = time.time()
        # c_logger.info("Current datetime is : %s", datetime.datetime.fromtimestamp(run_data_time))
        if sys.version_info < (2, 7):
            # raise RuntimeError('At least Python 3.4 is required')
            c_logger.warning('友情提示：当前系统版本低于2.7，建议升级python版本。')
        c_logger.info("当前脚本版本信息：%s", __version__)
        return func(*args, **kwargs)
    return _wrapper


def spend_time(func):
    def warpper(*args, **kwargs):
        start_time = datetime.datetime.now()
        c_logger.debug("Time start %s", start_time)
        func(*args, **kwargs)
        end_time = datetime.datetime.now()
        c_logger.debug("Time over %s,spend %s", end_time, end_time - start_time)
    return warpper


def get_options():
    if all_args:
        c_logger.debug("命令行参数是 %s", str(all_args))
    else:
        c_logger.error(usage)
        sys.exit()
    config_file = ''
    only_run_project = ''
    try:
        opts, args = getopt.getopt(all_args, "hc:p:V", ["help", "config=", "project=", "version"])
    except getopt.GetoptError:
        c_logger.error(usage)
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', "--help"):
            c_logger.info(usage)
            sys.exit()
        elif opt in ("-V", "--version"):
            print('Current version is %0.2f' % float(__version__))
            c_logger.debug('Version %s', __version__)
            sys.exit()
        elif opt in ("-c", "--config"):
            c_logger.info("Config file is %s", arg)
            config_file = arg
        elif opt in ("-p", "--project"):
            c_logger.info("收集的项目是 %s", arg)
            only_run_project = arg
    c_logger.debug("配置文件是%s， 单独运行 %s", config_file, only_run_project)
    return config_file, only_run_project


class AppListen(AppOp):
    """
    收集监听IP及port信息
    收集连接池信息
    """
    def __init__(self):
        AppOp.__init__(self)

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
        c_logger.debug(pattern_list)
        return pattern_list

    def project_list(self):
        """
        加载服务列表
        :return: projects_name_list
        """
        projects_name_list = []
        sql_cmd = "SELECT projectname from %s" % self.project_table  # self.projecttable来自AppOp
        c_logger.debug(sql_cmd)
        self.cursor.execute(sql_cmd)
        for row in self.cursor.fetchall():
            c_logger.debug("Fetch project name from database : %s", row)
            projects_name_list.append(row[0])
        c_logger.debug(projects_name_list)
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
        # c_logger.debug(ps_aux_result_text)
        # 2.pattern&compile
        ps_aux_pattern_string = pattern_string.format(projectname=project)
        c_logger.debug("%s> %s", project, ps_aux_pattern_string)
        ps_aux_compile = re.compile(ps_aux_pattern_string)
        # 3.match object
        for ps_aux_result_line in ps_aux_result_text.splitlines():
            # c_logger.debug(ps_aux_result_line)
            ps_aux_re_find = ps_aux_compile.findall(ps_aux_result_line)
            # c_logger.debug(ps_aux_re_find)
            if ps_aux_re_find:
                # logfile('ps_aux', project, ps_aux_result_text)
                c_logger.debug("%s> Pattern is %s", project, ps_aux_pattern_string)
                c_logger.info("%s> _____________________________Get： %s ", project, ps_aux_re_find)
                pid = int(ps_aux_result_line.split()[1])
                c_logger.debug("%s> %s", project, pid)
                c_logger.debug('%s> has a pid number %s ...', project, pid)
                pid_lists.append(pid)
        # except subprocess.CalledProcessError:
        # pid一般不会重复
        # pid_lists = collect_common.unique_list(pid_lists)
        if pid_lists:
            c_logger.info("%s> pid：%s", project, pid_lists)
        else:
            time.sleep(1)
            c_logger.debug('%s> is not in this host!', project)
        c_logger.debug("%s> %s", project, pid_lists)
        return pid_lists

    @staticmethod
    def get_localhost_ip_list():
        """
        获取本机所有IP信息
        """
        c_logger.debug('Collect localhost IP addresses.')
        card_ip_list = []
        for interface_card in netifaces.interfaces():
            c_logger.debug(interface_card)
            try:
                card_ip_address = netifaces.ifaddresses(interface_card)[netifaces.AF_INET][0]['addr']
                c_logger.debug(card_ip_address)
            except KeyError:
                c_logger.debug("%s is not have ip", interface_card)
            else:
                c_logger.debug("%s is have ip %s", interface_card, card_ip_address)
                card_ip_list.append(card_ip_address)
        # 如果服务监听端口无重复可以打开
        # card_ip_list_all = card_ip_list.remove('127.0.0.1')
        c_logger.info("Local collect IP: %s", card_ip_list)
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
            c_logger.debug("%s> %s is None, so return None", project, pid_list)
            return None
        port_list = []
        # 1.内容
        # ss_cmd = "ss -lntp -4 |grep %s |awk -F: '{print $2}'|awk '{print $1}'" % ipid
        ss_cmd = '%s -l -n -p -t' % ss_bin
        c_logger.debug("%s> %s", project, ss_cmd)
        ss_cmd_result = subprocess.Popen(shlex.split(ss_cmd), stdout=subprocess.PIPE)
        ss_cmd_result_text = ss_cmd_result.communicate()[0]  # .decode('utf-8')
        # c_logger.debug(ss_cmd_result_text)
        # logfile("ss_lnpt", project, ss_cmd_result_text)
        # 2.pattern&compile
        # 修复359会匹配23592造成数据错误问题
        ss_cmd_pattern_pid = '|'.join(",pid={0},".format(n) for n in pid_list)
        c_logger.debug("%s> pattern is: %s", project, ss_cmd_pattern_pid)
        ss_cmd_compile = re.compile(ss_cmd_pattern_pid)
        c_logger.debug("%s> ss_cmd_compile: %s", project, ss_cmd_compile)
        # 3.match object
        for ss_cmd_result_line in ss_cmd_result_text.splitlines():
            # c_logger.debug("%s> %s", project, ss_cmd_result_line)
            ss_cmd_re_findpid = ss_cmd_compile.findall(ss_cmd_result_line)
            # c_logger.debug("%s> %s", project, ss_cmd_re_findpid)
            if ss_cmd_re_findpid:
                found_pid = int(ss_cmd_re_findpid[0].split(',')[1].split('=')[1])
                c_logger.debug("%s> ss_cmd_re_findpid is %s ", project, found_pid)
                pid_create_time = psutil.Process(pid=found_pid).create_time()
                c_logger.debug("%s> pid_create_time is %s.", project, str(pid_create_time))
                if pid_create_time > run_date_time:
                    c_logger.info("%s> 的进程%s已经被其它程序使用，数据失效，丢弃...", project, found_pid)
                    continue
                else:
                    c_logger.debug("%s> 的进程%s数据有效，正在查找监听...", project, found_pid)
                    listen_port = ss_cmd_result_line.split()[3].split(':')[-1].strip()
                    c_logger.debug("%s> 找到监听端口：%s", project, listen_port)
                    port_list.append(listen_port)
        # 监听端口去重
        c_logger.debug("%s> un_unique list %s", project, port_list)
        port_list = collect_common.unique_list(port_list)
        c_logger.debug("%s> unique list %s", project, port_list)
        c_logger.info("%s> 监听端口接收到的监听列表%s", project, port_list)
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
        c_logger.info("%s> 处理连接池，接收参数端口：%s，进程号：%s", project, ports, pid_list)
        s_port_line = ["sport neq :%s" % n for n in ports]
        c_logger.debug("%s> %s", project, s_port_line)
        s_port_join = ' and '.join(s_port_line)
        c_logger.debug("%s> %s", project, s_port_join)
        # 1.内容
        # ss_cmd = ss -ntp -o state established \'( sport != :%s )\'|grep -E %s|\
        # awk \'{print $4}\'|awk -F \':\' \'{print $(NF-1)\":\" $NF}\'' % (self.port,self.pid)
        ss_ntp_cmd = '%s -ntp -o state established \\( %s \\)' % (ss_bin, s_port_join)
        c_logger.info("%s> Begin to execute ss connection command: %s", project, ss_ntp_cmd)
        ss_ntp_cmd_result = subprocess.Popen(shlex.split(ss_ntp_cmd), stdout=subprocess.PIPE)
        ss_ntp_cmd_result_text = ss_ntp_cmd_result.communicate()[0]  # .decode('utf-8')
        # c_logger.debug(ss_ntp_cmd_result_text)
        # logfile("ss_ntp", project, ss_ntp_cmd_result_text)
        # 2.pattern&compile
        # 2017版本的ss命令已经使用pid=num的方式，所以要修改成新格式
        # old2009: LISTEN     0      1024   *:14027 *:* users:(("nutcracker",47573,44))
        # new2017: LISTEN     0      1024   *:14027 *:* users:(("nutcracker",pid=47573,fd=44))
        # ss_ntp_cmd_pattern_pid = '|'.join(",{0},".format(n) for n in pid_list)
        ss_ntp_cmd_pattern_pid = '|'.join(",pid={0},".format(n) for n in pid_list)
        c_logger.debug("%s> %s", project, ss_ntp_cmd_pattern_pid)
        ss_ntp_cmd_compile = re.compile(ss_ntp_cmd_pattern_pid)
        # 3.match object
        for ss_ntp_cmd_result_line in ss_ntp_cmd_result_text.splitlines():
            ss_ntp_cmd_re_findpid = ss_ntp_cmd_compile.findall(ss_ntp_cmd_result_line)
            # c_logger.debug(ss_ntp_cmd_re_findpid)
            if ss_ntp_cmd_re_findpid:
                c_logger.debug("%s> ss_ntp_cmd_re_findpid 连接池匹配行：%s", project, ss_ntp_cmd_result_line)
                c_logger.debug("%s> ss_ntp_cmd_re_findpid 当前pid匹配结果：%s", project, ss_ntp_cmd_re_findpid)
                # 判断pid是否有效
                found_pid = int(ss_ntp_cmd_re_findpid[0].split(',')[1].split('=')[1])
                c_logger.debug("%s> 检查连接池传入的PID. Import pid is %s", project, found_pid)
                pid_create_time = psutil.Process(pid=found_pid).create_time()
                c_logger.debug("%s> %s", project, pid_create_time)
                if pid_create_time > run_date_time:
                    c_logger.info("%s> 的进程%s已经被其它程序使用，数据失效，丢弃...", project, found_pid)
                else:
                    c_logger.debug("%s> 的进程%s数据有效，放入pattern列表...", project, found_pid)
                    # 新版本的ss格式有变化
                    connect_ip_port_list = ss_ntp_cmd_result_line.split()[3].split(':')[-2:]
                    c_logger.debug("%s> 过滤出的连接池IP：port %s", project, connect_ip_port_list)
                    ip_port_message = ':'.join(connect_ip_port_list)
                    c_logger.debug("%s> %s", project, ip_port_message)
                    pool_list.append(ip_port_message)
            else:
                c_logger.debug("%s> ss_ntp_cmd_re_findpid is none.", project)
        # 连接池列表去重
        c_logger.debug("%s> un_unique list %s", project, pool_list)
        pool_list = collect_common.unique_list(pool_list)
        c_logger.debug("%s> unique list %s", project, pool_list)
        c_logger.info("%s> 处理连接池，列表：%s", project, pool_list)
        return pool_list

    def import2db(self, table, ip_port_column, project_column, server_uuid_column, message, project_name):
        """
        :param table:
        :param ip_port_column:
        :param project_column:
        :param project_name:
        :param server_uuid_column:
        :param message:
        :return:
        """
        c_logger.debug("%s> %s", project_name, message)
        if len(message) > 0:
            sql_cmd = "INSERT ignore INTO %s (%s,%s,%s) VALUES %s" % (
                table,
                ip_port_column,
                project_column,
                server_uuid_column,
                ','.join(message)
            )
            c_logger.debug("%s> 导入数据库操作命令： %s", project_name, sql_cmd)
            r_r_c = self.cursor.execute(sql_cmd)
            c_logger.info("%s> 插入数据库执行结果: %s", project_name, r_r_c)
            # c_logger.info("%s> 插入数据库执行结果数量: %s", project_name, r_r_c.rowcount)
            # self.DBcon.commit()
        else:
            c_logger.debug("%s> is not have socket.", project_name)
            pass

    def reset_local_db_info(self, table_name, column_name):
        """
        在每台服务器执行全收集的时候，先清除旧的数据库信息;
        """
        c_logger.debug("重置表%s的字段%s服务器的信息。", table_name, column_name)
        # sql_like_string = "%s LIKE '{0}:%s'" % (column_name, str('%'))
        sql_like_string = "%s = '{0}'" % column_name
        c_logger.debug("sql_like_string: %s", sql_like_string)
        # if '127.0.0.1' in ip_list:
        #     ip_list.remove('127.0.0.1')
        # c_logger.debug(ip_list)
        # sql_like_pattern = ' or '.join(sql_like_string.format(ip) for ip in ip_list.remove('127.0.0.1'))
        # sql_like_pattern = ' or '.join(sql_like_string.format(ip) for ip in ip_list)
        sql_like_pattern = sql_like_string.format(server_uuid)
        # c_logger.debug("sql_like_pattern: ", sql_like_pattern)
        # print("sql_like_string is : %r " % sql_like_string)
        c_logger.debug("sql_like_string is : %r ", sql_like_string)
        sql_cmd = "DELETE FROM %s WHERE %s" % (table_name, sql_like_pattern)
        c_logger.debug("清除数据库操作： %s", sql_cmd)
        c_logger.debug("清除数据库执行结果%s", self.cursor.execute(sql_cmd))
        # self.DBcon.commit()

    @staticmethod
    def start_line(info):
        c_logger.debug("\n" + ">" * 50 + "process project start : %s", info)

    @staticmethod
    def end_line(info):
        c_logger.debug("\n" + "<" * 50 + "process project finish : %s ", info)


def do_collect(project_name, instance, pattern_string, local_ip_list):
    # 导入数据库的两个列表
    c_logger.debug("当前执行：%s> , %s", project_name, pattern_string)
    to_db_ip_port_project = []
    to_db_con_ip_port_project = []
    # 使用几个global变量
    # rows, columns = os.popen('stty size', 'r').read().split()
    # c_logger.info("=" * int(columns) + "\n 1.process project : %s \n" % project_name)
    # Split line
    instance.start_line(project_name)
    # pid list
    from_db_pid_list = instance.collect_pid_list(project_name, pattern_string)
    c_logger.debug("%s> %s", project_name, from_db_pid_list)
    if not from_db_pid_list:
        c_logger.debug("%s> Have no project %s", project_name, project_name)
        instance.end_line(project_name)
    else:
        # port list
        from_db_ports = instance.listen_ports(project_name, from_db_pid_list)
        c_logger.debug("%s> %s", project_name, from_db_ports)
        if not from_db_ports:
            c_logger.info("%s> Have no project listen ports %s", project_name, project_name)
            instance.end_line(project_name)
        else:
            # 生成监听信息
            for port in from_db_ports:
                c_logger.debug("%s> %s", project_name, port)
                # 导入监听表
                # 监听信息需要提前合成
                for ip in local_ip_list:
                    ip_port = str(ip) + ':' + str(port)
                    c_logger.debug("%s> %s", project_name, ip_port)
                    listen_info = "('" + ip_port + "','" + project_name + "','" + server_uuid + "')"
                    c_logger.debug("%s> %s", project_name, listen_info)
                    to_db_ip_port_project.append(listen_info)
            c_logger.debug("%s> listen information ok", project_name)
            instance.import2db(listen_table,
                               listen_ipport_column,
                               project_column,
                               server_uuid_column,
                               to_db_ip_port_project,
                               project_name)
            # 生成连接池表
            collect_con_ip_port_list = instance.connect_pool(project_name, from_db_ports, from_db_pid_list)
            c_logger.debug("%s> %s", project_name, collect_con_ip_port_list)
            # 生成连接池信息
            for con in collect_con_ip_port_list:
                # ','.join(map(lambda x: "('" + x[0] + "'," + str(int(x[1])) + ')', listen_group_id_project_name))
                c_logger.debug("%s> %s", project_name, con)
                con_info = "('" + con + "','" + project_name + "','" + server_uuid + "')"
                c_logger.debug("%s> %s", project_name, con_info)
                to_db_con_ip_port_project.append(con_info)
            instance.import2db(connectpooltable,
                               connectpool_ipport_column,
                               project_column,
                               server_uuid_column,
                               to_db_con_ip_port_project,
                               project_name)
            instance.end_line(project_name)

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
#     c_logger.info("All collect thread finished.")
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
#     c_logger.info("All worker finished.")


@spend_time
@help_check
def main():
    """
    解析命令行参数
    :param config_file, single_project: 
    :return: 
    """
    config_file, project = get_options()
    c_logger.debug("main: config_file is %s.", config_file)
    c_logger.debug("main: project is %s.", project)
    if config_file:
        thread_num = 1
        # thread_num = multiprocessing.cpu_count()/6
        c_logger.info("There have %s Threads", thread_num)
        app_listen_instance = AppListen()
    else:
        c_logger.info(usage)
        exit()
    c_logger.debug("获取本机的ip信息")
    local_ip_list = app_listen_instance.get_localhost_ip_list()
    c_logger.debug(local_ip_list)
    c_logger.debug("如果指定了收集项目，不执行清除数据库个数据操作。")
    if project:
        app_listen_con_db_project_list = [project]
    else:
        app_listen_con_db_project_list = app_listen_instance.project_list()
        c_logger.debug("清除当前执行主机的旧数据")
        # for t, c in {listen_table: listen_ipport_column, connectpooltable: connectpool_ipport_column}.items():
            # print(type(t),type(c))
        #     c_logger.debug("%r, %r", t, c)
        for table_name in [listen_table, connectpooltable]:
            app_listen_instance.reset_local_db_info(table_name, server_uuid_column)
    c_logger.debug("app_listen_con_db_project_list ___ %s", app_listen_con_db_project_list)
    pattern_string = app_listen_instance.config_file_parser(config_file)
    c_logger.debug(pattern_string)

    # Make the Pool of workers
    pool = multiprocessing.dummy.Pool(processes=thread_num)
    # Process collect project in their own threads
    for project_item in app_listen_con_db_project_list:
        c_logger.debug(project_item)
        pool.apply_async(do_collect, args=(project_item, app_listen_instance, pattern_string, local_ip_list))
    # close the pool and wait for the work to finish
    pool.close()
    pool.join()
    app_listen_instance.connect.commit()
    app_listen_instance.finally_close_all()

if __name__ == "__main__":
    main()
