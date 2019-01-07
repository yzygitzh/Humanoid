root_path=/home/yzy/humanoid/

out_tester=_sapienz

tested=`ls $root_path/out$out_tester/$1/finish_mark`

if [ -z "$tested" ]; then
    rm -rf $root_path/out$out_tester/$1
    mkdir -p $root_path/out$out_tester/$1

    $ANDROID_HOME/tools/emulator -avd androtest_$2 -port $3 -wipe-data -http-proxy http://192.168.1.6:8995 -no-window -writable-system -cores 4 &
    emulator_pid=$!

    sleep 60

    # Sapienz
    sapienz_root=/home/yzy/projects/sapienz/sapienz
    cd $sapienz_root
    timeout 10800s python main.py $root_path/apps/$1.apk emulator-$3 &> $root_path/out$out_tester/$1/sapienz.log &

    tester_pid=$!
    ec_count=1

    while kill -0 "$tester_pid" > /dev/null 2>&1; do
        sleep 1
        echo "$ec_count" >> $root_path/out$out_tester/$1/activity_coverage
        adb -s emulator-$3 shell dumpsys activity activities | grep 'Hist #' >> $root_path/out$out_tester/$1/activity_coverage
        let ec_count++
    done

    adb -s emulator-$3 shell dumpsys activity activities | grep 'Hist #' >> $root_path/out$out_tester/$1/finish_mark
    while kill -0 "$emulator_pid" > /dev/null 2>&1; do
        sleep 1
        kill -9 $emulator_pid
    done

else
    echo "PASS $1"
fi
