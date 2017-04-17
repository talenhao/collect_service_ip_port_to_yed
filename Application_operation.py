#!/bin/env python
# -*- coding:utf-8 -*-
# ******************************************************
# Author       : tianfei hao
# Create Time  : 2017-02-25
# Last modified: 2017-04-16
# Email        : talenhao@gmail.com
# Description  : collect listen ip port and connect socket.
# ******************************************************
# 数据库操作
"""
2017-03-15
    修复添加重复application报错_mysql_exceptions.IntegrityError:
"""

import MySQLdb
import datetime
import sys
import logging
import collect_log


LogPath = '/tmp/%s.log.%s' % (sys.argv[0], datetime.datetime.now().strftime('%Y-%m-%d,%H.%M'))
c_logger = collect_log.GetLogger(LogPath, __name__, logging.DEBUG).get_l()


class DbInitConnect(object):
    """
    数据库初始化及连接，游标
    """
    # 初始化基本变量
    def __init__(self):
        self.host = '192.168.1.138'
        self.port = 3306
        self.password = 'yed'
        self.username = 'yed'
        self.db = 'yed_collect'

    # 连接数据库
    def db_connect(self):
        self.connect = MySQLdb.connect(host=self.host,
                                     port=self.port,
                                     user=self.username,
                                     passwd=self.password,
                                     db=self.db)
        # 返回指针
        return self.connect

    # 游标
    def db_cursor(self):
        self.cursor = self.db_connect().cursor()
        return self.cursor

    def finally_close_all(self):
        """
        关闭游标，关闭连接。
        :return: 
        """
        self.cursor.close()
        self.connect.close()

    def show_databases(self):
        cursor = self.db_cursor()
        sql_cmd = 'show create database yed_collect'
        try:
            cursor.execute(sql_cmd)
        except:
            c_logger.info('数据库连接有问题。')
        finally:
            for row in cursor.fetchall():
                c_logger.info(row)


class GroupOperation(DbInitConnect):
    def __init__(self):
        # 初始父类的生成器
        # super(DbInitConnect, self).__init__()
        DbInitConnect.__init__(self)
        DbInitConnect.db_cursor(self)
        self.group_table = "appgroup"

    def show_group(self):
        sql_cmd= 'SELECT groupname,parent_group from %s' % self.group_table
        self.cursor.execute(sql_cmd)
        for row in self.cursor.fetchall():
            print(row)
            
    def add_group(self, group_name, parent_group_name=''):
        sql_cmd = 'INSERT IGNORE INTO %s (groupname, parent_group) VALUES ("%s", "%s")' % (
            self.group_table,
            group_name,
            parent_group_name)
        c_logger.info(sql_cmd)
        self.cursor.execute(sql_cmd)
        self.connect.commit()
        
    def del_group(self, group_name):
        sql_cmd = 'DELETE FROM %s where groupname="%s";' % (
            self.group_table,
            group_name)
        c_logger.info(sql_cmd)
        try:
            self.cursor.execute(sql_cmd)
        except:
            c_logger.info("删除失败。")

    def modify_group(self, old_name, new_name):
        sql_cmd = 'UPDATE %s SET groupname = "%s" where groupname = "%s";' % (
            self.group_table,
            old_name,
            new_name)
        c_logger.info(sql_cmd)
        self.cursor.execute(sql_cmd)


class ApplicationOperation(GroupOperation):
    def __init__(self):
        # 初始父类的生成器
        # super(DbInitConnect, self).__init__()
        GroupOperation.__init__(self)
        self.project_table = "application"

    def show_application(self):
        sql_cmd = 'SELECT projectname, groupname from %s a, %s b where a.groupid = b.group_id' % (
            self.group_table,
            self.project_table)
        self.cursor.execute(sql_cmd)
        for row in self.cursor.fetchall():
            print(row)

    def add_application(self, app_name, group_name='in'):
        sql_cmd='SELECT groupid from %s where groupname = "%s"' % (
            self.group_table,
            group_name)
        c_logger.info(sql_cmd)
        self.cursor.execute(sql_cmd)
        group_id = self.cursor.fetchone()[0]
        c_logger.info('group id is: %r', str(group_id))
        sql_cmd = 'INSERT IGNORE INTO %s (projectname, group_id) VALUES ("%s", %s)' % (
            self.project_table,
            app_name,
            group_id)
        c_logger.info(sql_cmd)
        try:
            self.cursor.execute(sql_cmd)
        # except _mysql_exceptions.IntegrityError as e:
        except:
                # Another instance already created in this column
                print("Duplicate!")

    def del_application(self, app_name):
        sql_cmd = 'DELETE FROM %s where projectname = "%s";' % (self.project_table, app_name)
        c_logger.info(sql_cmd)
        self.cursor.execute(sql_cmd)

    def modify_application(self, old_app, new_app):
        sql_cmd = 'UPDATE %s SET projectname = "%s" where projectname="%s";' %(self.project_table, new_app, old_app)
        c_logger.info(sql_cmd)
        self.cursor.execute(sql_cmd)


class Tui(object):
    def __init__(self):
        self.item_list = ['group', 'project']
        self.operation_list = ["show", 'add', 'del', 'modify']

    @staticmethod
    def header_line(item):
        start_header = '>' * 40 + "In " + item + " choice: " + '<' * 40
        print(start_header)

    @staticmethod
    def end_line():
        end_header = '=' * 40 + 'End' + '=' * 40
        print(end_header)
    
    @staticmethod
    def list_item(list_name):
        print(zip(range(len(list_name)), list_name))
        

if __name__ == "__main__":
    Tui_menu = Tui()
    group_item = GroupOperation()
    app_item = ApplicationOperation()
    flag = True
    Tui_menu.header_line('start')
    while flag:
        Tui_menu.list_item(Tui_menu.item_list)
        try:
            choice_item_input = raw_input('请输入项目编号：\n')
            choice_item = int(choice_item_input)
        except ValueError:
            if str(choice_item_input) in ['q', 'quit']:
                break
            else:
                print('Input a Num!')
                continue
        if int(choice_item) not in range(len(Tui_menu.item_list)):
            print(range(len(Tui_menu.item_list)))
            print('Error num')
            continue
        Tui_menu.list_item(Tui_menu.operation_list)
        try:
            choice_item_op_input = int(raw_input('请输入项目编号：\n'))
            Tui_menu.header_line('RESULT')
            choice_item_op = int(choice_item_op_input)
        except ValueError:
            if str(choice_item_op) in ["q", "quit"]:
                break
            else:
                print('Input a Num!')
                continue
        if int(choice_item_op) not in range(len(Tui_menu.operation_list)):
            print(range(len(Tui_menu.operation_list)))
            print('Error num')
            continue
        c_logger.debug('process')
        if choice_item == 0 and choice_item_op == 0:
            group_item.show_group()
            Tui_menu.end_line()
        elif choice_item == 0 and choice_item_op == 1:
            group_input = raw_input("请输入group名称：\n")
            parent_group_input = raw_input("请输入父group名称，留空不添加父组：\n")
            group_item.add_group(group_input, parent_group_input)
            Tui_menu.end_line()
        elif choice_item == 0 and choice_item_op == 2:
            group_item.show_group()
            group_input = raw_input("请输入要删除的项目名：\n").strip()
            group_item.del_group(group_input)
            Tui_menu.end_line()
        elif choice_item == 0 and choice_item_op == 3:
            group_item.show_group()
            group_input = raw_input("老项目名：\n").strip()
            new_group_input = raw_input("new项目名").strip()
            group_item.modify_group(group_input, new_group_input)
            Tui_menu.end_line()
        elif choice_item == 1 and choice_item_op == 0:
            app_item.show_application()
            Tui_menu.end_line()
        elif choice_item == 1 and choice_item_op == 1:
            app_input = raw_input("请输入app名称：\n")
            parent_app_input = raw_input("请输入父app名称，留空不添加组：\n")
            app_item.add_application(app_input, parent_app_input)
            Tui_menu.end_line()
        elif choice_item == 1 and choice_item_op == 2:
            app_item.show_application()
            app_input = raw_input("请输入要删除的项目名：\n").strip()
            app_item.del_application(app_input)
            Tui_menu.end_line()
        elif choice_item == 1 and choice_item_op == 3:
            app_item.show_application()
            app_input = raw_input("老项目名：\n").strip()
            new_app_input = raw_input("new项目名").strip()
            app_item.modify_application(app_input,new_app_input)
            Tui_menu.end_line()
    app_item.connect.commit()
    app_item.finally_close_all()
