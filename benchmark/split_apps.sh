head -n 40 app_list.txt > cluster1_app_list.txt
cp cluster1_app_list.txt cluster1_droidbot.sh
head -n 80 app_list.txt | tail -n 40 > cluster2_app_list.txt
cp cluster2_app_list.txt cluster2_droidbot.sh
head -n 160 app_list.txt | tail -n 80 > cluster3_app_list.txt
cp cluster3_app_list.txt cluster3_droidbot.sh
tail -n 40 app_list.txt > cluster4_app_list.txt
cp cluster4_app_list.txt cluster4_droidbot.sh
