root_path=/mnt/FAST_volume/lab_data/AndroTest/
humanoid_server=162.105.87.84:55377

# out_tester=_humanoid
# out_tester=_monkey
# out_tester=_puma
# out_tester=_stoat
out_tester=_droidmate

# PUMA
# tested=`cat $root_path/out$out_tester/$1/puma.log | grep 'OK (1 test)'`
# OTHERS
tested=`ls $root_path/out$out_tester/$1/coverage.ec`

if [ -z "$tested" ]; then
    echo "TEST $1"
    rm -rf $root_path/out$out_tester/$1
    mkdir -p $root_path/out$out_tester/$1

    $ANDROID_HOME/tools/emulator -avd androtest_$2 -ports $3,$4 -wipe-data &
    sleep 60

    # DROIDBOT
    # timeout 3600s droidbot -d emulator-$3 -a $root_path/apps/$1.apk -interval 1 -count 600 -policy dfs_greedy -grant_perm -keep_env -random -is_emulator -humanoid $humanoid_server -o $root_path/out$out_tester/$1/droidbot_out &> $root_path/out$out_tester/$1/droidbot.log &

    # MONKEY
    # package_name=$(aapt dump badging $root_path/apps/$1.apk | grep 'package\: name' | awk -F"'" '{print $2}')
    # timeout 600s adb -s emulator-$3 install $root_path/apps/$1.apk
    # timeout 3600s adb -s emulator-$3 shell monkey -p $package_name --ignore-crashes --ignore-security-exceptions --ignore-timeouts --throttle 1000 -v 3000 &> $root_path/out$out_tester/$1/monkey.log &

    # PUMA
    # puma_root=/mnt/EXT_volume/projects_light/androtest/tools/PUMA
    # cd $puma_root
    # package_name=$(aapt dump badging $root_path/apps/$1.apk | grep 'package\: name' | awk -F"'" '{print $2}')
    # app_label=$(aapt dump badging $root_path/apps/$1.apk | grep 'launchable' | awk -F"'" '{print $4}')

    # if [ -z "$app_label" ]; then
    #     app_label=$(aapt dump badging $root_path/apps/$1.apk | grep 'application-label' | awk -F"'" '{print $2}' | tail -n1)
    # fi

    # echo $app_label
    # echo $package_name > app.info.emulator-$3
    # echo $app_label >> app.info.emulator-$3
    # adb -s emulator-$3 shell input tap 900 480 # skip welcome screen
    # timeout 600s adb -s emulator-$3 install $root_path/apps/$1.apk
    # ./setup-phone.sh emulator-$3
    # timeout 3600s ./run.sh emulator-$3 &> $root_path/out$out_tester/$1/puma.log &

    # STOAT
    # adb -s emulator-$3 shell settings put secure show_ime_with_hard_keyboard 0
    # stoat_root=/mnt/EXT_volume/projects_light/Stoat/Stoat/bin
    # cd $stoat_root
    # timeout 3600s ruby run_stoat_testing.rb --app_dir $root_path/apps/$1.apk --real_device_serial=emulator-$3 --stoat_port $5 --max_event 600 --event_delay 1000 --model_time 1200s --project_type apk &> $root_path/out$out_tester/$1/stoat.log &

    # DROIDMATE
    droidmate_root=/mnt/EXT_volume/projects_light/droidmate/project/pcComponents/API/build/libs
    cd $droidmate_root
    rm -rf ./apks_$3
    mkdir -p ./apks_$3
    cp $root_path/apps/$1.apk ./apks_$3/
    timeout 3600s java -jar shadow-1.0-RC4-all.jar -config defaultConfig.properties --Selectors-actionLimit=600 --Exploration-deviceIndex=$2 --Exploration-deviceSerialNumber=emulator-$3 --Exploration-apksDir=./apks_$3 --Strategies-fitnessProportionate=true --DeviceCommunication-deviceOperationDelay=1000 --Deploy-uninstallApk=false --UiAutomatorServer-basePort=20000 --ApiMonitorServer-basePort=30000 &> $root_path/out$out_tester/$1/droidmate.log &

    tester_pid=$!
    ec_count=1

    while kill -0 "$tester_pid" > /dev/null 2>&1; do
        sleep 60
        adb -s emulator-$3 shell am broadcast -a edu.gatech.m3.emma.COLLECT_COVERAGE
        adb -s emulator-$3 pull /sdcard/coverage.ec $root_path/out$out_tester/$1/coverage.ec.$ec_count
        let ec_count++
    done

    # STOAT
    # pids=`ps a | grep 'Server.jar' | grep $1 | awk '{print $1}'`
    # echo $pids
    # for pid in $pids; do kill -9 $pid; done

    adb -s emulator-$3 pull /mnt/sdcard/coverage.ec $root_path/out$out_tester/$1/coverage.ec
    adb -s emulator-$3 shell reboot -p

else
    echo "PASS $1"
fi
