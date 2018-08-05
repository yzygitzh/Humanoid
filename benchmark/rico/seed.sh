root_path=/home/yzy/humanoid/
humanoid_server=162.105.87.118:60109

# out_tester=_humanoid
# out_tester=_monkey
# out_tester=_puma
# out_tester=_stoat
out_tester=_droidmate

# PUMA
# tested=`cat $root_path/out$out_tester/$1/puma.log | grep 'OK (1 test)'`
# OTHERS
tested=`ls $root_path/out$out_tester/$1/finish_mark`

if [ -z "$tested" ]; then
    rm -rf $root_path/out$out_tester/$1
    mkdir -p $root_path/out$out_tester/$1

    qemu-img create -f qcow2 $root_path/qemu/droidbot-6.0-r3.qcow2.$2 -o backing_file=$root_path/qemu/droidbot-6.0-r3.qcow2

    qemu-system-i386 -hda $root_path/qemu/droidbot-6.0-r3.qcow2.$2 -m 2048 -smp cpus=4 -enable-kvm -machine q35 -nographic -net nic,model=e1000 -net user,hostfwd=tcp::$2-:5555 &

    sleep 60
    adb connect localhost:$2

    # DROIDBOT
    # timeout 12000s droidbot -d localhost:$2 -a $root_path/apps/$1.apk -interval 1 -count 2000 -policy dfs_greedy -grant_perm -keep_env -keep_app -random -is_emulator -humanoid $humanoid_server -o $root_path/out$out_tester/$1/droidbot_out &> $root_path/out$out_tester/$1/droidbot.log &

    # MONKEY
    # package_name=$(aapt dump badging $root_path/apps/$1.apk | grep 'package\: name' | awk -F"'" '{print $2}')
    # timeout 600s adb -s localhost:$2 install $root_path/apps/$1.apk
    # timeout 12000s adb -s localhost:$2 shell monkey -p $package_name --ignore-crashes --ignore-security-exceptions --ignore-timeouts --throttle 1000 -v 10000 &> $root_path/out$out_tester/$1/monkey.log &

    # PUMA
    # puma_root=/home/yzy/projects/PUMA
    # cd $puma_root
    # package_name=$(aapt dump badging $root_path/apps/$1.apk | grep 'package\: name' | awk -F"'" '{print $2}')
    # app_label=$(aapt dump badging $root_path/apps/$1.apk | grep 'application\: label' | awk -F"'" '{print $2}')

    # if [ -z "$app_label" ]; then
    #     app_label=$(aapt dump badging $root_path/apps/$1.apk | grep 'launchable' | awk -F"'" '{print $4}')
    # fi

    # echo $app_label
    # echo $package_name > app.info.localhost:$2
    # echo $app_label >> app.info.localhost:$2
    # timeout 600s adb -s localhost:$2 install $root_path/apps/$1.apk
    # ./setup-phone.sh localhost:$2
    # timeout 12000s ./run.sh localhost:$2 &> $root_path/out$out_tester/$1/puma.log &

    # STOAT
    # adb -s localhost:$2 shell settings put secure show_ime_with_hard_keyboard 0
    # stoat_root=/home/yzy/projects/Stoat/Stoat/bin
    # cd $stoat_root
    # timeout 12000s ruby run_stoat_testing.rb --app_dir $root_path/apps/$1.apk --real_device_serial=localhost:$2 --stoat_port $3 --max_event 2000 --event_delay 1000 --model_time 12000s --project_type apk &> $root_path/out$out_tester/$1/stoat.log &

    # DROIDMATE
    export ANDROID_HOME=/home/yzy/projects/fake-android-sdk/
    export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64/
    droidmate_root=/home/yzy/projects/droidmate/project/pcComponents/API/build/libs
    cd $droidmate_root
    rm -rf ./apks_$2
    mkdir -p ./apks_$2
    cp $root_path/apps/$1.apk ./apks_$2/
    timeout 12000s java -jar shadow-1.0-RC4-all.jar -config defaultConfig.properties --Selectors-actionLimit=2000 --Exploration-deviceIndex=$2 --Exploration-deviceSerialNumber=localhost:$2 --Exploration-apksDir=./apks_$2 --Strategies-fitnessProportionate=true --DeviceCommunication-deviceOperationDelay=2000 --Deploy-uninstallApk=false --UiAutomatorServer-basePort=20000 --ApiMonitorServer-basePort=30000 &> $root_path/out$out_tester/$1/droidmate.log &

    tester_pid=$!
    ec_count=1

    while kill -0 "$tester_pid" > /dev/null 2>&1; do
        sleep 1
        echo "$ec_count" >> $root_path/out$out_tester/$1/activity_coverage
        adb -s localhost:$2 shell dumpsys activity activities | grep 'Hist #' >> $root_path/out$out_tester/$1/activity_coverage
        let ec_count++
    done

    # STOAT
    # pids=`ps a | grep 'Server.jar' | grep $1 | awk '{print $1}'`
    # echo $pids
    # for pid in $pids; do kill -9 $pid; done

    adb -s localhost:$2 shell dumpsys activity activities | grep 'Hist #' >> $root_path/out$out_tester/$1/finish_mark
    adb -s localhost:$2 shell reboot -p

else
    echo "PASS $1"
fi
