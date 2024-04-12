#!/bin/bash

source /cvmfs/sndlhc.cern.ch/SNDLHC-2022/July14/setUp.sh

DEAD_TIME_DIR=/home/sndlumi/dead-time-and-emulsion-runs
EOS_DIR=/eos/experiment/sndlhc/www/luminosity/

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
LOG_DIR=${SCRIPT_DIR}/Logs/
LOG_FILE_NAME=${LOG_DIR}/get_nxcals_data_`date +'%Y%m%d'`.log

echo `date` Start 2>&1 | tee -a $LOG_FILE_NAME
echo Getting nxcals data 2>&1 | tee -a $LOG_FILE_NAME
python3 -u ${SCRIPT_DIR}/getLumiFill.py -o /eos/experiment/sndlhc/nxcals_data --raw_data_dir /eos/experiment/sndlhc/raw_data/physics/2024/ecc_run_06/ 2>&1 | tee -a $LOG_FILE_NAME
echo Getting ATLAS data 2>&1 | tee -a $LOG_FILE_NAME
python3 -u ${SCRIPT_DIR}/getLumiFillATLAS.py -o /eos/experiment/sndlhc/atlas_lumi 2>&1 | tee -a $LOG_FILE_NAME
echo Updating deadtime | tee -a $LOG_FILE_NAME
cd $DEAD_TIME_DIR
k5start -f ~/.Authentication/cvilela.kt -u cvilela
git pull | tee -a $LOG_FILE_NAME
cd $SCRIPT_DIR
echo Making summary | tee -a $LOG_FILE_NAME
#python3 -u ${SCRIPT_DIR}/makeLumiSummary.py > lumi_summary.txt
PYTHONPATH=/home/sndlumi/.local/lib/python3.8/site-packages:${PYTHONPATH} python makeLumiSummaryDataFrame.py
xrdcp -f index.html $EOS_DIR 2>&1 | tee -a $LOG_FILE_NAME
xrdcp -f Plots/* $EOS_DIR 2>&1 | tee -a $LOG_FILE_NAME

rm -rf index.html Plots
echo `date` Done 2>&1 | tee -a $LOG_FILE_NAME
