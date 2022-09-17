#!/bin/bash

source /cvmfs/sndlhc.cern.ch/SNDLHC-2022/July14/setUp.sh

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
LOG_DIR=${SCRIPT_DIR}/Logs/
LOG_FILE_NAME=${LOG_DIR}/get_nxcals_data_`date +'%Y%m%d'`.log

echo `date` Start 2>&1 | tee -a $LOG_FILE_NAME
python3 -u ${SCRIPT_DIR}/getLumiFill.py -o /eos/experiment/sndlhc/nxcals_data 2>&1 | tee -a $LOG_FILE_NAME
echo `date` Done 2>&1 | tee -a $LOG_FILE_NAME
