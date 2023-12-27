#!/usr/bin/env python3
import json
import subprocess
from typing import Tuple

MAX_USERNAME_LENGTH = 100

squeue_json = None

def shell_command(command: str, timeout_s: int) -> Tuple[str, str]:
    #print(command)
    process = subprocess.run(command,timeout=timeout_s,capture_output=True,shell=True,check=True)
    # process.stdout returns a bytes object, convert to string
    _stdout = str(process.stdout, 'UTF-8').strip()
    _stderr = str(process.stderr, 'UTF-8').strip()
    return _stdout, _stderr

def user_usage(accounts=None, partitions=None, states=None):
    """
    returns a report of the total number of CPU's and GPU's each user is using
    slurm arguments for accounts, partitions, states, don't seem to work.
    accounts/partitions/states are case insensitive.
    """
    # don't gather `squeue --json` multiple times, save the result in a global variable
    global squeue_json
    if squeue_json is None:
        _stdout, _stderr = shell_command("squeue --json", 10)
        squeue_json = json.loads(_stdout)
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
        num_cpus = len(job["cpus"])
        gres = job["tres_alloc_str"]
        num_gpus = 0
        for resource in gres.split(','):
            if resource.startswith("gpu:"):
                num_gpus += int(resource.split(':')[-1])
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

def main():
    # `groups` makes output delimited by spaces, `tr` replaces spaces with newlines
    list_pi_groups = r"/usr/bin/groups | /usr/bin/tr ' ' '\n' | /usr/bin/grep -e ^pi_"
    _stdout, _stderr = shell_command(list_pi_groups, 1)
    pi_groups = _stdout.splitlines()
    no_usage_printed = True
    for pi_group in pi_groups:
        running_usage = user_usage(accounts=[pi_group], states=["running"])
        preempt_usage = user_usage(accounts=[pi_group], partitions=["cpu-preempt","gpu-preempt"], states=["running"])
        pending_usage = user_usage(accounts=[pi_group], states=["pending"])
        overall_user_usage = {}
        # add running usage to dict
        for user, (running_cpus, running_gpus) in running_usage.items():
            overall_user_usage[user] = (running_cpus, running_gpus, 0, 0)
        # subtract preempt usage from running usage, because it doesn't apply to the quota
        for user, (preempt_cpus, preempt_gpus) in preempt_usage.items():
            running_cpus, running_gpus = running_usage[user]
            overall_user_usage[user] = (running_cpus - preempt_cpus, running_gpus - preempt_gpus, 0, 0)
        # add pending usage to the dict
        for user, (pending_cpus, pending_gpus) in pending_usage.items():
            if user in overall_user_usage:
                cpus, gpus = overall_user_usage[user][0], overall_user_usage[user][1]
            else:
                cpus, gpus = (0, 0)
            overall_user_usage[user] = (cpus, gpus, pending_cpus, pending_gpus)

        print(f"Current resource allocation under account \"{pi_group}\":", end='')
        if len(overall_user_usage)==1: # if "total" is the only element
            print(" (none)")
            print()
            continue
        else:
            print()
        total_usage = overall_user_usage["total"]
        print(f"* CPU count: {total_usage[0]}")
        print(f"* GPU count: {total_usage[1]}")
        print()
        no_usage_printed = False
    if not no_usage_printed:
        print("use the `unity-slurm-account-usage` command for more info.")
        print()

if __name__=="__main__":
    main()
