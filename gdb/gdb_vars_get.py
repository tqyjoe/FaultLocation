#!usr/bin/python2
# -*- coding:utf-8 -*-
# gdb得到断点处内存值的操作，以及将各个测试用例各个断点处内存值存入数据库中

import sys, os
import string
import re
import time
import popen2
import sqlite3
import cStringIO

# Own modules
import Testcase
from GDB import GDB
from TimedMessage import TimedMessage
from DB import DB

# GDB interface with special state fetching capability
class StateGDB(GDB):
	CHAR_PATTERN    = re.compile("(?P<value>\d+) +(?P<character>'.*')")
	STRING_PATTERN  = re.compile('(?P<pointer>0x[^ ]+) +(?P<string>".*")')
	POINTER_PATTERN = re.compile(".*(?P<value>0x[0-9a-f]+)")
	FUNCTION_POINTER_PATTERN = re.compile(".*(?P<value>0x[0-9a-f]+) <(?P<identifier>[^>]*)>")

	def _unfold_pointer(self, name, frame, value, vars):
		if string.find(value, "(void *)") >= 0:
			return                  # Generic pointer - ignore

		if value == "0x0":
			vars[(name, frame)] = "0x0" # NULL pointer
			return

		deref_value = self.question("output *(" + name + ")")

		if deref_value[:2] == '{\n':
			# We have a pointer structure.  Dereference elements.
			SEP = " = "
			for line in string.split(deref_value, "\n"):
				separator = string.find(line, SEP)
				if separator < 0:
					continue

				member_name = name + "->" + line[0:separator]
				member_value = line[separator + len(SEP):]

				self._fetch_values(member_name, frame, member_value, vars)

			return

		if deref_value[0] == '{':
			# Some function pointer.  Leave it unchanged.
			return

		# Otherwise, assume it's an array or object on the heap
		# (hopefully)

		if name == "argv":
			# Special handling for program arguments.
			elems = 4096
		else:
			# This trick will get the number of elements (if we use
			# GNU malloc on Linux)
			elems = self.question("output (((int *)(" + name +
								"))[-1] & ~0x1) /" +
								"sizeof(*(" + name + "))")
			#print("###########"+elems)
			if len(elems)<=20:
				elems = string.atoi(elems)
			else:
				return
				
		if elems > 10000:
			return                      # Cannot handle this

		beyond = 1                      # Look 1 elements beyond bounds

		for i in range(0, elems + beyond):
			elem_name = name + "[" + `i` + "]"
			elem_value = self.question("output " + elem_name)

			self._fetch_values(elem_name, frame, elem_value, vars)
			if name == "argv" and elem_value == "0x0":
				break               # Stop it


	# Fetch a value NAME = VALUE from GDB into VARS, with special
	# handling of pointer structures.
	def _fetch_values(self, name, frame, value, vars):
		value = string.strip(value)
		value = string.replace(value, "\n", "")

		# print "Handling " + name + " = " + value

		# GDB reports characters as VALUE 'CHARACTER'.  Prefer CHARACTER.
		m = self.CHAR_PATTERN.match(value)
		if m is not None:
			vars[(name, frame)] = m.group('character')
			return

		# GDB reports strings as POINTER "STRING".  Prefer STRING.
		m = self.STRING_PATTERN.match(value)
		if m is not None:
			vars[(name, frame)] = m.group('string')
			return

		# GDB reports function pointers as POINTER <IDENTIFIER>.
		# Prefer IDENTIFIER.
		m = self.FUNCTION_POINTER_PATTERN.match(value)
		if m is not None:
			vars[(name, frame)] = m.group('identifier')
			return

		# In case of pointers, unfold the given data structure
		if self.POINTER_PATTERN.match(value):
			self._unfold_pointer(name, frame, value, vars)
			return

		# Anything else: Just store the value
		vars[(name, frame)] = value


	# Store mapping (variable, frame) => values in VARS
	def _fetch_variables(self, frame, vars):
		SEP = " = "
		IDENTIFIER = re.compile("[a-zA-Z_]")
#        print "-----------------"
#        print self.question("info variables")
#        print "-----------------"
		for query in ["info locals", "info args"]:
			list = self.question(query)
			lines = string.split(list, "\n")

			# Some values as reported by GDB are split across several lines
			for i in range(1, len(lines)):
				if lines[i] != "" and not IDENTIFIER.match(lines[i][0]):
					lines[i - 1] = lines[i - 1] + string.strip(lines[i])

			for line in lines:
				separator = string.find(line, SEP)
				if separator > 0:
					name  = line[0:separator]
					value = line[separator + len(SEP):]
					self._fetch_values(name, frame, value, vars)

		return vars


	# Return mapping (variable, frame) => values
	def state(self):
		t = TimedMessage("Capturing state")
		vars = {}
		frame = 0
		
		reply = "#0"
		while string.find(reply, "#") != -1:
			reply = self.question("down")

		reply = "#0"
		while string.find(reply, "#") != -1:
			self._fetch_variables(frame, vars)
			reply = self.question("up")
			frame = frame + 1

		t.outcome = `len(vars.keys())` + " variables"
		return vars

	# Return (opaque) list of deltas
	def deltas(self, state_1, state_2):
		deltas = []
		for var in state_1.keys():
			value_1 = state_1[var]
			if not state_2.has_key(var):
				continue                # Uncomparable

			value_1 = state_1[var]
			value_2 = state_2[var]
			if value_1 != value_2:
				deltas.append((var, value_1, value_2))

		deltas.sort()
		return deltas


	# Apply (opaque) list of deltas to STATE_1
	def apply_deltas(self, deltas):
		cmds = self.delta_cmds(deltas)
		for cmd in cmds:
			self.question(cmd)

	def delta_cmds(self, deltas):
		cmds = []
		current_frame = None
		for delta in deltas:
			(var, value_1, value_2) = delta
			(name, frame) = var
			if frame != current_frame:
				cmds.append("frame " + `frame`)
				current_frame = frame

			cmds.append("set variable " + name + " = " + value_2)

		return cmds

	# #按行号插入断点
	# def insertBreakpoints(self,lineNums):
	# 	if lineNums:
	# 		for num in lineNums:
	# 			self.question("b %s"%num)

	def insertBreakpoints(self,start,end):
		count=start
		while count<=end:
			self.question("b %s"%count)
			count+=1
		self.question("enable once b " + str(start) + "-" + str(end))

	def enableBreakList(self, breakpoints):
		for point in breakpoints:
			self.question("enable once b " + point)

	def getBreakLineVars(self,conn,cmd_run,tc_name,dict_method_line,dict_line_var,lines, pName, dic_cycle, dic_not_cycle_flag,dic_mul):
		output = self.question(cmd_run)
		last_var_list = []
		last_exist_flag = False
		disenable_list = []
		record_linenum = []
		# path2 = "/home/npu/program/20190603/FaultLocation/gdb/a"
		# if not os.path.exists(path2):
		# 	os.mknod(path2)
		# f = open(path2, "a")
		# f.write(output+"\n")
		breakLoc = output.find("\nBreakpoint ")
		while breakLoc >= 0:
			s = output
			# num 断点所在行号
			# startLoc = s.find("\nBreakpoint ")
			loc = s.find(pName+".c:",breakLoc) + len(pName+".c:")
			num = s[loc:s.find("\n", loc)]
			# f.write(output + "\n")
			# f.write("################"+num+"\n")
			loc_comma = s.find(",",breakLoc)

			b_id = s[breakLoc+12:loc_comma]

			loc_parenthes = s.find("(",breakLoc)
			methodName = s[loc_comma+1:loc_parenthes-1].strip()
			# f.write(output)
			# info_local = self.question("info locals")
			# local_list = self.get_local_arg_var(info_local)
			# info_global_var = self.question("info var")
			# global_var_list = self.get_global_var(info_global_var,pName)
			# # f.write(info_global_var)
			# var_list = []
			# var_list.extend(local_list)
			# if methodName.find("main") < 0:
			# 	info_arg = self.question("info arg")
			# 	arg_list = self.get_local_arg_var(info_arg)
			# 	var_list.extend(arg_list)
			# var_list.extend(global_var_list)

			var_list, exist_flag = self.getLineVarList(conn, int(num), methodName,pName)

			if dict_method_line:
				if methodName in dict_method_line:
					lastNum = dict_method_line[methodName]
					dic_lastline,not_exist_list = self.find_line_var(conn,lastNum,last_var_list, lines,methodName,last_exist_flag,dic_mul)
					for not_exist_var in not_exist_list:
						dic_lastline[not_exist_var]=dict_line_var[lastNum][not_exist_var]
					dic_lastline_str = str(dic_lastline).replace("'", "''")
					dic_line,not_exist_list = self.find_line_var(conn,int(num),var_list,lines,methodName,exist_flag,dic_mul)
					dict_method_line[methodName]=int(num)
					dict_line_var.clear()
					dict_line_var[int(num)]=dic_line
					if dic_lastline:
						conn.execute("insert into bp_tc(lineNum, tc_name, val)  values('%d','%s','%s')"%(lastNum,tc_name,dic_lastline_str))
						# conn.commit()
					disenable_list.append(b_id)
					if int(num) in dic_cycle:
						for cycle_line in dic_cycle[int(num)]:
							if ((int(num) in dic_not_cycle_flag) and dic_not_cycle_flag[int(num)]) or (cycle_line in record_linenum):
								cycle_list, cycle_flag = self.getLineVarList(conn, cycle_line, methodName,pName)
								dic_line_cycle, not_exist_list = self.find_line_var(conn, cycle_line, cycle_list,
																					lines, methodName,
																					cycle_flag,dic_mul)
								if not_exist_list:
									query_cycle = conn.execute(
										"select val from bp_tc where tc_name='%s' and lineNum='%d' " % (
										tc_name, cycle_line))
									query_result = query_cycle.fetchall()
									query_val = query_result[len(query_result) - 1][0]
									dic_vars = eval(query_val)
									for not_exist in not_exist_list:
										dic_line_cycle[not_exist] = dic_vars[not_exist]
								if dic_line_cycle:
									dic_line_str = str(dic_line_cycle).replace("'", "''")
									conn.execute("insert into bp_tc(lineNum, tc_name, val)  values('%d','%s','%s')" % (
									cycle_line, tc_name, dic_line_str))
									# f.write(str(cycle_line) + " : " + dic_line_str + "\n")
					record_linenum.append(int(num))
				else:
					lastMethodName = dict_method_line.keys()[0]
					lastNum = dict_method_line[lastMethodName]
					dic_lastline = dict_line_var[lastNum]
					dic_line,not_exist_list = self.find_line_var(conn,int(num),var_list, lines,methodName,exist_flag,dic_mul)
					dict_method_line.clear()
					dict_line_var.clear()
					dict_method_line[methodName] = int(num)
					dict_line_var[int(num)] = dic_line
					dic_lastline_str = str(dic_lastline).replace("'", "''")
					if dic_lastline:
						conn.execute("insert into bp_tc(lineNum, tc_name, val)  values('%d','%s','%s')" % (lastNum, tc_name, dic_lastline_str))
						# conn.commit()
					# self.enableBreakList(disenable_list)
					disenable_list=[]
					disenable_list.append(b_id)
					record_linenum=[]
					record_linenum.append(int(num))
			else:
				dic_line,not_exist_list = self.find_line_var(conn,int(num),var_list, lines,methodName,exist_flag,dic_mul)
				dict_method_line[methodName] = int(num)
				dict_line_var[int(num)] = dic_line
				disenable_list.append(b_id)
				record_linenum.append(int(num))
			last_var_list = var_list
			last_exist_flag = exist_flag
			output = self.question("c")
			breakLoc = output.find("\nBreakpoint ")
		for methodName in dict_method_line:
			linenum = dict_method_line[methodName]
			dic = dict_line_var[linenum]
			dic_str = str(dic).replace("'", "''")
			if dic:
				conn.execute("insert into bp_tc(lineNum, tc_name, val)  values('%d','%s','%s')" % (linenum, tc_name, dic_str))
			if ((int(num) in dic_not_cycle_flag) and dic_not_cycle_flag[int(num)]) or (int(num) in dic_cycle):
				for cycle_line in dic_cycle[int(num)]:
					if cycle_line in record_linenum:
						cycle_list, cycle_flag = self.getLineVarList(conn, cycle_line, methodName,pName)
						dic_line_cycle, not_exist_list = self.find_line_var(conn, cycle_line, cycle_list,
																			lines, methodName,
																			cycle_flag,dic_mul)
						if not_exist_list:
							query_cycle = conn.execute(
								"select val from bp_tc where tc_name='%s' and lineNum='%d' " % (
									tc_name, cycle_line))
							query_result = query_cycle.fetchall()
							query_val = query_result[len(query_result) - 1][0]
							dic_vars = eval(query_val)
							for not_exist in not_exist_list:
								dic_line_cycle[not_exist] = dic_vars[not_exist]
						if dic_line_cycle:
							dic_line_str = str(dic_line_cycle).replace("'", "''")
							conn.execute("insert into bp_tc(lineNum, tc_name, val)  values('%d','%s','%s')" % (
								cycle_line, tc_name, dic_line_str))
							# f.write(str(cycle_line)+" : "+dic_line_str+"\n")
		conn.commit()
		# f.close()
		# disenable_list.append(int(num))
		# self.enableBreakList(disenable_list)


	def getLineVarList(self, conn, linenum, methodName,pName):
		query_varList = conn.execute(
			"select break_var_line from bp_line_var where lineNum='%d'" % (linenum))
		query_result = query_varList.fetchall()
		if len(query_result) > 0:
			exist_flag = True
			return query_result, exist_flag
		else:
			info_local = self.question("info locals")
			local_list = self.get_local_arg_var(info_local)
			info_global_var = self.question("info var")
			global_var_list = self.get_global_var(info_global_var,pName)
			var_list = []
			var_list.extend(local_list)
			if methodName.find("main") < 0:
				info_arg = self.question("info arg")
				arg_list = self.get_local_arg_var(info_arg)
				var_list.extend(arg_list)
			var_list.extend(global_var_list)
			exist_flag = False
			return var_list, exist_flag

	def get_global_var(self,info_var_result,pName):
		# temp = info_var_result.split("Non-debugging symbols")
		# temp1 = temp[0]
		# temp2 = temp1.split(";")
		# g_var = []
		# for temp3 in temp2:
		# 	temp4 = temp3.split()
		# 	len_4 = len(temp4)
		# 	if len_4 >= 2:
		# 		var = temp4[len_4 - 1]
		# 		var1 = var.split("[")[0]
		# 		var2 = var1.replace("*", "")
		# 		g_var.append(var2)
		# g_var.append(temp4[len_4 - 1])
		# path2 = "/home/npu/program/20190603/FaultLocation/gdb/a"
		# if not os.path.exists(path2):
		# 	os.mknod(path2)
		# f = open(path2, "a")

		# return g_var

		temp = info_var_result.split(pName+".c:")
		g_var = []
		if len(temp)>1:
			temp1 = temp[1]
			temp1_1 = temp1.split(".c:")
			temp1_2 = temp1_1[0]
			temp2 = temp1_2.split(";")
			count = 1
			for temp3 in temp2:
				if count < len(temp2):
					temp4 = temp3.split()
					len_4 = len(temp4)
					if len_4 >= 2:
						var = temp4[len_4 - 1]
						var1 = var.split("[")[0]
						var2 = var1.replace("*","")
						g_var.append(var2)
				count+=1
		h_names = ["tokens","stream"]
		for h_name in h_names:
			temp = info_var_result.split(h_name + ".h:")
			if len(temp) > 1:
				temp1 = temp[1]
				temp1_1 = temp1.split("\nFile")
				temp1_2 = temp1_1[0]
				temp2 = temp1_2.split(";")
				count = 1
				for temp3 in temp2:
					if count < len(temp2):
						temp4 = temp3.split()
						len_4 = len(temp4)
						if len_4 >= 2:
							var = temp4[len_4 - 1]
							var1 = var.split("[")[0]
							var2 = var1.replace("*", "")
							g_var.append(var2)
					count += 1
		# f.write(str(g_var) + "\n")
		return g_var

	def get_local_arg_var(self,info_local):
		result = info_local.split("\n")
		var_list = []
		for line in result:
			get_var = line.split("=")
			if len(get_var) >= 2:
				key = get_var[0].strip()
				var_list.append(key)
		return var_list

	def find_line_var(self, conn, lineNum, var_list, lines, methodName, exist_flag,dic_mul):
		dic = {}
		not_exist_list = []
		# path2 = "/home/sr/program/20190531/FaultLocation/gdb/a"
		# path2 = "/home/npu/program/20190603/FaultLocation/gdb/a"
		# if not os.path.exists(path2):
		# 	os.mknod(path2)
		# f = open(path2, "a")
		# f.write(str(var_list) + "\n")
		# f.close()
		for var in var_list:
			if exist_flag:
				var = var[0]
			else:
				var = var
			var = var.replace("*", "")
			var = var.replace(" ", "")
			pattern = "\W" + var + "\W"
			# linew
			# f.write(var)
			if lineNum not in dic_mul:
				match_line = lines[lineNum-1]
			else:
				match_line = ""
				for mul_linenum in dic_mul[lineNum]:
					match_line += lines[mul_linenum-1]
			# f.write(str(lineNum)+"$$$$"+match_line+"\n")
			matchObject = re.search(pattern, match_line, re.M | re.DOTALL)
			if matchObject:
				var_val = self.question("p " + var)
				var_equal_loc = var_val.find("=")
				var_result = var_val.split("=")
				if len(var_result) == 2 or ((len(var_result) >= 2 and var_result[1].find("0x") > 0) or (len(var_result) >= 2 and var_result[1].strip().find("{")!=0)):
					if var_result[1].find("0x") < 0:
						if var_result[1].find("{") < 0:
							eq_loc = var_val.find("=")
							save_val = var_val[eq_loc+1:].strip().strip('"')
							dic[var] = save_val
							# bp_line_var(lineNum
							# integer, break_var_line
							# TEXT
							query_result = conn.execute(
								"select * from bp_line_var where lineNum='%d' and break_var_line='%s'" % (lineNum, var))
							if len(query_result.fetchall()) == 0:
								conn.execute("insert into bp_line_var values('%d','%s',0,'%s')" % (lineNum, var,methodName))
								# conn.commit()
						else:
							pattern_array = "\W" + var + "\[\s*\w+\s*\]"
							matchArray = re.findall(pattern_array, match_line, re.M | re.DOTALL)
							count = 0
							for match in matchArray:
								arraySub = match.split("[")[1].replace("]", "").strip()
								try:
									sub = float(arraySub)
								except:
									sub = arraySub
								arrayVal = self.question("p " + var + "[" + str(sub) + "]")
								array_result = arrayVal.split("=")
								if len(array_result) == 2:
									if count == 0:
										dic[var] = array_result[1].strip()
										query_result = conn.execute(
											"select * from bp_line_var where lineNum='%d' and break_var_line='%s'" % (
											lineNum, var))
										if len(query_result.fetchall()) == 0:
											conn.execute("insert into bp_line_var values('%d','%s','%d','%s')" % (
											lineNum, var, count,methodName))
											# conn.commit()
									else:
										dic[var + "#" + str(count)] = array_result[1].strip()
										query_result = conn.execute(
											"select * from bp_line_var where lineNum='%d' and break_var_line='%s'" % (
											lineNum, var))
										if len(query_result.fetchall()) == 0:
											conn.execute("insert into bp_line_var values('%d','%s','%d','%s')" % (
											lineNum, var, count, methodName))
											# conn.commit()
									count += 1

					elif var_result[1].find("*") < 0:
						var_address_val = var_result[1].strip()
						var_address = var_address_val.split(" ")[0].strip()
						get_var_val = var_val.split(var_address)[1].strip().strip('"')
						# get_var_val = var_address_val.replace(var_address, "").strip()
						query_result = conn.execute(
							"select * from bp_line_var where lineNum='%d' and break_var_line='%s'" % (lineNum, var))
						if len(query_result.fetchall()) == 0:
							conn.execute("insert into bp_line_var values('%d','%s',0,'%s')" % (lineNum, var, methodName))
							# conn.commit()
						dic[var] = get_var_val
					else:
						pattern_array = "\W" + var + "\[\s*\w+\s*\]"
						matchArray = re.findall(pattern_array, match_line, re.M | re.DOTALL)
						count = 0
						for match in matchArray:
							arraySub = match.split("[")[1].replace("]", "").strip()
							try:
								sub = float(arraySub)
							except:
								sub = arraySub
							arrayVal = self.question("p " + var + "[" + str(sub) + "]")
							array_result = arrayVal.split("=")
							if len(array_result) == 2:
								if count == 0:
									dic[var] = array_result[1].strip()
								else:
									dic[var + "#" + str(count)] = array_result[1].strip()
								query_result = conn.execute(
									"select * from bp_line_var where lineNum='%d' and break_var_line='%s'" % (
									lineNum, var))
								if len(query_result.fetchall()) == 0:
									conn.execute(
										"insert into bp_line_var values('%d','%s','%d','%s')" % (lineNum, var, count, methodName))
									# conn.commit()
								count += 1
						if count == 0:

							struct_val = self.question("p *" + var)
							struct_content = struct_val.split("{")
							if len(struct_content) == 1:
								dic[var] = "1"
								query_result = conn.execute(
									"select * from bp_line_var where lineNum='%d' and break_var_line='%s'" % (
										lineNum, var))
								if len(query_result.fetchall()) == 0:
									conn.execute("insert into bp_line_var values('%d','%s','%d','%s')" % (
										lineNum, var, 0, methodName))
							else:
								struct_array = struct_content[1].replace("}", "").split(",")
								for struct_var in struct_array:
									struct_result = struct_var.split("=")
									try:
										dic[var + "." + struct_result[0].strip()] = struct_result[1].strip()
										query_result = conn.execute(
											"select * from bp_line_var where lineNum='%d' and break_var_line='%s'" % (
												lineNum, var + "." + struct_result[0].strip()))
										if len(query_result.fetchall()) == 0:
											conn.execute("insert into bp_line_var values('%d','%s','%d','%s')" % (
												lineNum, var + "." + struct_result[0].strip(), 0, methodName))
									except:
										dic[var] = "1"
										query_result = conn.execute(
											"select * from bp_line_var where lineNum='%d' and break_var_line='%s'" % (
												lineNum, var))
										if len(query_result.fetchall()) == 0:
											conn.execute("insert into bp_line_var values('%d','%s','%d','%s')" % (
												lineNum, var, 0, methodName))

				elif len(var_result) > 2:
					# path2 = "/home/npu/program/20190603/FaultLocation/gdb/a"
					# if not os.path.exists(path2):
					# 	os.mknod(path2)
					# f = open(path2, "a")
					# f.write(str(var_val) + "\n")
					struct_content = var_val.split("{")
					if len(struct_content)==1:
						dic[var] = "1"
						query_result = conn.execute(
							"select * from bp_line_var where lineNum='%d' and break_var_line='%s'" % (
								lineNum, var))
						if len(query_result.fetchall()) == 0:
							conn.execute("insert into bp_line_var values('%d','%s','%d','%s')" % (
								lineNum, var, 0, methodName))
					else:
						struct_array = struct_content[1].replace("}", "").split(",")
						for struct_var in struct_array:
							struct_result = struct_var.split("=")
							try:
								dic[var + "." + struct_result[0].strip()] = struct_result[1].strip()
								query_result = conn.execute(
									"select * from bp_line_var where lineNum='%d' and break_var_line='%s'" % (
									lineNum, var + "." + struct_result[0].strip()))
								if len(query_result.fetchall()) == 0:
									conn.execute("insert into bp_line_var values('%d','%s','%d','%s')" % (
									lineNum, var + "." + struct_result[0].strip(), 0, methodName))
							except:
								dic[var] = "1"
								query_result = conn.execute(
									"select * from bp_line_var where lineNum='%d' and break_var_line='%s'" % (
										lineNum, var))
								if len(query_result.fetchall()) == 0:
									conn.execute("insert into bp_line_var values('%d','%s','%d','%s')" % (
										lineNum, var, 0, methodName))
								# conn.commit()
				else:
					not_exist_list.append(var)
		# dic_line_str = str(dic).replace("'", "''")
		# f.close()
		conn.commit()
		return dic, not_exist_list


def saveTC(version, dbfilename, datafile,pName,pathFile,recordFile,mulFile):
	print "\t\trun and write information of testcases into database..."
	db = DB(dbfilename)
	Testcase.initTestcase(db, version, datafile,pName)
	print "\n"
	
	print "\t\tset breakpoints and write variable values on them into database..."
	testcase = Testcase.testcases.values()[0]
	gdb = StateGDB(testcase.debuggee)
	# f = open(recordFile,"r")
	# lines = f.readlines()
	# data =[]
	# for line in lines:
	# 	data.append(int(line))
	gdb.insertBreakpoints(1, 11000)
	# f.write("hello : "+str(len(data)))
	# f.close()

	# gdb.insertBreakpoints(1,172)

	output = gdb.question("info b")

	# 断点数据存入数据库
	# 填表breakpoint
	db.insertBreakpoint(output)
	totalcount = len(Testcase.testcases)

	v_num = int(version.replace("v", ""))
	record = open(recordFile + "/"+pName+"/record")
	recordLines = record.readlines()
	v_name = recordLines[v_num - 1].split(":")[1].strip()
	v_File = open(recordFile + "/"+pName+"/"+ v_name)
	# v_File = open(recordFile + "/" + pName + "/1")
	lineNum_lines = v_File.readlines()
	dic_cycle = {}
	dic_not_cycle_flag = {}
	for line in lineNum_lines:
		if line:
			linenums = line.split(" ")
			key = int(linenums[0])
			num = 1
			linenum_list = []
			while num < len(linenums) / 2:
				start = int(linenums[num * 2 - 1])
				end = int(linenums[num * 2])
				while start <= end:
					linenum_list.append(start)
					start += 1
				num += 1
			if int(linenums[len(linenums)-1])==1:
				dic_not_cycle_flag[key] = True
			else:
				dic_not_cycle_flag[key] = False
			dic_cycle[key] = linenum_list

	# mul = open(mulFile+ "/"+pName+"/mul")
	# mulLines = mul.readlines()
	# mul_name = mulLines[v_num - 1].split(":")[1].strip()
	# mul_File = open(mulFile + "/" + pName + "/" + mul_name)
	# mul_lines = mul_File.readlines()
	dic_mul = {}
	# for line in mul_lines:
	# 	if line:
	# 		linenums = line.split(" ")
	# 		key = int(linenums[0])
	# 		mul_list = []
	# 		for linenum in linenums:
	# 			mul_list.append(int(linenum))
	# 		dic_mul[key] = mul_list

	# gdb.get_global_var(db.conn,gdb.question("info var"))
	cFile = open(pathFile + "/" + pName + ".c")
	lines = cFile.readlines()
	# return_loc_list = []
	# for loc in range(len(lines)):
	# 	if line.find("return")>0:
	# 		return_loc_list.append(loc+1)
	count = 0
	# path2 = "/home/sr/program/20190531/FaultLocation/gdb/a"
	# if not os.path.exists(path2):
	# 	os.mknod(path2)
	# f = open(path2, "a")
	# f.write("######################" + "\n")
	for testcase_name in Testcase.testcases:
		# f.write("$$$$$$$$$$$$$$$$$" + "\n")
		testcase = Testcase.testcases.get(testcase_name)
		dict_method_line = {}
		dict_line_var = {}
		count += 1
		print "\r\t%6d/%-6d" % (count, totalcount),
		# print "##########################################\n"
		sys.setrecursionlimit(100)
		gdb.getBreakLineVars(db.conn, testcase.invocation, testcase_name, dict_method_line, dict_line_var, lines, pName, dic_cycle,dic_not_cycle_flag,dic_mul)
		test=gdb.question("enable once b " + str(1) + "-" + str(9300))
		# print "\r\t%s" % (gdb.question("info b ")),
	# gdb.getBreakVars(db.conn,testcase.invocation,testcase_name)
	# f.close()
	print "\n\nDone."

if __name__ == '__main__':
	if len(sys.argv) != 8:
		print("Error. You should input 5 parameters."+str(len(sys.argv)))
		exit(1)
	saveTC(sys.argv[1], sys.argv[2], sys.argv[3],sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7])
