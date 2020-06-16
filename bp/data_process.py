import sqlite3
import re

def getInputNeurons(dbfile):
    conn = sqlite3.connect(dbfile)
    line_result = conn.execute("select lineNum from bp_line_var group by lineNum")
    lineNums = line_result.fetchall()
    dic = {}
    for lineNum in lineNums:
        var_result = conn.execute("select break_var_line from bp_line_var where lineNum = '%d'"%lineNum[0])
        vars = var_result.fetchall()
        var_list = []
        for var in vars:
            # if var[0] != 'Positive_RA_Alt_Thresh':
            var_list.append(var[0])
            # f.write(str(lineNum[0])+" : "+var[0]+"\n")
        dic[lineNum[0]] = var_list
    conn.close()
    return dic

def getInputDataOftc_name(dbfile,dic_neu,tc_name):
    conn = sqlite3.connect(dbfile)
    dic = {}
    path = "/home/sr/program/20190531/FaultLocation/bp/a"
    f = open(path,"a")
    f.write(tc_name+"\n")
    for linenum in dic_neu:
        f.write("   "+str(linenum)+"\n")
        line_single = conn.execute("select val from bp_tc where lineNum='%d' and tc_name='%s' "%(linenum,tc_name))
        line_vars = line_single.fetchall()
        if len(line_vars)>0:
            vars = line_vars[len(line_vars)-1]
            dic_vars = eval(vars[0])
            varList = dic_neu[linenum]
            value = []
            for var in varList:
               value.append(dic_vars[var])
            dic[linenum] = value
    f.close()
    conn.close()
    return dic

def getInputData(dbfile,dic_neu):
    dic={}
    conn = sqlite3.connect(dbfile)
    conn_names = conn.execute("select name from testcase")
    tc_names = conn_names.fetchall()
    for tc_name in tc_names:
        dic_tc = getInputDataOftc_name(dbfile,dic_neu,tc_name[0])
        dic[tc_name[0]] = dic_tc
    return  dic

def saveData(datafile):
    dic_neu = getInputNeurons(datafile)
    # f.write(str(dic_neu))
    conn = sqlite3.connect(datafile)
    conn_count = conn.execute("select count(name) from testcase")
    count = conn_count.fetchone()[0]
    if count>0:
        dic_data = getInputData(datafile, dic_neu)
    # f.write(str(dic_data))
    all_data=[]
    all_result=[]
    all_name=[]
    all_false_tcas_loc = []
    all_tcas_null_dic = {}
    record_known_data_dic = {}
    zero_dic = {}
    for lineNum in dic_neu:
        known_data = []
        record_known_data_dic[lineNum] = known_data

    # print("\r -------- tcas'%d' "%i)
    count=0
    for tc_name in dic_data:
        all_name.append(tc_name)
        dic = dic_data[tc_name]
        data =[]
        data_loc = 0
        # zero_list = []
        null_list = []
        for lineNum in dic_neu:
            known_data = record_known_data_dic[lineNum]
            if known_data:
                flag = True
            else:
                flag = False
            if lineNum not in dic:
                # for k in dic_neu[lineNum]:
                #     data.append(0)
                if flag:
                    data_1 = record_known_data_dic[lineNum].copy()
                    data.extend(data_1)
                    for i in data_1:
                        null_list.append(data_loc)
                        data_loc+=1
                else:
                    zero_list = []
                    for k in dic_neu[lineNum]:
                        data.append(0)
                        zero_list.append(data_loc)
                        null_list.append(data_loc)
                        data_loc += 1
                    if count not in zero_dic:
                        zero_dic[count] = zero_list
                    else:
                        zero_dic[count].extend(zero_list)
            else:
                line_data = dic[lineNum]
                for value in line_data:
                    try:
                        v = float(value)
                        data.append(v)
                        data_loc += 1
                        if not flag:
                            known_data.append(v)
                    except ValueError:
                        cur_val = 'True'
                        if cur_val==value:
                            data.append(1)
                            if not flag:
                                known_data.append(1)
                        elif value == 'False':
                            data.append(-1)
                            if not flag:
                                known_data.append(-1)
                        else:
                            ch_loc = 1
                            sum = 0
                            for ch in value:
                                sum += ord(ch)*ch_loc*0.11
                            data.append(sum)
                            if not flag:
                                known_data.append(sum)
                        data_loc += 1
        all_data.append(data)
        select_result = conn.execute("select pass from testcase where name='%s'"%tc_name)
        result = select_result.fetchone()
        if result[0]:
            all_result.append(-1)
        else:
            all_result.append(1)
            all_false_tcas_loc.append(count)
        all_tcas_null_dic[count] = null_list
        count += 1
    for tc_name_loc in zero_dic:
        zero_data = zero_dic[tc_name_loc]
        for zero_loc in zero_data:
            all_data[tc_name_loc][zero_loc] = all_data[len(all_data)-1][zero_loc]
    return all_data,all_result,all_name,all_false_tcas_loc, all_tcas_null_dic,dic_neu

def getVirData(false_data,dic_neu,dbfile):
    conn = sqlite3.connect(dbfile)
    conn_vars = conn.execute("select break_var_line from bp_line_var group by break_var_line")
    vars = conn_vars.fetchall()
    vir_datas={}
    dic_vars_linenum={}
    dic_vars_loc={}
    for var in vars:
        vir_data=[]
        var_linenum=[]
        var_loc=[]
        count = 0
        pattern = "#"+var[0]+"#"
        for lineNum in dic_neu:
            linevars = dic_neu[lineNum]
            for line_var in linevars:
                pattern_object = "#"+line_var
                match = re.search(pattern, pattern_object, re.M | re.DOTALL)
                if var[0] == line_var or match:
                    vir_data.append(false_data[count])
                    var_linenum.append(lineNum)
                    var_loc.append(count)
                else:
                    vir_data.append(0)
                count+=1
        vir_datas[var[0]] = vir_data
        dic_vars_linenum[var[0]] = var_linenum
        dic_vars_loc[var[0]]=var_loc
    # conn.close()

    return vir_datas,dic_vars_linenum,dic_vars_loc

# {var:{method:[data]}}
def getVirMethodData(false_data,dic_neu,conn):
    # conn = sqlite3.connect(dbfile)
    conn_vars = conn.execute("select break_var_line from bp_line_var group by break_var_line")
    vars = conn_vars.fetchall()
    vir_var_method_datas = {}
    dic_vars_linenum = {}
    for var in vars:
        var_linenum = []
        pattern = "#" + var[0] + "#"
        query_method = conn.execute("select method from bp_line_var where break_var_line='%s' group by method"%(var[0]))
        methods = query_method.fetchall()
        vir_method_data = {}
        for method in methods:
            vir_data = []
            query_linenum = conn.execute(
                "select lineNum from bp_line_var where method='%s' group by lineNum" % (method[0]))
            method_linenums = getListByQueryDB(query_linenum.fetchall())
            count = 0
            for lineNum in dic_neu:
                linevars = dic_neu[lineNum]
                for line_var in linevars:
                    pattern_object = "#" + line_var
                    match = re.search(pattern, pattern_object, re.M | re.DOTALL)
                    if var[0] == line_var or match:
                        if lineNum in method_linenums:
                            vir_data.append(false_data[count])
                            var_linenum.append(lineNum)
                        else:
                            vir_data.append(0)
                    else:
                        vir_data.append(0)
                    count += 1
            vir_method_data[method[0]] = vir_data
        vir_var_method_datas[var[0]] = vir_method_data
        dic_vars_linenum[var[0]] = var_linenum
    # conn.close()
    return vir_var_method_datas

def getListByQueryDB(query_results):
    list = []
    for result in query_results:
        list.append(result[0])
    return list

def getVirLineData(vir_datas_tcs,dic_vars_linenum,dic_vars_loc):
    vir_all_line_datas={}
    for tc_name in vir_datas_tcs:
        vir_line_datas = {}
        vir_all_var_data = vir_datas_tcs[tc_name]
        for var in vir_all_var_data:
            vir_var_data = vir_all_var_data[var]
            vir_line_data = {}
            count=0
            for loc in dic_vars_loc[var]:
                vir_data = []
                for value in vir_var_data:
                    if loc==count:
                        vir_data.append(0)
                    else:
                        vir_data.append(value)
                    count+=1
                vir_line_data[loc]=vir_data
            vir_line_datas[var] = vir_line_data
        vir_all_line_datas[tc_name] = vir_line_datas

    return vir_all_line_datas

def getLinumByLoc(dic_vars_linenum,dic_vars_loc,var,loc):
    var_loc = dic_vars_loc[var]
    var_lineum=dic_vars_linenum[var]
    count=0
    for loc_val in var_loc:
        if loc_val == loc:
            return  var_lineum[count]
        count+=1
    return 0

def getVirLineDataOne(vir_datas_tcs,dic_vars_loc):
    vir_all_line_datas={}
    for tc_name in vir_datas_tcs:
        vir_line_datas = {}
        vir_all_var_data = vir_datas_tcs[tc_name]
        for var in vir_all_var_data:
            vir_var_data = vir_all_var_data[var]
            vir_line_data = {}
            count=0
            for loc in dic_vars_loc[var]:
                vir_data = []
                for value in vir_var_data:
                    if loc==count:
                        vir_data.append(value)
                    else:
                        vir_data.append(0)
                    count+=1
                vir_line_data[loc]=vir_data
            vir_line_datas[var] = vir_line_data
        vir_all_line_datas[tc_name] = vir_line_datas

    return vir_all_line_datas

