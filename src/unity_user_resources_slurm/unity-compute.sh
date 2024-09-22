#!/bin/bash
set -e

_help() {
    echo "usage: \`unity-compute <num-cores>\`"
    echo "default num-cores: 2"
}

SRUN="/usr/bin/srun"
GETENT="/usr/bin/getent"
CUT="/usr/bin/cut"

if [ -z $1 ]; then
    num_cores=2
    _help
else
    num_cores=$1
fi

if [[ ! $num_cores =~ ^[0-9]+$ ]]; then
    echo "invalid argument! Expected integer number of threads."
    exit 1
fi

# $SHELL is not always defined
# my_login_shell=$(ldapsearch -h identity -x -b ou=users,dc=unity,dc=rc,dc=umass,dc=edu -o ldif-wrap=no -LL cn=$USER loginShell | grep loginShell | cut -f 2 -d ' ')
my_login_shell=$($GETENT passwd $USER | $CUT -d: -f7)

command="$SRUN --pty -c $num_cores --mem=4G -p cpu-preempt $my_login_shell"
echo "$command"
eval "$command"
