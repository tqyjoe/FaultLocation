import numpy as np
from sklearn import preprocessing
from numpy import float64
from NeuralNetwork import NeuralNetwork
import data_process as dp
import sys
import os
import random
import operator
import sqlite3
import pickle

#第一个数字表示输入层的神经元个数为2
#第二个数字表示隐藏层的神经元个数为2
#第三个数字表示输出层的神经元个数为1
#"tanh"表示选择的激活函数
# nn = NeuralNetwork([2, 2, 1], 'tanh')
#
# temp = [[0, 0], [0, 1], [1, 0], [1, 1]]
# X = np.array(temp)
# y = np.array([0, 1, 1, 0])
# nn.fit(X, y)
# for i in temp:
#     print(i, nn.predict(i))


def loadDataSet(all_data,all_result): #读取数据
    dataMat1 = all_data
    labelMat1 = all_result
    # for data in all_data:
    #     dataMat1.append([lineArr[0], lineArr[1], lineArr[2], lineArr[3]])
    #     labelMat1.append(lineArr[4])
    dataMat = np.array(dataMat1, dtype=float64)
    # removeLocList = []
    # for i in range(dataMat):
    #     data = dataMat[i]
    #     for d in data:
    #         if np.isnan(d):
    #             removeLocList.append(i)
    #             break
    #         if not np.isfinite(d).all():
    #             removeLocList.append(i)
    #             break
    labelMat = np.array(labelMat1, dtype=float64)

    # count = 0
    # for loc in removeLocList:
    #     np.delete(dataMat, loc - count, axis=0)
    #     np.delete(labelMat, loc - count, axis=0)
    #     count += 1

    min_max_scaler = preprocessing.MinMaxScaler(feature_range=(-1,1))
    X_train_minmax = min_max_scaler.fit_transform(dataMat)
    print(X_train_minmax)
    return X_train_minmax, labelMat#,removeLocList #返回数据特征和数据类别
    # return dataMat, labelMat
def getResult(train_data_file,apath):
    if not os.path.exists(apath):
        os.mknod(apath)
    f = open(apath,"a")
    all_data,all_result,tc_names,all_false_tcas_loc,all_tcas_null_dic,dic_neu=dp.saveData(train_data_file)
    # f.write(str(all_data))
    X,y=loadDataSet(all_data,all_result)

    # removeNum = 0
    # for loc in removeLocList:
    #     del tc_names[loc - removeNum]
    #     removeNum+=1
    #
    #

    # f.write(str(X))
    for tc_loc in all_tcas_null_dic:
        for null_loc in all_tcas_null_dic[tc_loc]:
            X[tc_loc][null_loc] = 0

    conn = sqlite3.connect(train_data_file)
    conn.execute("create table if not exists bp_input(tc_name TEXT,input_data TEXT, result INTEGER )")
    conn.execute("create table if not exists bp_neu(dic_neu TEXT)")
    dic_neu_str = str(dic_neu).replace("'", "''")
    conn.execute("insert into bp_neu values('%s')"%(dic_neu_str))
    conn.commit()

    for count in range(len(X)):
        tc_name = tc_names[count]
        input = X[count].tolist()
        result = y[count]
        conn.execute("insert into bp_input values ('%s','%s','%d')" % (tc_name,str(input),result))
    conn.commit()
    conn.close()


    nn = NeuralNetwork([len(all_data[0]),len(all_data[0])//2,1],'tanh')

    # f.write(str(X))
    # X,y = deRepeat(X,all_false_tcas_loc,y,f)
    X2=[]
    X1=[]
    y1=[]
    y2=[]
    count = 0
    for value in X:
        if random.randint(0,9)>=2:
            X2.append(value)
            y2.append(y[count])
        else:
            X1.append(value)
            y1.append(y[count])
        count+=1
    nn.fit(X2,y2)
    # all_data1, all_result1,tc_names1 = dp.saveData(test_data_file, False)
    # X1,y1=loadDataSet(all_data1,all_result1)
    k=0
    s=0
    fail=0
    acess = 0
    r_fail=0
    r_acess=0
    for i in X1:
        result = nn.predict(i)
        if y1[k]==1:
            fail+=1
        if y1[k]==-1:
            acess+=1
        if result>0 and y1[k]==1:
            r_fail+=1
            s+=1
        if result<0 and y1[k]==-1:
            r_acess+=1
            s+=1
        k+=1
    f.write("错误/正确="+str(fail/acess)+"\n")
    f.write("错误预测准确率："+str(r_fail/fail)+"\n")
    f.write("正确预测准确率："+str(r_acess/acess)+"\n")
    f.write("预测准确率："+str(s/k)+"\n")
    f.close()

def getFaultLocation(data_file,path,savePath):
    all_data, all_result, tc_names, all_false_tcas_loc = getData(data_file)
    # f.write(str(all_data))
    X, y = loadDataSet(all_data, all_result)
    dic_neu = getNeu(data_file)
    # all_data, all_result, tc_names, all_false_tcas_loc, all_tcas_null_dic, dic_neu = dp.saveData(data_file)
    # # f.write(str(all_data))
    # X, y = loadDataSet(all_data, all_result)

    # # f.write(str(X))
    # for tc_loc in all_tcas_null_dic:
    #     for null_loc in all_tcas_null_dic[tc_loc]:
    #         X[tc_loc][null_loc] = 0

    conn = sqlite3.connect(data_file)
    # conn.execute("create table if not exists bp_input(tc_name TEXT,input_data TEXT, result INTEGER )")
    # conn.execute("create table if not exists bp_neu(dic_neu TEXT)")
    # conn.execute("create table if not exists bp_method_var_weight(break_var_line TEXT,tc_name TEXT,method TEXT,fault_weight TEXT )")
    # conn.execute(
    #     "create table if not exists bp_tc_var_weight(break_var_line TEXT,tc_name TEXT, fault_weight TEXT)")
    # conn.commit()
    query = conn.execute("select * from bp_neu")
    if not len(query.fetchall()):
        dic_neu_str = str(dic_neu).replace("'", "''")
        conn.execute("insert into bp_neu values('%s')" % (dic_neu_str))
        conn.commit()
    query = conn.execute("select * from bp_input")
    if not len(query.fetchall()):
        for count in range(len(X)):
            tc_name = tc_names[count]
            input = X[count].tolist()
            result = y[count]
            conn.execute("insert into bp_input values ('%s','%s','%d')" % (tc_name, str(input), result))
        conn.commit()

    nn = NeuralNetwork([len(all_data[0]), len(all_data[0]) // 2, 1], 'tanh')
    nn.fit(X, y)


    saveModelPath = savePath+".pkl"
    if not os.path.exists(saveModelPath):
        os.mknod(saveModelPath)
    else:
        saveModelPath = savePath + "(1).pkl"
        os.mknod(saveModelPath)
    saveModelFile = open(saveModelPath, 'wb')
    s = pickle.dump(nn,saveModelFile)
    saveModelFile.close()

    if not os.path.exists(path):
        os.mknod(path)
    f = open(path, "a")
    # f.write(str(X))
    X1=[]
    y1=[]
    fault_names = []
    for loc in all_false_tcas_loc:
        y1.append(y[loc])
        X1.append(X[loc])
        fault_names.append(tc_names[loc])
    vir_data_tcs={}
    dic_vars_linenum_tc={}

    k = 0
    fail = 0
    r_fail = 0
    for i in X1:
        result = nn.predict(i)
        if y1[k] == 1:
            fail += 1
        if result > 0 and y1[k] == 1:
            r_fail += 1
        k += 1
    if fail !=0:
        f.write("错误占比："+str(fail/len(X))+"\n")
        f.write("错误预测准确率：" + str(r_fail / fail) + "\n")
    else:
        f.write("no error\n")



    count = 0
    for f_data in X1:
        vir_var_method_datas = dp.getVirMethodData(f_data, dic_neu, conn)
        vir_data_tcs[fault_names[count]] = vir_var_method_datas
        count += 1

    # conn.execute(
    #     "create table if not exists bp_method_var_weight(break_var_line TEXT,tc_name TEXT, method TEXT, fault_weight integer)")
    # conn.commit()
    tc_name_pre = {}
    for tc_name in vir_data_tcs:
        tc_vir_data = vir_data_tcs[tc_name]
        var_fault_pre = {}
        for var_name in tc_vir_data:
            method_vir_data = tc_vir_data[var_name]
            for method in method_vir_data:
                vir_var_data = method_vir_data[method]
                result_var = nn.predict(vir_var_data)
                var_fault_pre[var_name] = result_var
                if result_var > 0:
                    # f.write(var_name + "-"+method+" : " + str(result_var) + "\n")
                    conn.execute("insert into bp_method_var_weight values('%s','%s','%s','%s')"%(var_name,tc_name,method,result_var))
                    conn.commit()
        tc_name_pre[tc_name] = var_fault_pre

    # dic_neu = dp.getInputNeurons(data_file)
    vir_data_tcs1={}
    count=0
    for f_data in X1:
        vir_data, dic_vars_linenum,dic_vars_loc=dp.getVirData(f_data,dic_neu,data_file)
        vir_data_tcs1[fault_names[count]]=vir_data
        dic_vars_linenum_tc[fault_names[count]]=dic_vars_linenum
        count+=1

    # conn.execute(
    #     "create table if not exists bp_tc_var_weight(break_var_line TEXT,tc_name TEXT, fault_weight TEXT)")
    # conn.commit()
    tc_name_pre1={}
    for tc_name in vir_data_tcs1:
        tc_vir_data = vir_data_tcs1[tc_name]
        var_fault_pre = {}
        for var_name in tc_vir_data:
            vir_var_data = tc_vir_data[var_name]
            result_var = nn.predict(vir_var_data)
            var_fault_pre[var_name] = result_var
            if result_var>0:
                # f.write(var_name + " : "+str(result_var)+"\n")
                conn.execute("insert into bp_tc_var_weight values('%s','%s','%s')"%(var_name,tc_name,result_var))
                conn.commit()
        tc_name_pre1[tc_name]=var_fault_pre

    # vir_all_line_datas = dp.getVirLineDataOne(vir_data_tcs,dic_vars_loc)
    # conn.execute(
    #     "create table if not exists bp_line_var_weight(lineNum integer,break_var_line TEXT,tc_name TEXT, fault_weight integer)")
    # conn.commit()
    # for tc_name in vir_all_line_datas:
    #     tc_vir_data = vir_all_line_datas[tc_name]
    #     for var in tc_vir_data:
    #         var_vir_data = tc_vir_data[var]
    #         for loc in var_vir_data:
    #             data = var_vir_data[loc]
    #             result_loc = nn.predict(data)
    #             # change_result = tc_name_pre[tc_name][var]-result_loc
    #             linenum = dp.getLinumByLoc(dic_vars_linenum,dic_vars_loc,var,loc)
    #             f.write(str(var) + "  "+ str(linenum)+"   "+str(result_loc)+"\n")
    #             if result_loc>0:
    #                 f.write(str(var) + "  "+ str(linenum)+"   "+str(result_loc)+"\n")
    #                 # conn.execute("insert into bp_line_var_weight values('%d','%s','%s','%d')"%(linenum,var,tc_name,result_loc))
    #                 # conn.commit()
    f.close()
    conn.close()

def deRepeat(data_list,false_loc_list,result_list):
    repeat_list = []
    de_data_list = data_list.tolist()
    de_result_list = result_list.tolist()
    for false_loc in false_loc_list:
        count = 0
        for data in de_data_list:
            if count not in false_loc_list:
                if operator.eq(data,de_data_list[false_loc]):
                    if count not in repeat_list:
                        repeat_list.append(count)
            count+=1
    sum = 0
    for repeat_loc in repeat_list:
        de_data_list.pop(repeat_loc-sum)
        de_result_list.pop(repeat_loc-sum)
        sum+=1
    return np.array(de_data_list, dtype=float64),np.array(de_result_list, dtype=float64)


def getData(data_file):
    conn = sqlite3.connect(data_file)
    query = conn.execute("select * from bp_input")
    all_data = []
    all_result = []
    tc_names = []
    all_false_tcas_loc = []
    query_results = query.fetchall()
    loc = 0
    for query_result in query_results:
        tc_names.append(query_result[0])
        all_result.append(query_result[2])
        if query_result[2] == 1:
            all_false_tcas_loc.append(loc)
        list = eval(query_result[1])
        all_data.append(list)
        loc+=1
    return all_data,all_result,tc_names,all_false_tcas_loc

def getNeu(data_file):
    conn = sqlite3.connect(data_file)
    query = conn.execute("select * from bp_neu")
    result = query.fetchone()
    dic_neu = eval(result[0])
    return dic_neu

def addFaultProportion(data_file,path,savePath):
    all_data, all_result, tc_names, all_false_tcas_loc = getData(data_file)
    # f.write(str(all_data))
    X, y = loadDataSet(all_data, all_result)

    X1 = []
    y1 = []
    fault_names = []
    num = 0
    for loc in all_false_tcas_loc:
        y1.append(y[loc-num])
        X1.append(X[loc-num])
        np.delete(X,loc-num,axis=0)
        np.delete(y, loc - num, axis=0)
        fault_names.append(tc_names[loc-num])
        del tc_names[loc-num]
        num+=1

    cycle_num = 1
    if len(X1)>=4:
        mul = len(X)/len(X1)
        if mul>19:
            cycle_num = int(0.1*int(mul))

    trainX = []
    trainY = []
    testX = []
    testY = []
    count = 0
    for value in X:
        if random.randint(0, 9) > 4:
            trainX.append(value)
            trainY.append(y[count])
        else:
            testX.append(value)
            testY.append(y[count])
        count += 1

    listTest = []
    if len(X1)/len(all_data)<0.5 and len(X1)>=4:
        while True:
            rand = random.randint(0, len(X1))
            if rand not in listTest:
                listTest.append(rand)
            if len(listTest)==int(len(X1)*0.4):
                break
        for i in range(len(X1)):
            if i in listTest:
                for k in range(cycle_num):
                    insertLoc = random.randint(0,len(testX))
                    testX.insert(insertLoc,X1[i])
                    testY.insert(insertLoc,y1[i])
            else:
                for k in range(cycle_num):
                    insertLoc = random.randint(0,len(trainX))
                    trainX.insert(insertLoc,X1[i])
                    trainY.insert(insertLoc, y1[i])


        nn = NeuralNetwork([len(all_data[0]), len(all_data[0]) // 2, 1], 'tanh')
        nn.fit(trainX, trainY)

        if not os.path.exists(path):
            os.mknod(path)
        f = open(path, "a")

        fail = 0
        r_fail=0
        k=0
        for i in testX:
            result = nn.predict(i)
            if testY[k] == 1:
                fail += 1
            if result > 0 and testY[k] == 1:
                r_fail += 1
            k += 1
        sum = len(trainY)+len(testY)
        fail_sum = len(X1)*cycle_num
        if fail !=0:
            f.write("随机过采样:\n")
            f.write("错误占比："+str(fail_sum/sum)+"\n")
            f.write("错误预测准确率：" + str(r_fail / fail) + "\n")
        else:
            f.write("no error\n")

def createDB(data_file):
    conn = sqlite3.connect(data_file)
    conn.execute("create table if not exists bp_input(tc_name TEXT,input_data TEXT, result INTEGER )")
    conn.execute("create table if not exists bp_neu(dic_neu TEXT)")
    conn.execute("create table if not exists bp_method_var_weight(break_var_line TEXT,tc_name TEXT,method TEXT,fault_weight TEXT )")
    conn.execute(
        "create table if not exists bp_tc_var_weight(break_var_line TEXT,tc_name TEXT, fault_weight TEXT)")
    conn.commit()

def getFaultLocationByProportion(data_file,path,savePath):
    all_data, all_result, tc_names, all_false_tcas_loc = getData(data_file)
    X, y = loadDataSet(all_data, all_result)
    dic_neu = getNeu(data_file)

    X1 = []
    y1 = []
    fault_names = []
    for loc in all_false_tcas_loc:
        y1.append(y[loc])
        X1.append(X[loc])
        fault_names.append(tc_names[loc])
    vir_data_tcs = {}
    dic_vars_linenum_tc = {}

    conn = sqlite3.connect(data_file)
    conn.execute("delete from bp_method_var_weight")
    conn.execute("delete from bp_tc_var_weight")
    conn.commit()
    # query = conn.execute("select * from bp_neu")
    # if not len(query.fetchall()):
    #     dic_neu_str = str(dic_neu).replace("'", "''")
    #     conn.execute("insert into bp_neu values('%s')" % (dic_neu_str))
    #     conn.commit()
    # query = conn.execute("select * from bp_input")
    # if not len(query.fetchall()):
    #     for count in range(len(X)):
    #         tc_name = tc_names[count]
    #         input = X[count].tolist()
    #         result = y[count]
    #         conn.execute("insert into bp_input values ('%s','%s','%d')" % (tc_name, str(input), result))
    #     conn.commit()
    cycle_num=1
    if len(X1)/len(X)<0.05 and len(X1)!=0:
        X1_1 = []
        y1_1 = []
        num = 0
        for loc in all_false_tcas_loc:
            y1_1.append(y[loc - num])
            X1_1.append(X[loc - num])
            np.delete(X, loc - num, axis=0)
            np.delete(y, loc - num, axis=0)
            del tc_names[loc - num]
            num += 1


        mul = len(X) / len(X1_1)
        cycle_num = int(0.1 * int(mul))

        trainX = []
        trainY = []
        count = 0
        for value in X:
            trainX.append(value)
            trainY.append(y[count])
            count += 1
        for k in range(cycle_num):
            for i in range(len(X1_1)):
                insertLoc = random.randint(0, len(trainX))
                trainX.insert(insertLoc, X1_1[i])
                trainY.insert(insertLoc, y1_1[i])
        X = trainX
        y = trainY


    nn = NeuralNetwork([len(all_data[0]), len(all_data[0]) // 2, 1], 'tanh')
    nn.fit(X, y)


    saveModelPath = savePath+".pkl"
    if not os.path.exists(saveModelPath):
        os.mknod(saveModelPath)
    else:
        saveModelPath = savePath + "(1).pkl"
        os.mknod(saveModelPath)
    saveModelFile = open(saveModelPath, 'wb')
    s = pickle.dump(nn,saveModelFile)
    saveModelFile.close()

    if not os.path.exists(path):
        os.mknod(path)
    f = open(path, "a")
    # f.write(str(X))
    # X1=[]
    # y1=[]
    # fault_names = []
    # for loc in all_false_tcas_loc:
    #     y1.append(y[loc])
    #     X1.append(X[loc])
    #     fault_names.append(tc_names[loc])
    # vir_data_tcs={}
    # dic_vars_linenum_tc={}

    k = 0
    fail = 0
    r_fail = 0
    for i in X1:
        result = nn.predict(i)
        if y1[k] == 1:
            fail += 1
        if result > 0 and y1[k] == 1:
            r_fail += 1
        k += 1
    if fail !=0:
        f.write("随机过采样:\n")
        f.write("错误占比："+str(len(X1)*cycle_num/len(X))+"\n")
        f.write("错误预测准确率：" + str(r_fail / fail) + "\n")
    else:
        f.write("no error\n")



    count = 0
    for f_data in X1:
        vir_var_method_datas = dp.getVirMethodData(f_data, dic_neu, conn)
        vir_data_tcs[fault_names[count]] = vir_var_method_datas
        count += 1

    tc_name_pre = {}
    for tc_name in vir_data_tcs:
        tc_vir_data = vir_data_tcs[tc_name]
        var_fault_pre = {}
        for var_name in tc_vir_data:
            method_vir_data = tc_vir_data[var_name]
            for method in method_vir_data:
                vir_var_data = method_vir_data[method]
                result_var = nn.predict(vir_var_data)
                var_fault_pre[var_name] = result_var
                if result_var > 0:
                    # f.write(var_name + "-"+method+" : " + str(result_var) + "\n")
                    conn.execute("insert into bp_method_var_weight values('%s','%s','%s','%s')"%(var_name,tc_name,method,result_var))
                    conn.commit()
        tc_name_pre[tc_name] = var_fault_pre

    # dic_neu = dp.getInputNeurons(data_file)
    vir_data_tcs1={}
    count=0
    for f_data in X1:
        vir_data, dic_vars_linenum,dic_vars_loc=dp.getVirData(f_data,dic_neu,data_file)
        vir_data_tcs1[fault_names[count]]=vir_data
        dic_vars_linenum_tc[fault_names[count]]=dic_vars_linenum
        count+=1

    tc_name_pre1={}
    for tc_name in vir_data_tcs1:
        tc_vir_data = vir_data_tcs1[tc_name]
        var_fault_pre = {}
        for var_name in tc_vir_data:
            vir_var_data = tc_vir_data[var_name]
            result_var = nn.predict(vir_var_data)
            var_fault_pre[var_name] = result_var
            if result_var>0:
                # f.write(var_name + " : "+str(result_var)+"\n")
                conn.execute("insert into bp_tc_var_weight values('%s','%s','%s')"%(var_name,tc_name,result_var))
                conn.commit()
        tc_name_pre1[tc_name]=var_fault_pre

    f.close()
    conn.close()

def saveData(train_data_file):

	all_data, all_result, tc_names, all_false_tcas_loc, all_tcas_null_dic, dic_neu = dp.saveData(train_data_file)
	X, y = loadDataSet(all_data, all_result)

	for tc_loc in all_tcas_null_dic:
		for null_loc in all_tcas_null_dic[tc_loc]:
			X[tc_loc][null_loc] = 0

	conn = sqlite3.connect(train_data_file)
	conn.execute("create table if not exists bp_input(tc_name TEXT,input_data TEXT, result INTEGER )")
	conn.execute("create table if not exists bp_neu(dic_neu TEXT)")
	dic_neu_str = str(dic_neu).replace("'", "''")
	conn.execute("insert into bp_neu values('%s')" % (dic_neu_str))
	conn.commit()

	for count in range(len(X)):
		tc_name = tc_names[count]
		input = X[count].tolist()
		result = y[count]
		conn.execute("insert into bp_input values ('%s','%s','%d')" % (tc_name, str(input), result))
	conn.commit()
	conn.close()


if __name__ == '__main__':
    data_file = sys.argv[1]
    pname = sys.argv[2]
    path = sys.argv[3]
    savePath = sys.argv[4]
    # getResult(data_file,path)
    # getFaultLocation(data_file,path,savePath)
    createDB(data_file)
    # addFaultProportion(data_file,path,savePath)
    # getFaultLocationByProportion(data_file,path,savePath)

