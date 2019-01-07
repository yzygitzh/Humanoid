rm -rf run
mkdir -p run

head -n  17 app_list.txt | tail -n 17 | awk '{print "bash seed_sapienz.sh "$1" 01 4444"}' > run/cluster01_androtest.sh
head -n  34 app_list.txt | tail -n 17 | awk '{print "bash seed_sapienz.sh "$1" 02 4446"}' > run/cluster02_androtest.sh
head -n  51 app_list.txt | tail -n 17 | awk '{print "bash seed_sapienz.sh "$1" 03 4448"}' > run/cluster03_androtest.sh
head -n  68 app_list.txt | tail -n 17 | awk '{print "bash seed_sapienz.sh "$1" 01 4450"}' > run/cluster04_androtest.sh
head -n  85 app_list.txt | tail -n 17 | awk '{print "bash seed_sapienz.sh "$1" 02 4452"}' > run/cluster05_androtest.sh
head -n 102 app_list.txt | tail -n 17 | awk '{print "bash seed_sapienz.sh "$1" 03 4454"}' > run/cluster06_androtest.sh
head -n 119 app_list.txt | tail -n 17 | awk '{print "bash seed_sapienz.sh "$1" 01 4456"}' > run/cluster07_androtest.sh
head -n 136 app_list.txt | tail -n 17 | awk '{print "bash seed_sapienz.sh "$1" 02 4458"}' > run/cluster08_androtest.sh
head -n 152 app_list.txt | tail -n 16 | awk '{print "bash seed_sapienz.sh "$1" 03 4460"}' > run/cluster09_androtest.sh
head -n 168 app_list.txt | tail -n 16 | awk '{print "bash seed_sapienz.sh "$1" 01 4462"}' > run/cluster10_androtest.sh
head -n 184 app_list.txt | tail -n 16 | awk '{print "bash seed_sapienz.sh "$1" 02 4464"}' > run/cluster11_androtest.sh
head -n 200 app_list.txt | tail -n 16 | awk '{print "bash seed_sapienz.sh "$1" 03 4466"}' > run/cluster12_androtest.sh
