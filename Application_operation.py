#!/bin/env python
# -*- coding:utf-8 -*-
# ******************************************************
# Author       : tianfei hao
# Create Time  : 2017-02-25
# Last modified:
# Email        : talenhao@gmail.com
# Description  : collect listen ip port and connect socket.
# ******************************************************
# 数据库操作

import MySQLdb


class DbInitConnect(object):
    # 初始化基本变量
    def __init__(self):
        self.host = '192.168.1.138'
        self.port = 3306
        self.password = 'yed'
        self.username = 'yed'
        self.db = 'yed_collect'
    # 连接数据库
    
    def Connect(self):
        self.DBcon = MySQLdb.connect(host=self.host,
                               port = self.port,
                               user = self.username,
                               passwd=self.password,
                               db = self.db)
        return self.DBcon
        # 返回指针
    
    def Cursor(self):
        self.Connect()
        self.resultCursor=self.DBcon.cursor()
        return self.resultCursor
    
    def ShowDatabases(self):
        self.Cursor()
        sql_cmd='show create database yed_collect'
        # print(self.DBcon,self.resultCursor)
        self.resultCursor.execute(sql_cmd)
        for self.row in self.resultCursor.fetchall():
            print self.row

    def finally_close_connect(self):
        self.DBcon.close()

class GroupOperation(DbInitConnect):
    def __init__(self):
        # 初始父类的生成器
        # super(DbInitConnect, self).__init__()
        DbInitConnect.__init__(self)
        self.group_table = "appgroup"
        self.Cursor()
        # print(self.host,self.DBcon,self.resultCursor,self.resultCursor.description)
        
    def ShowGroup(self):
        sql_cmd= 'SELECT groupname,parent_group from %s' % self.group_table
        self.resultCursor.execute(sql_cmd)
        for self.row in self.resultCursor.fetchall():
            print(self.row)
            
    def addGroup(self,groupname,parent_groupname='NULL'):
        self.groupname=groupname
        self.parent_groupname=parent_groupname
        sql_cmd = 'INSERT INTO %s (groupname, parent_group) VALUES ("%s", "%s")' % (self.group_table, self.groupname, self.parent_groupname)
        print(sql_cmd)
        self.resultCursor.execute(sql_cmd)
        self.DBcon.commit()
        
    def delGroup(self,groupname):
        self.groupname = groupname
        sql_cmd = 'DELETE FROM %s where groupname="%s";' % (self.group_table, self.groupname)
        print(sql_cmd)
        self.resultCursor.execute(sql_cmd)
        self.DBcon.commit()
        
    def modifyGroup(self,groupname,new_groupname):
        self.groupname = groupname
        self.newgroupname = new_groupname
        sql_cmd = 'UPDATE %s SET groupname = "%s" where groupname = "%s";' %(self.group_table, self.newgroupname, self.groupname)
        print(sql_cmd)
        self.resultCursor.execute(sql_cmd)
        self.DBcon.commit()
        
    def finallyCloseConnect(self):
        self.DBcon.close()


class applicationOperation(GroupOperation):
    def __init__(self):
        # 初始父类的生成器
        # super(DbInitConnect, self).__init__()
        GroupOperation.__init__(self)
        self.projecttable = "application"
    def showApplication(self):
        sql_cmd= 'SELECT projectname,groupname from %s,%s where %s.groupid=%s.group_id' % (self.group_table,self.projecttable,self.group_table,self.projecttable)
        self.resultCursor.execute(sql_cmd)
        for self.row in self.resultCursor.fetchall():
            print(self.row)

    def addApplication(self,projectname,groupname):
        self.groupname=groupname
        self.projectname=projectname
        if not self.groupname:
            self.groupname='in'
        sql_cmd='SELECT groupid from %s where groupname="%s"' % (self.group_table, self.groupname)
        print(sql_cmd)
        self.resultCursor.execute(sql_cmd)
        self.groupid = self.resultCursor.fetchone()[0]
        print('groupid is :',self.groupid)
        sql_cmd='INSERT INTO %s (projectname, group_id) VALUES ("%s", %s)' % (self.projecttable, self.projectname, self.groupid)
        # sql_cmd='INSERT INTO %s (projectname) VALUE ("%s") ' % (self.projecttable, self.projectname)
        print(sql_cmd)
        self.resultCursor.execute(sql_cmd)
        self.DBcon.commit()

    def delApplication(self, projectname):
        self.projectname = projectname
        sql_cmd = 'DELETE FROM %s where projectname="%s";' % (self.projecttable, self.projectname)
        print(sql_cmd)
        self.resultCursor.execute(sql_cmd)
        self.DBcon.commit()

    def modifyApplication(self,projectname,new_projectname):
        self.projectname = projectname
        self.newprojectname = new_projectname
        sql_cmd = 'UPDATE %s SET projectname="%s" where projectname="%s";' %(self.projecttable, self.newprojectname, self.projectname)
        print(sql_cmd)
        self.resultCursor.execute(sql_cmd)
        self.DBcon.commit()

    def finallyCloseConnect(self):
        self.DBcon.close()


class Tui(object):
    def __init__(self):
        self.itemlist=['group','project']
        self.operationlist=["show",'add','del','modify']

    def headerline(self,item):
        self.item=item
        self.startheader = '>'*40+"In "+self.item+" choice: "+'<'*40
        print(self.startheader)
        
    def endline(self):
        self.endheader   = '='*40+'End'+'='*40
        print(self.endheader)
        
    def listitem(self,list):
        self.list=list
        print(zip(range(len(self.list)),self.list))
        
if __name__ == "__main__":
    Tuimenu=Tui()
    Groupitem = GroupOperation()
    Appitem   = applicationOperation()
    flag = True
    Tuimenu.headerline('start')
    while flag:
        Tuimenu.listitem(Tuimenu.itemlist)
        try:
            '''后期考虑添加退出'''
            choiceitem = int(raw_input('请输入项目编号：\n'))
        except ValueError:
            print('Input a Num!')
            continue
        if int(choiceitem) not in range(len(Tuimenu.itemlist)):
            print(range(len(Tuimenu.itemlist)))
            print('Error num')
            continue
        Tuimenu.listitem(Tuimenu.operationlist)
        choiceitem2 = int(raw_input('请输入项目编号：\n'))
        if int(choiceitem2) not in range(len(Tuimenu.operationlist)):
            print(range(len(Tuimenu.operationlist)))
            print('Error num')
            continue
        print('process')
        if choiceitem == 0 and choiceitem2 == 0 :
            Groupitem.ShowGroup()
        elif choiceitem == 0 and choiceitem2 == 1:
            groupinput=raw_input("请输入group名称：\n")
            parentgroupinput=raw_input("请输入父group名称，留空不添加父组：\n")
            Groupitem.addGroup(groupinput,parentgroupinput)
        elif choiceitem == 0 and choiceitem2 ==2:
            Groupitem.ShowGroup()
            groupinput = raw_input("请输入要删除的项目名：\n").strip()
            Groupitem.delGroup(groupinput)
        elif choiceitem == 0 and choiceitem2 == 3:
            Groupitem.ShowGroup()
            groupinput = raw_input("老项目名：\n").strip()
            newgroupinput = raw_input("new项目名").strip()
            Groupitem.modifyGroup(groupinput,newgroupinput)
        elif choiceitem == 1 and choiceitem2 == 0 :
            Appitem.showApplication()
        elif choiceitem == 1 and choiceitem2 == 1:
            appinput=raw_input("请输入app名称：\n")
            parentappinput=raw_input("请输入父app名称，留空不添加组：\n")
            Appitem.addApplication(appinput,parentappinput)
        elif choiceitem == 1 and choiceitem2 ==2:
            Appitem.showApplication()
            appinput = raw_input("请输入要删除的项目名：\n").strip()
            Appitem.delApplication(appinput)
        elif choiceitem == 1 and choiceitem2 == 3:
            Appitem.showApplication()
            appinput = raw_input("老项目名：\n").strip()
            newappinput = raw_input("new项目名").strip()
            Appitem.modifyApplication(appinput,newappinput)
    Tuimenu.endline()
        # for key,value in Tuimenu.listitem():
