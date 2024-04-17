#!/bin/bash
SCONTROL="/usr/bin/scontrol"
PCREGREP="/usr/bin/pcregrep"
TR="/usr/bin/tr"
SORT="/usr/bin/sort"
COLUMN="/usr/bin/column"

if [ -t 1 ]; then
    $SCONTROL show nodes | $PCREGREP -o1 'AvailableFeatures=([^ ]*)' | $TR , '\n' | $SORT -u | $COLUMN
else
    $SCONTROL show nodes | $PCREGREP -o1 'AvailableFeatures=([^ ]*)' | $TR , '\n' | $SORT -u
fi
