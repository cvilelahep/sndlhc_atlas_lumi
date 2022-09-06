#!/bin/bash

out_dir=run_004726

timestamp_file=run_timestamps_${out_dir}.json

start_time=`jq -r ".start_time" $timestamp_file`
if [[ start_time == *"Z"* ]];
then
    start_time=`date +'%Y-%m-%d %H:%M:%S' -d $start_time`
else 
    start_time=`date +'%Y-%m-%d %H:%M:%S' -d "TZ=\"CEST\" ${start_time}"`
fi

stop_time=`jq -r ".stop_time" $timestamp_file`
if [[ stop_time == *"Z"* ]];
then
    stop_time=`date +'%Y-%m-%d %H:%M:%S' -d $stop_time`
else 
    stop_time=`date +'%Y-%m-%d %H:%M:%S' -d "TZ=\"CEST\" ${stop_time}"`
fi

#if stop_time == "null";
#then

mkdir -p $out_dir

python3 getLUMIROOT.py -o $out_dir "$start_time" "$stop_time" --nxcals_variables ATLAS:LUMI_TOT_INST ATLAS.OFFLINE:LUMI_TOT_INST CMS:LUMI_TOT_INST CMS.OFFLINE:LUMI_TOT_INST LHCB:LUMI_TOT_INST ALICE:LUMI_TOT_INST LHC.BRAND.1R:LuminosityBunchSum:totalLuminosityBunchSum LHC.BRANA.4L1:TOTAL_LUMINOSITY HX:BETASTAR_IP1 LHC.BRANA.4L1:LUMINOSITY_Q1 LHC.BRANA.4L1:LUMINOSITY_Q2 LHC.BRANA.4L1:LUMINOSITY_Q3 LHC.BRANA.4L1:LUMINOSITY_Q4 HX:BMODE
