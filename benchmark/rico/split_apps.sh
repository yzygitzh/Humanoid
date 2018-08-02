rm -rf run
mkdir -p run

head -n  10 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4444 10000"}' > run/cluster01_androtest.sh
head -n  20 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4445 10001"}' > run/cluster02_androtest.sh
head -n  30 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4446 10002"}' > run/cluster03_androtest.sh
head -n  40 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4447 10003"}' > run/cluster04_androtest.sh
head -n  50 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4448 10004"}' > run/cluster05_androtest.sh
head -n  60 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4449 10005"}' > run/cluster06_androtest.sh
head -n  70 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4450 10006"}' > run/cluster07_androtest.sh
head -n  80 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4451 10007"}' > run/cluster08_androtest.sh
head -n  90 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4452 10008"}' > run/cluster09_androtest.sh
head -n 100 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4453 10009"}' > run/cluster10_androtest.sh
head -n 110 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4454 10010"}' > run/cluster11_androtest.sh
head -n 120 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4455 10011"}' > run/cluster12_androtest.sh
head -n 130 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4456 10012"}' > run/cluster13_androtest.sh
head -n 140 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4457 10013"}' > run/cluster14_androtest.sh
head -n 150 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4458 10014"}' > run/cluster15_androtest.sh
head -n 160 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4459 10015"}' > run/cluster16_androtest.sh
head -n 170 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4460 10016"}' > run/cluster17_androtest.sh
head -n 180 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4461 10017"}' > run/cluster18_androtest.sh
head -n 190 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4462 10018"}' > run/cluster19_androtest.sh
head -n 200 app_list.txt | tail -n 10 | awk '{print "bash seed.sh "$1" 4463 10019"}' > run/cluster20_androtest.sh
