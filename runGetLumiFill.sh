#!/bin/bash

source /cvmfs/sndlhc.cern.ch/SNDLHC-2022/July14/setUp.sh

LOG_DIR=${SCRIPT_DIR}/Logs/

LOG_FILE_NAME=${LOG_DIR}/get_nxcals_data_`date +'%Y%m%d'`.log

python3 getLumiFill.py -o /eos/user/c/cvilela/nxcals_data 2>&1 | tee -a $LOG_FILE_NAME
