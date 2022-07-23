#!/bin/bash

CONVERTED_DIR=/eos/experiment/sndlhc/convertedData/commissioning/TI18/
TEMP_RECO_DIR=/afs/cern.ch/work/c/cvilela/private/tempReco/

SNDSW_SETUP=/cvmfs/sndlhc.cern.ch/SNDLHC-2022/June26/setUp.sh
SNDSW_DIR=/eos/home-c/cvilela/SND_Jul10

#source ${SNDSW_SETUP}
#cd ${SNDSW_DIR}
#eval `alienv load sndsw/latest-master-release`
#cd -

while IFS=, read -r run_number start_time end_time scale_factor
do
    # Get converted files
    for converted_file in `ls $CONVERTED_DIR/run_00${run_number}/sndsw_raw-*.root`
    do
	file_name="$(basename -- $converted_file)"
	file_name="${file_name%.*}"
	reco_file=${TEMP_RECO_DIR}/run_00${run_number}/${file_name}_muonReco.root
	if [ -f $reco_file ]
	then
	    echo Already reconstructed $reco_file
	else
	    mkdir -p ${TEMP_RECO_DIR}/run_00${run_number}/
	    cd ${TEMP_RECO_DIR}/run_00${run_number}/
	    python3 ${SNDSW_ROOT}/shipLHC/run_muonRecoSND.py -f $converted_file -g /eos/experiment/sndlhc/convertedData/commissioning/TI18/geofile_sndlhc_TI18_V1_06July2022.root -t 1 --hits_to_fit "ds" --hits_for_triplet "ds" -n 50000000 -o -s $scale_factor
	fi
    done
done < run_summary.csv


