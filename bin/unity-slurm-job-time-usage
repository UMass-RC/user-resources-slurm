#!/bin/bash
num_jobs_printed=6
if [ ! -z "$1" ]; then
    if ! echo "$1" | grep -E '^[0-9]+$' &> /dev/null; then
        echo "argument must be an integer"
        exit 1
    fi
    num_jobs_printed=$1
fi
sacct_out=$(sacct --user $USER --state COMPLETED --allocations -S now-365days -E now --format=jobname,jobid,elapsed,timelimit)
num_lines=$(echo "$sacct_out" | wc -l)
if [ "$num_jobs_printed" -lt "$num_lines" ]; then
    echo "$sacct_out" | head -n 2
fi
echo "$sacct_out" | tail -n $num_jobs_printed

