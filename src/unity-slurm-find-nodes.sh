#!/bin/bash
set -e

_help() {
    echo What constraint would you like to search for? 1>&2
    echo "use \`unity-slurm-list-constraints\` for examples." 1>&2
}

SINFO="/usr/bin/sinfo"
GREP="/usr/bin/grep"
AWK="/usr/bin/awk"
SORT="/usr/bin/sort"
COLUMN="/usr/bin/column"
WC="/usr/bin/wc"

if (($# == 0)); then
    _help
    exit 1
fi

if (($# > 1)); then
    echo "too many arguments! Expected 1 argument." 1>&2
    exit 1
fi

nodes_found=$($SINFO -N -o "%n %f" | $GREP -E "(,|\\s)$1(,|\\s|$)" | $AWK '{print $1;}' | $SORT -u)
echo "$nodes_found" | $COLUMN
echo found $(echo "$nodes_found" | $WC -w) nodes. 1>&2
