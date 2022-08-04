#!/bin/bash


if [[ ! -f "run_summary.csv" ]]
then
    cp run_summary.csv.in run_summary.csv
fi

k5start -f ~/.Authentication/cvilela.kt -u cvilela
python3 update_run_summary.py -f run_summary.csv --lumi_path /eos/user/c/cvilela/sndlumi_2/
kdestroy -p cvilela@CERN.CH
