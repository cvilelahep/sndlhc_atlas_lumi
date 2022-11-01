#!/bin/bash

source /cvmfs/sndlhc.cern.ch/SNDLHC-2022/July14/setUp.sh

DEAD_TIME_DIR=/home/sndlumi/dead-time-and-emulsion-runs
EOS_DIR=/eos/experiment/sndlhc/www/luminosity/

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
LOG_DIR=${SCRIPT_DIR}/Logs/
LOG_FILE_NAME=${LOG_DIR}/get_nxcals_data_`date +'%Y%m%d'`.log

echo `date` Start 2>&1 | tee -a $LOG_FILE_NAME
echo Getting nxcals data 2>&1 | tee -a $LOG_FILE_NAME
python3 -u ${SCRIPT_DIR}/getLumiFill.py -o /eos/experiment/sndlhc/nxcals_data 2>&1 | tee -a $LOG_FILE_NAME
echo Updating deadtime | tee -a $LOG_FILE_NAME
cd $DEAD_TIME_DIR
k5start -f ~/.Authentication/cvilela.kt -u cvilela
git pull | tee -a $LOG_FILE_NAME
cd $SCRIPT_DIR
echo Making summary | tee -a $LOG_FILE_NAME
python3 -u ${SCRIPT_DIR}/makeLumiSummary.py > lumi_summary.txt
echo Copying to EOS | tee -a $LOG_FILE_NAME
xrdcp -f sndlhc_delivered_recorded_integrated_lumi* $EOS_DIR 2>&1 | tee -a $LOG_FILE_NAME
xrdcp -f sndlhc_delivered_recorded_instantaneous_lumi* $EOS_DIR 2>&1 | tee -a $LOG_FILE_NAME
xrdcp -f lumi_summary.txt $EOS_DIR 2>&1 | tee -a $LOG_FILE_NAME
tree -T "SND@LHC Luminosity report" -I "index.html" -H '.' -L 1 --noreport --charset utf-8 -o index.html $EOS_DIR | tee -a $LOG_FILE_NAME
xrdcp -f index.html $EOS_DIR/index.html

rm sndlhc_delivered_recorded_integrated_lumi* sndlhc_delivered_recorded_instantaneous_lumi* lumi_summary.txt index.html
echo `date` Done 2>&1 | tee -a $LOG_FILE_NAME
