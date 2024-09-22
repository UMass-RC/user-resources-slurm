#!/usr/bin/env python3
"""
Print the resource usage for each user under a slurm account
"""
import sys
import json
import subprocess as subp

MAX_USERNAME_LENGTH = 100

IGNORE_PARTITIONS = ["cpu-preempt", "gpu-preempt"]

squeue_json = None

def fmt_table(table) -> str:
    """
    I would use tabulate but I don't want nonstandard imports
    """
    table_output = ""
    # no row has more elements than the header row
    assert(all(len(row) <= len(table[0]) for row in table))
    column_widths = [ 0 ] * len(table[0])
    for row in table:
        for i,element in enumerate(row):
            if len(str(element)) > column_widths[i]:
                column_widths[i] = len(str(element))
    column_widths = [ x + 3 for x in column_widths ] # room for whitespace on either side
    table_output += "\033[4m" # start underline
    for i,column_header in enumerate(table[0]):
        if i > 0:
            table_output += '|'
        table_output += str(column_header).center(column_widths[i]-1) # minus one for the '|'
    table_output += "\033[0m" # end underline
    table_output += '\n'
    for row in table[1:]:
        for i,value in enumerate(row):
            table_output += str(value).ljust(column_widths[i])
        table_output += '\n'
    return(table_output)

def user_usage(accounts=None, partitions=None, states=None):
    """
    returns a report of the total number of CPU's and GPU's each user is using
    slurm arguments for accounts, partitions, states, don't seem to work.
    accounts/partitions/states are case insensitive.
    """
    # don't gather `squeue --json` multiple times, save the result in a global variable
    global squeue_json
    if squeue_json is None:
        print("collecting info from slurm...", end="\r", file=sys.stderr)
        squeue_json = json.loads(subp.check_output(["squeue", "--all", "--json"], timeout=10))
    jobs = squeue_json["jobs"]
    if accounts is not None:
        accounts = [x.lower() for x in accounts]
        jobs = [x for x in jobs if x["account"].lower() in accounts]
    if partitions is not None:
        partitions = [x.lower() for x in partitions]
        jobs = [x for x in jobs if x["partition"].lower() in partitions]
    if states is not None:
        states = [x.lower() for x in states]
        jobs = [x for x in jobs if x["job_state"].lower() in states]
    # build user_usage dictionary
    user_usage_dict = {}
    cpu_total = 0
    gpu_total = 0
    for job in jobs:
        user = job["user_name"]
        num_cpus = job["cpus"]["number"]
        num_gpus = 0
        tres_str = job["tres_alloc_str"]
        # pending job will have no resources allocated, use resources requested instead
        if len(tres_str) == 0:
            tres_str = job["tres_req_str"]
        for resource in tres_str.split(','):
            if resource.startswith("gres/gpu="):
                num_gpus += int(resource.rsplit('=',1)[-1])
        # get info from user dictionary, add to totals, put new info back in user dictionary
        if user not in user_usage_dict:
            user_cpu_total, user_gpu_total  = (0, 0)
        else:
            user_cpu_total, user_gpu_total = user_usage_dict[user]
        user_cpu_total += num_cpus
        cpu_total += num_cpus
        user_gpu_total += num_gpus
        gpu_total += num_gpus
        user_usage_dict[user] = (user_cpu_total, user_gpu_total)
    user_usage_dict["total"] = (cpu_total, gpu_total)
    return user_usage_dict

# `groups` makes output delimited by spaces, `tr` replaces spaces with newlines
list_pi_groups_cmd = r"/usr/bin/groups | /usr/bin/tr ' ' '\n' | /usr/bin/grep -e ^pi_"
pi_groups = subp.check_output(list_pi_groups_cmd, shell=True, timeout=1).decode().splitlines()
no_usage_printed = True
for pi_group in pi_groups:
    running_usage        = user_usage(accounts=[pi_group], states=["running"])
    pending_usage        = user_usage(accounts=[pi_group], states=["pending"])
    running_usage_ignore = user_usage(accounts=[pi_group], partitions=IGNORE_PARTITIONS, states=["running"])
    pending_usage_ignore = user_usage(accounts=[pi_group], partitions=IGNORE_PARTITIONS, states=["pending"])
    all_users = set()
    all_users.update(running_usage.keys())
    all_users.update(pending_usage.keys())
    overall_user_usage = {}
    for user in all_users:
        overall_user_usage[user] = {
            "cpu_alloc": 0,
            "gpu_alloc": 0,
            "cpu_pending": 0,
            "gpu_pending": 0,
        }
    for user, (cpu_count, gpu_count) in running_usage.items():
        overall_user_usage[user]["cpu_alloc"] += cpu_count
        overall_user_usage[user]["gpu_alloc"] += gpu_count
    for user, (cpu_count, gpu_count) in running_usage_ignore.items():
        overall_user_usage[user]["cpu_alloc"] -= cpu_count
        overall_user_usage[user]["gpu_alloc"] -= gpu_count
    for user, (cpu_count, gpu_count) in pending_usage.items():
        overall_user_usage[user]["cpu_pending"] += cpu_count
        overall_user_usage[user]["gpu_pending"] += gpu_count
    for user, (cpu_count, gpu_count) in pending_usage_ignore.items():
        overall_user_usage[user]["cpu_pending"] -= cpu_count
        overall_user_usage[user]["gpu_pending"] -= gpu_count
    print(f"Current resource allocation under account \"{pi_group}\":", end='')
    if len(overall_user_usage)==1: # if "total" is the only element
        print(" (none)")
        print()
        continue
    else:
        print()

    user_counts_raw = []
    for user, counts in overall_user_usage.items():
        user_counts_raw.append([user, *counts.values()])
    rows_labeled_total = [x for x in user_counts_raw if x[0] == "total"]
    assert len(rows_labeled_total) == 1
    total_row = rows_labeled_total[0]
    rows_not_labeled_total = [x for x in user_counts_raw if x[0] != "total"]
    del user_counts_raw

    output_table = [["username", "CPUs allocated", "GPUs allocated", "CPUs pending", "GPUs pending"]]
    # sort rows by username
    output_table = output_table + sorted(rows_not_labeled_total, key=lambda x: x[0])
    output_table = output_table + [total_row]

    print(fmt_table(output_table))

print("Note: CPU count and GPU count do not include those in preempt queues.")
print("This means that the total applies directly to your account based CPU and GPU limits.")
print()
