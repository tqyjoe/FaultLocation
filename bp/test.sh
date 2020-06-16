cwd=`pwd`

path="$cwd/a"
pName="tcas"
path1="$cwd/datasource"
path2="$cwd/trainset"
path3="$cwd/dataset"

python3 Test.py ${pName} ${path} ${path1} ${path2} ${path3} > /dev/null