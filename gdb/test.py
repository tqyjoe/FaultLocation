#!usr/bin/python2
# -*- coding:utf-8 -*-
import gdb_vars_get
import sys,os
import popen2
import sqlite3
import random

def getVars(self,debuggee):
    gdb = gdb_vars_get.StateGDB(debuggee)

def storeVars(vars):
    dic = {}

    dic["2"] = "1"
    return dic

if __name__ == '__main__':
    debuggee = sys.argv[1]
    path = sys.argv[2]
    # path1 = sys.argv[3]
    # path2 = sys.argv[4]
    # path3 = sys.argv[5]
    # #
    # #
    # datafile = open(path1)
    # trainfile = open(path2,"a")
    # testfile = open(path3,"a")
    # lines = datafile.readlines()
    # for line in lines:
    #     if random.random()>0.25:
    #         trainfile.write(line)
    #     else:
    #         testfile.write(line)



    if not os.path.exists(path):
        os.mknod(path)
    f = open(path,"a")

    # str = 'hello'
    # # str.encode(encoding='utf-8')
    # # f.write(str(str.encode(encoding="utf-8")))
    # num1 = pow(10,2)
    # f.write(num1)
    # fout = popen2.Popen3(
    #     "gcc tcas.c" + " -std=c99 -lm -g -o tcas" )
    # a = "a:1|b:2"
    # a = {}
    # a["123"]="124"
    # # # dic = eval(a)
    # # # dic["b"] = "612"
    # val = str(a).replace("'", "''")
    conn = sqlite3.connect("/home/npu/program/20190603/FaultLocation/schedule2_db/schedule2_v2.db")
    count = conn.execute("select tc_name from bp_tc group by tc_name order by tc_name")
    result = count.fetchall()
    for res in result:
        f.write(str(res[0])+"\n")
    conn.close()

    # conn.execute("create table if not exists test(id integer primary key autoincrement,break_var TEXT)")
    # conn.commit()
    #
    # data = ["911 1 1 4194  242 4667 1  401  399 1 1 1",
    #         "548 1 1 2625  249 1679 0  641  501 1 1 1",
    #         "763 0 0  907  444 1881 0  741  399 0 0 1"]
    # # lineNum = [2, 3]
    # cflie = open(debuggee+".c")
    # lines = cflie.readlines()
    # gdb = gdb_vars_get.StateGDB(debuggee)
    # gdb.question("b 50")
    # gdb.question("b 51")
    # gdb.question("b 52")
    # gdb.question("b 53")
    #
    # # out = gdb.question("info b")
    # out = gdb.question("run " + data[1])
    # dict_method_line = {}
    # dict_line_var = {}
    # gdb.getBreakLineVars(conn,"run " + data[1],"tcas1",dict_method_line,dict_line_var,lines,f)
    # all_var = ["Positive_RA_Alt_Thresh"]
    # dic_lastline_str = gdb.find_line_var(conn, 50, all_var, " Positive_RA_Alt_Thresh[0] = 400;")
    # dic_line_str = gdb.find_line_var(conn, 51, all_var, " Positive_RA_Alt_Thresh[1] = 500;")
    # f.write(out+"\n")
    # f.write("50: "+dic_lastline_str+"\n")
    # f.write("51: " + dic_line_str)


    # gobal_vars = conn.execute("select break_var from bp_vars where lineNum=-1")
    # results = gobal_vars.fetchall()
    # val_dic={}
    # for var in results:
    #     gobal_var = gdb.question("p " + var[0])
    #     gobal_result = gobal_var.split("=")
    #     if len(gobal_result) >= 2:
    #         val_dic[var[0]] = gobal_result[len(gobal_result) - 1].strip()
    # val = str(val_dic).replace("'", "''")
    # # f.write(val)
    #
    # line_single = conn.execute("select val from bp_tc where lineNum='%d' and tc_name='%s' " % (148, "tcas235"))
    # result = line_single.fetchone()
    # f.write(eval(result[0])['Other_RAC'])


    # gobal_local = gdb.question("p Up_Separation")
    # val = gobal_local.split("=")

    # results = conn.execute("select break_var from bp_vars where lineNum=150")
    #
    # all_var = results.fetchall()
    # for var in all_var:
    #     f.write(var[0]+"\n")
    # conn.execute("insert into test(break_var) values ('%s')"%val[1].strip())
    # conn.commit()



    # out = gdb.getBreakVars(conn,data[1])
    # f.write(out)
    # output = gdb.question("info locals")
    # result = output.split("\n")
    # dic = {}
    # for line in result:
    #     get_var = line.split("=")
    #     if len(get_var) >= 2:
    #         var = get_var[1].strip()
    #         key = get_var[0].strip()
    #         dic[key] = var
    # f.write(str(dic))

    # conn.execute("insert into sen_var values('%s','%s','%s')" % ("tcas583","2121212W",val))
    # conn.execute("delete from sen_var")
    # conn.commit()

    # result = conn.execute("select sen_var from sen_var")
    # for record in result:
    #     senvar = eval(record[0])
    #     # val = str(senvar).replace("''", "'")
    #     f.write(str(senvar))
    #     for key in senvar:
    #         f.write(key)

    # conn.execute("create table if not exists bp_vars(lineNum integer,break_var TEXT)")
    # conn.commit()

    # a=  conn.execute("SELECT val FROM bp_tc WHERE bp_id=%d AND tc_name='%s' ORDER BY id DESC LIMIT 1"%(1,"tcas235"))
    #设置GDB对象
    # gdb = gdb_vars_get.StateGDB(debuggee)
    # read = open(debuggee+".c")
    # line = read.readline()
    # linenumber = 1
    # while line:
    #     if 0 < line.find("return") or 0 < line.find("exit("):
    #         # linenumber行处有return或exit，加断点
    #         output = gdb.question("b " + '%d' % linenumber)
    #     line = read.readline()
    #     linenumber += 1
    # read.close
    # if not os.path.exists(path):
    #     os.mknod(path)
    # f = open(path,"a")
    # f.write(str(a))
    #f.write(output)
    # gdb.question("b 148")

    # gdb.insertBreakpoints(lineNum)
    # output = gdb.question("info var")
    # f.write(output)
    # out = gdb.getBreakVars("")
    # out = gdb.question("run "+data[1])


    # output = gdb.question("info var")
    # temp = output.split("Non-debugging symbols")
    # temp1 = temp[0]
    # temp2 = temp1.split(";")
    # g_var=[]
    # for temp3 in temp2:
    #     temp4 = temp3.split()
    #     f.write(str(type(temp4)))
    #     len_4 = len(temp4)
    #     if len_4>=2:
    #         g_var.append(temp4[len_4-1])
    # for get_g_var in g_var:
    #     f.write("\n")
    #     f.write(str(type(get_g_var)))
    #     f.write("\n")
    #     conn.execute("insert into bp_vars values('%d','%s')"%(-1,get_g_var))
    # conn.commit()
    # f.write(str(g_var))
    #
    # f.write(output)
    # f.write("######################\n")
    # out = gdb.getBreakVars("")
    # f.write(str(out))
    # s = out
    # s2 = s[12:s.find(",", 12)]
    # f.write("######################\n")
    # loc = gdb.question("i locals")
    # # arg = gdb.question("i args")
    # p = gdb.question("display enabled")
    # f.write(loc)
    # f.write(str(isinstance(loc,str)))
    # # f.write(arg)
    # # f.write(p)
    # state = gdb.state()
    # f.write("######################\n")
    # f.write(str(state))
    # f.write("######################\n")
    # f.write(str(storeVars(1)))
    # while out.find("\nBreakpoint ") == 0:
    #     # 运行到了断点处
    #
    #     # 断点处的值
    #     state = gdb.state()

        # 得到断点处的行数，用在数据库中断点ID处
    # pname = "tcas"
    # i=1
    # tc_name = pname+str(i+1)
    # select_result = conn.execute("select pass from testcase where name='%s'"%tc_name )
    # result = select_result.fetchone()
    # if result[0]:
    #     f.write("T:"+str(result[0]))
    # else:
    #     f.write("F:"+str(result[0]))
    # conn_count = conn.execute("select count(name) from testcase")
    # count = conn_count.fetchone()[0]
    # f.write("count : "+str(count))
    # line_single = conn.execute("select val from bp_tc where lineNum='%d' and tc_name='%s' " % (100000, tc_name))
    # f.write("\n length : "+str(len(line_single.fetchall())))
    f.close()





