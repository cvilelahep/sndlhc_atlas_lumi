#!/bin/bash

RAW_DATA_DIR=/eos/experiment/sndlhc/raw_data/commissioning/TI18/data/
LUMI_DIR=/eos/user/c/cvilela/lumi_test/

MAX_FILES=500

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

LOG_DIR=${SCRIPT_DIR}/Logs/

LOG_FILE_NAME=${LOG_DIR}/updateLumi_`date +'%Y%m%d'`.log

k5start -f ~/.Authentication/cvilela.kt -u cvilela

LAST_RUNS=(`ls -rt ${RAW_DATA_DIR} | tail -n${MAX_FILES}`)

PROCESSED_RUNS=(`ls -rt ${LUMI_DIR} | tail -n${MAX_FILES}`)

source /cvmfs/sndlhc.cern.ch/SNDLHC-2022/July14/setUp.sh

for last_run in ${LAST_RUNS[@]}
do
	# If this run hasn't been processed yet, process it.
	if [[ ! " ${PROCESSED_RUNS[*]} " =~ " ${last_run} " ]]; then

		timestamp_file=${RAW_DATA_DIR}/${last_run}/run_timestamps.json

		if [[ $last_run == *"monitoring"* ]]; then
			continue
		fi

                echo `date` PROCESSING ${last_run}  2>&1 | tee -a $LOG_FILE_NAME

		if [ ! -f "$timestamp_file" ]; then
			echo `date` $timestamp_file does not exist. Skipping this run. 2>&1 | tee -a $LOG_FILE_NAME
			continue
		fi

		start_time=`jq -r ".start_time" $timestamp_file`
		if [[ start_time == *"Z"* ]];
		then
			start_time=`date +'%Y-%m-%d %H:%M:%S' -d $start_time`
		else
    			start_time=`date +'%Y-%m-%d %H:%M:%S' -d "TZ=\"CEST\" ${start_time}"`
		fi

		stop_time=`jq -r ".stop_time" $timestamp_file`

		if [[ $stop_time == "null" ]];
		then
			echo $timestamp_file does not contain the stop time. Extracting run duration from data file. 2>&1 | tee -a $LOG_FILE_NAME
			
			last_data=`ls -r ${RAW_DATA_DIR}/${last_run}/data_*.root | head -n 1`
			echo Last data file: $last_data 2>&1 | tee -a $LOG_FILE_NAME
			run_duration_seconds=`python3 <<EOF
import ROOT
f=ROOT.TFile("${last_data}")
if hasattr(f, "event") :
   f.event.GetEntry(f.event.GetEntries()-1)
   print(f.event.timestamp*6.25/1e9)
else :
   f.data.GetEntry(f.data.GetEntries()-1)
   print(f.data.evt_timestamp*6.25/1e9)
EOF`
			echo Run duration in seconds: $run_duration_seconds 2>&1 | tee -a $LOG_FILE_NAME
			
			if [[ start_time == *"Z"* ]];
                	then
		 		stop_time=`date +'%Y-%m-%d %H:%M:%S' -d "$start_time + $run_duration_seconds seconds"`
			else
				stop_time=`date +'%Y-%m-%d %H:%M:%S' -d "TZ=\"CEST\" $start_time + $run_duration_seconds seconds"`
			fi

		elif [[ stop_time == *"Z"* ]];
		then
			stop_time=`date +'%Y-%m-%d %H:%M:%S' -d $stop_time`
		else
    			stop_time=`date +'%Y-%m-%d %H:%M:%S' -d "TZ=\"CEST\" ${stop_time}"`
		fi

		echo GETTING data between $start_time and $stop_time 2>&1 | tee -a $LOG_FILE_NAME

		kdestroy -p cvilela@CERN.CH

		mkdir -p temp/${last_run}

		k5start -f ~/.Authentication/cristova.kt -u cristova
		python3 -u getLumiROOT.py -o temp/${last_run} "$start_time" "$stop_time" --nxcals_variables ATLAS:LUMI_TOT_INST ATLAS.OFFLINE:LUMI_TOT_INST CMS:LUMI_TOT_INST CMS.OFFLINE:LUMI_TOT_INST LHCB:LUMI_TOT_INST ALICE:LUMI_TOT_INST LHC.BRAND.1R:LuminosityBunchSum:totalLuminosityBunchSum LHC.BRANA.4L1:TOTAL_LUMINOSITY HX:BETASTAR_IP1 LHC.BRANA.4L1:LUMINOSITY_Q1 LHC.BRANA.4L1:LUMINOSITY_Q2 LHC.BRANA.4L1:LUMINOSITY_Q3 LHC.BRANA.4L1:LUMINOSITY_Q4 HX:BMODE LHC.LUMISERVER:AutomaticScanIP1:Nominal_Separation LHC.LUMISERVER:AutomaticScanIP1:Nominal_Separation_Plane 2>&1 | tee -a $LOG_FILE_NAME
		
		kdestroy -p cristova@CERN.CH

		k5start -f ~/.Authentication/cvilela.kt -u cvilela
		xrdcp -v -r temp/${last_run} ${LUMI_DIR}/ 2>&1 | tee -a $LOG_FILE_NAME
		rm -rf temp/${last_run}

		echo `date` END ${last_run}  2>&1 | tee -a $LOG_FILE_NAME
	fi
done
