import pandas as pd
import sys
import os
def getBreakpoint(csvPath,version,recordPath):
   df = pd.read_csv(csvPath)
   # df = df.iloc[:,['program title']]
   df_need = df[df["program title"]==version]
   list_data = df_need.values.tolist()
   list_data.sort(key=lambda ele:ele[26],reverse=True)
   breakpoints = []
   if not os.path.exists(recordPath):
      os.mknod(recordPath)
   f = open(recordPath, "w+")
   for count in range(int(len(list_data)*0.2)):
      if count!=0:
         f.write("\n")
      # print(list_data[count][1])
      breakpoints.append(list_data[count][1])
      f.write(str(list_data[count][1]))
   f.close()

if __name__ == '__main__':
   if len(sys.argv) != 4:
      print("Error. You should input 5 parameters." + str(len(sys.argv)))
      exit(1)
   path = sys.argv[1]
   version = sys.argv[2]
   recordPath = sys.argv[3]
   getBreakpoint(path,version,recordPath)