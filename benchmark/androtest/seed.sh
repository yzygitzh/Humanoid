root_path=/mnt/FAST_volume/lab_data/AndroTest/
humanoid_server=162.105.87.84:47927
out_num=1

rm -rf $root_path/out$out_num/$1
mkdir -p $root_path/out$out_num/$1

$ANDROID_HOME/tools/emulator -avd androtest_$2 -ports $3,$4 -wipe-data &
sleep 60

# DROIDBOT
timeout 3600s droidbot -d emulator-$3 -a $root_path/apps/$1.apk -interval 3 -count 2000 -policy dfs_greedy -grant_perm -keep_env -random -is_emulator -humanoid $humanoid_server -o $root_path/out$out_num/$1/droidbot_out &> $root_path/out$out_num/$1/droidbot.log &

droidbot_pid=$!
ec_count=1

while kill -0 "$droidbot_pid" > /dev/null 2>&1; do
    sleep 60
    adb -s emulator-$3 shell am broadcast -a edu.gatech.m3.emma.COLLECT_COVERAGE
    adb -s emulator-$3 pull /sdcard/coverage.ec $root_path/out$out_num/$1/coverage.ec.$ec_count
    let ec_count++
done

adb -s emulator-$3 pull /mnt/sdcard/coverage.ec $root_path/out$out_num/$1/coverage.ec
adb -s emulator-$3 shell reboot -p
