root_path=/home/yzy/humanoid/
humanoid_server=162.105.87.118:43997

out_tester=_humanoid
# out_tester=_monkey

rm -rf $root_path/out$out_tester/$1
mkdir -p $root_path/out$out_tester/$1

qemu-img create -f qcow2 $root_path/qemu/droidbot-6.0-r3.qcow2.$2 -o backing_file=$root_path/qemu/droidbot-6.0-r3.qcow2

qemu-system-i386 -hda $root_path/droidbot-6.0-r3.qcow2.$2 -m 2048 -smp cpus=4 -enable-kvm -machine q35 -nographic -net nic,model=e1000 -net user,hostfwd=tcp::$2-:5555 &

sleep 60
adb connect localhost:$2

# DROIDBOT
timeout 20000s droidbot -d localhost:$2 -a $root_path/apps/$1.apk -interval 3 -count 2000 -policy dfs_greedy -grant_perm -keep_env -keep_app -random -is_emulator -humanoid $humanoid_server -o $root_path/out$out_tester/$1/droidbot_out &> $root_path/out$out_tester/$1/droidbot.log &

tester_pid=$!
ec_count=1

while kill -0 "$tester_pid" > /dev/null 2>&1; do
    sleep 600
    adb -s localhost:$2 shell am broadcast -a edu.gatech.m3.emma.COLLECT_COVERAGE
    adb -s localhost:$2 pull /sdcard/coverage.ec $root_path/out$out_tester/$1/coverage.ec.$ec_count
    let ec_count++
done

adb -s localhost:$2 pull /sdcard/coverage.ec $root_path/out$out_tester/$1/coverage.ec
adb -s localhost:$2 shell reboot -p

