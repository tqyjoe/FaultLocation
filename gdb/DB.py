#!/usr/bin/python2
# -*- coding:utf-8 -*-
# 数据库操作封装，用来进行测试用例及断点值相关内容的数据库创建与插入
import sqlite3
import string
import time
import Testcase

class DB:
	def __init__(self, db_filename):
		# logtime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
		# print db_filename + logtime + ".db"
		self.conn = sqlite3.connect(db_filename)
		self.conn.isolation_level = None
		self.execute("create table if not exists breakpoint(id integer primary key, method TEXT, file TEXT, lineNum integer)")
		self.execute("create table if not exists testcase(name TEXT primary key, para TEXT, result TEXT, expected TEXT, pass BOOLEAN, debuggee TEXT)")
		self.execute("create table if not exists bp_tc(id integer primary key autoincrement, lineNum integer REFERENCES breakpoint(lineNum), tc_name TEXT REFERENCES testcase(name), val TEXT)")
		self.execute("create table if not exists bp_vars(lineNum integer,break_var TEXT)")
		self.execute("create table if not exists bp_line_var(lineNum integer,break_var_line TEXT,num integer,method TEXT )")
		self.conn.commit()

	# 执行SQL语句
	def execute(self,  cmd):
		return self.conn.execute(cmd)

	# 数据库中插入断点
	def insertBreakpoint(self,  b):
		ss = b.split("\n")
		for s in ss:
			if 0<s.find("breakpoint     keep y"):
				s2 = s.split()
				s3 = s2[8].split(":")
				self.execute("insert into breakpoint values (%s, '%s', '%s', %s)"%(s2[0],  s2[6],  s3[0],  s3[1]))
		self.conn.commit()

	# 数据库中插入测试用例
	def insertTestcase(self, name, s,  result,  result_right,  same,  debuggee):
		ss = str(s).replace("'", "''")
		self.execute("insert into testcase values ('%s', '%s', '%s', '%s', %d, '%s')"%(name,   ss,  result,   result_right,  same,  debuggee))

	# # 数据库中插入指定断点处指定测试用例的内存值
	# def insertVarValue(self, testcase,  breakpoint,  state):
	# 	ss = str(state).replace("'", "''")
	# 	sqlcmd = "insert into bp_tc(bp_id, tc_name, val) values (%s, '%s', '%s')"%(breakpoint,  testcase, ss)
	# 	# print "\nsql cmd : \n" + sqlcmd + "\n\n"
	# 	cur = self.execute("insert into bp_tc(bp_id, tc_name, val) values (%s, '%s', '%s')"%(breakpoint,  testcase, ss))

	# 关闭数据库
	def closeDB(self):
		self.conn.close()

	# 删除表
	def droptable(self, tablename):
		self.execute("drop table if exists " + tablename)

