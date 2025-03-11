#!/bin/bash

#if [ $# != 2 ] ; then
#        echo "Please provide CONFIG"
#        exit 1
#fi

config=$1
build_id=$2
data_size=$3
read_write_ratio=$4
iterations=$5

test_mode=$build_id"_"$config


for ((i=1;i<=$iterations;i++));
  do
    sleep 5
    ./instance_benchmark.sh $data_size $read_write_ratio $test_mode $i 180
  done

sleep 5

cd /root/redis/redis-7.0.0/log/set/

rename 's/:/0/' *

[ -d $build_id ] || mkdir $build_id

# Removing the old data and copying the new data
mv *.csv $build_id/
#rm set/*
