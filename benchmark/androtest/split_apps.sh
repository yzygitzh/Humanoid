rm -rf run
mkdir -p run

head -n 23 app_list.txt | awk '{print "bash seed.sh "$1" 01 5554 5555 10000"}' > run/cluster1_androtest.sh
head -n 46 app_list.txt | tail -n 23 | awk '{print "bash seed.sh "$1" 02 5556 5557 10001"}' > run/cluster2_androtest.sh
tail -n 23 app_list.txt | awk '{print "bash seed.sh "$1" 03 5558 5559 10002"}' > run/cluster3_androtest.sh
