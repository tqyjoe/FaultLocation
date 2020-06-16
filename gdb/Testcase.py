#!/usr/bin/python2
# -*- coding:utf-8 -*-
# 测试用例对象及数据库插入测试用例信息的操作
import string
import popen2
import gccunions
import mmapunions
import DB
import os

# pName = "tcas"
 # 测试用例对象
class Testcase:
	def __init__(self, debuggee, invocation, \
				union_table = None, filter = None):
		self.debuggee = debuggee
		if isinstance(invocation, type([])):
			self.invocation = invocation
		else:
			self.invocation = [invocation]
		self.union_table = union_table
		self.filter = filter

# testcase-format: (debuggee, breakpoint, invocation, union_table) 
testcases = {
	# `sample.c' Delta Debugging test cases
	
	#"sample-fail":
	#Testcase("tests/sample", 8, "run 11 14 13 16"),

	#"sample-pass":
	#Testcase("tests/sample", 8, "run 9 8 7"),
	
	#"sample-debook":
	#Testcase("tests/sample", "run 11 14", 0),
	
	#"printtokens":
	#Testcase("print_tokens", "run tests/uslin.1477", 1)
}

# 初始化测试用例集合信息，得到个测试用例运行结果及正确性
def initTestcase(db,  version, datafile,pName):

	debuggee = "versions_"+pName+"/"+version+"/"+pName
	read = open(datafile)

	fout = popen2.Popen3("gcc "+"versions_"+pName+"/"+version+"/"+pName+".c" +" -lm -g -o "+"versions_"+pName+"/"+version+"/"+pName)
	t = "1"
	result = ""
	while t:
		t = fout.fromchild.readline()
		result = result+t
	print result
	#print "sssssssssssssssssssss\n"
	lines=read.readlines()
	linenumber = 0
	same=1
	# path2 = "/home/sr/program/all_program/FaultLocation/gdb/a"
	# if not os.path.exists(path2):
	# 	os.mknod(path2)
	# f = open(path2, "a")
	# f.write("55554" + "\n")
	# f.close()
	for line in lines:
	#while line and linenumber<=:
		linenumber += 1
		s = line[:len(line) - 1]
		print "\r------run testcase %d " % linenumber,
		
		#print(linenumber,s)
		fout = popen2.Popen3("versions_"+pName+"/"+version+"/./"+pName+" "+s)
		fout2 = popen2.Popen3("versions_"+pName+"/"+"right/./"+pName+" "+s)
		t = "1"
		result = ""
		while t:
			t = fout.fromchild.readline()
			#result = result+t
			result =result + str(t).replace("'", "''")
		t = "1"
		result2 = ""
		while t:
			t = fout2.fromchild.readline()
			#result2 = result2+t
			result2 = result2+ str(t).replace("'", "''")
		# f.write(s+":\n"+result2+"\n")
		if result2.find("Error:") == 0 or not result2:
			continue
		else:
			testcases[pName + '%d'%linenumber] = Testcase(debuggee, "run "+s)
			same = result == result2;
			#print("print_tokens" + '%d'%linenumber, s,  result,  result2,  same,  debuggee)
			#exit(0)
			db.insertTestcase(pName + '%d'%linenumber, s,  result,  result2,  same,  debuggee)
		
		#line=read.readline()
		#s = line[:len(line)-1]
	read.close
	# f.close()
