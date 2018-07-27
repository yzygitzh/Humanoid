rm -rf run
mkdir -p run

head -n  10 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4444"}' > run/cluster01_androtest.sh
head -n  20 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4445"}' > run/cluster02_androtest.sh
head -n  30 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4446"}' > run/cluster03_androtest.sh
head -n  40 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4447"}' > run/cluster04_androtest.sh
head -n  50 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4448"}' > run/cluster05_androtest.sh
head -n  60 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4449"}' > run/cluster06_androtest.sh
head -n  70 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4450"}' > run/cluster07_androtest.sh
head -n  80 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4451"}' > run/cluster08_androtest.sh
head -n  90 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4452"}' > run/cluster09_androtest.sh
head -n 100 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4453"}' > run/cluster10_androtest.sh
head -n 110 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4454"}' > run/cluster11_androtest.sh
head -n 120 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4455"}' > run/cluster12_androtest.sh
head -n 130 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4456"}' > run/cluster13_androtest.sh
head -n 140 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4457"}' > run/cluster14_androtest.sh
head -n 150 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4458"}' > run/cluster15_androtest.sh
head -n 160 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4459"}' > run/cluster16_androtest.sh
head -n 170 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4460"}' > run/cluster17_androtest.sh
head -n 180 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4461"}' > run/cluster18_androtest.sh
head -n 190 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4462"}' > run/cluster19_androtest.sh
head -n 200 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4463"}' > run/cluster20_androtest.sh
