#!/bin/bash

RAW_DATA_DIR=/eos/experiment/sndlhc/raw_data/commissioning/TI18/data/
LUMI_DIR=/eos/user/c/cvilela/lumi_test/
PLOTS_DIR=/eos/user/c/cvilela/lumi_plots/

MAX_FILES=5000

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

LOG_DIR=${SCRIPT_DIR}/Logs/

LOG_FILE_NAME=${LOG_DIR}/updateLumiPlots_`date +'%Y%m%d'`.log

k5start -f ~/.Authentication/cvilela.kt -u cvilela

LAST_RUNS=(`ls -rt ${LUMI_DIR} | tail -n${MAX_FILES}`)

PROCESSED_RUNS=(`ls -rt ${PLOTS_DIR} | tail -n${MAX_FILES} | cut -d'.' -f1`)

source /cvmfs/sndlhc.cern.ch/SNDLHC-2022/July14/setUp.sh

for last_run in ${LAST_RUNS[@]}
do
	# If this run hasn't been processed yet, process it.
	if [[ ! " ${PROCESSED_RUNS[*]} " =~ " ${last_run} " ]]; then

                echo `date` PROCESSING ${last_run}  2>&1 | tee -a $LOG_FILE_NAME
 python3 makeSummaryPlotsROOT.py --raw_data_dir /eos/experiment/sndlhc/raw_data/commissioning/TI18/data/run_004626/ --lumi_dir /eos/user/c/cvilela/lumi_test/run_004626/
		python3 -u --raw_data_dir ${RAW_DATA_DIR}/$last_run --lumi_dir ${LUMI_DIR}/$last_run --output_file ${PLOTS_DIR}/${last_run}.root
		echo `date` END ${last_run}  2>&1 | tee -a $LOG_FILE_NAME
	fi
done
