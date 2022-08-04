#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
LUMI_WORK_DIR=/eos/user/c/cvilela/sndlumi_2

first=`head -n1 ${SCRIPT_DIR}/run_summary.csv.in | awk -F'[,]' '{print $2}'`
now=`date -u +"%Y-%m-%d %H:%M:%S"`

k5start -f ~/.Authentication/cvilela.kt -u cvilela
latest_lumi_file=`ls -rt ${LUMI_WORK_DIR}/sndlhc_atlas_lumi_*.csv 2> /dev/null | tail -n 1`

if [[ -z $latest_lumi_file ]];
then
	start_date=$first
else
        datetime=`tail -n1 $latest_lumi_file | awk -F'[,]' '{print $1}'`
	date=`echo $datetime | awk -F'[T]' '{print $1}'`
	time=`echo $datetime | awk -F'[T]' '{print $2}'`
	start_date="${date} ${time}"
fi

kdestroy -p cvilela@CERN.CH

echo Requesting lumi from $start_date to $now

cd ${SCRIPT_DIR}

k5start -f ~/.Authentication/cristova.kt -u cristova
python3 ${SCRIPT_DIR}/getATLASLumi.py 0 "$start_date" "$now" 
kdestroy -p cristova@CERN.CH

if [[ -f "sndlhc_atlas_lumi_0.csv" ]]
then
	k5start -f ~/.Authentication/cvilela.kt -u cvilela
	xrdcp -f sndlhc_atlas_lumi_0.csv ${LUMI_WORK_DIR}/sndlhc_atlas_lumi_`date +"%Y%m%d_%H%M%S"`.csv
	rm sndlhc_atlas_lumi_0.csv
	kdestroy -p cvilela@CERN.CH
fi
