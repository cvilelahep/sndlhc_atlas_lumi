#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
LUMI_WORK_DIR=/eos/user/c/cvilela/sndlumi_2

first=`head -n1 ${SCRIPT_DIR}/run_summary.csv.in | awk -F'[,]' '{print $2}'`
now=`date +"%Y-%m-%d %H:%M:%S"`

k5start -f ~/.Authentication/cvilela.kt -u cvilela
latest_lumi_file=`ls -rt ${LUMI_WORK_DIR}/sndlhc_atlas_lumi_*.csv 2> /dev/null | tail -n 1`
kdestroy -p cvilela@CERN.CH

if [[ -z $latest_lumi_file ]];
then
	start_date=$first
else
	lumi_f_name=`basename $latest_lumi_file .csv`
	lumi_f_date=`echo $lumi_f_name | awk -F'[_]' '{print $4}'`
	lumi_f_year=${lumi_f_date:0:4}
	lumi_f_month=${lumi_f_date:4:2}
	lumi_f_day=${lumi_f_date:6:2}
	lumi_f_time=`echo $lumi_f_name | awk -F'[_]' '{print $5}'`
	lumi_f_hour=${lumi_f_time:0:2}
	lumi_f_min=${lumi_f_time:2:2}
	lumi_f_sec=${lumi_f_time:4:2}
	start_date="${lumi_f_year}-${lumi_f_month}-${lumi_f_day} ${lumi_f_hour}:${lumi_f_min}:${lumi_f_sec}"
fi

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
