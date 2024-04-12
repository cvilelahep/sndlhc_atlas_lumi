import os
import argparse
import pickle
import glob

import ROOT

import array
import numpy as np
import json

import time
import datetime
import pytz
import dateutil.parser

parser = argparse.ArgumentParser(description='Get luminosity from NXCALS and save to ROOT TTrees')

parser.add_argument("-o", "--output_dir", type = str, help="Directory to store the ROOT files", required=True)
parser.add_argument("--raw_data_dirs", type = str, help="Directories with SND@LHC raw data", default="/eos/experiment/sndlhc/raw_data/physics/2022/,/eos/experiment/sndlhc/raw_data/physics/2023_tmp/")

args = parser.parse_args()

def downsample_2d(d, factor) :
    times = d[0]
    values = d[1]

    # Make arrays divisible by factor (throw away remainder)
    length = len(times)

    if length < factor :
        factor = length
    
    new_length = int(length/factor)*factor
    
    times = times[:new_length]
    values = values[:new_length]

    downsampled_times = times.reshape(-1, int(factor)).mean(axis = 1)
    downsampled_values = values.reshape(-1, int(factor), values.shape[-1]).mean(axis = 1)

    return(downsampled_times, downsampled_values)

NXCALS_VARIABLES = {}
NXCALS_VARIABLES["LuminosityIP1"] = [["ATLAS:LUMI_TOT_INST", 12*60*60, None],
                                     ["ATLAS:BUNCH_LUMI_INST", 12*60*60, None],
                                     ["ATLAS.OFFLINE:LUMI_TOT_INST", 12*60*60, None],
                                     ["ATLAS.OFFLINE:BUNCH_LUMI_INST", 12*60*60, None],
                                     ["LHC.BRAND.1R:LuminosityBunchSum:totalLuminosityBunchSum", 12*60*60, None],
                                     ["LHC.BRANA.4L1:TOTAL_LUMINOSITY", 12*60*60, None],
                                     ["LHC.BRANA.4L1:LUMINOSITY_Q1", 12*60*60, None],
                                     ["LHC.BRANA.4L1:LUMINOSITY_Q2", 12*60*60, None],
                                     ["LHC.BRANA.4L1:LUMINOSITY_Q3", 12*60*60, None],
                                     ["LHC.BRANA.4L1:LUMINOSITY_Q4", 12*60*60, None]]

NXCALS_VARIABLES["LuminosityOtherIPs"] = [["CMS:LUMI_TOT_INST", 12*60*60, None],
                                          ["CMS.OFFLINE:LUMI_TOT_INST", 12*60*60, None],
                                          ["LHCB:LUMI_TOT_INST", 12*60*60, None],
                                          ["ALICE:LUMI_TOT_INST", 12*60*60, None]]

NXCALS_VARIABLES["LHC"] = [["HX:BMODE", 12*60*60, None],
                           ["LHC.STATS:LHC:INJECTION_SCHEME", 12*60*60, None],
                           ["HX:BETASTAR_IP1", 12*60*60, None],
#                           ["LHC.BQM.B%:BUNCH_INTENSITIES", 120*60, lambda d : downsample_2d(d, 60)], # Data gets published every second or so. A factor of 60 will result in about one data point per minute. The 120 minute time interval for the database queries is determined by the available memory in the VM this script is currently running in.
#                           ["LHC.BQM.B%:FILLED_BUCKETS", 120*60, lambda d : downsample_2d(d, 60)],
#                           ["LHC.BCTFR.%6R4.B%:BUNCH_INTENSITY", 120*60, lambda d : downsample_2d(d, 60)],
                           ["LHC.BCTFR.%6R4.B%:BEAM_INTENSITY", 12*60*60, None]]

NXCALS_VARIABLES["AutomaticScans"] = [["LHC.LUMISERVER:AutomaticScanIP%:Nominal%", 12*60*60, None]]

NXCALS_VARIABLES["CollimatorSettingsIP1"] =  [["TCL.%1.B%:SET_%", 12*60*60, None],
                                              ["TCTP%.%1.%:SET_%", 12*60*60, None]]

FIRST_FILL=7920
FIRST_RUN=4362

EPSILON = 1e-6 # To avoid rounding trouble. Look for database entries starting 1 ms before the start of the fill.

# Temporary, for running on my VM. Will move to sndonline user and remove these lines. Secondary account to access SND@LHC EOS.
os.system("k5start -f ~/.Authentication/cvilela.kt -u cvilela")

# HERE CHECK fill number and run number in processed fills.
try :
    last_processed_fill = int(glob.glob(args.output_dir+"/fill_*.root")[-1].split('/')[-1].split('_')[1].split('.')[0])
except IndexError :
    last_processed_fill = FIRST_FILL - 1

try :
    f_temp = ROOT.TFile(args.output_dir+"/fill_{0:06d}.root".format(last_processed_fill))
    try :
        last_processed_run = int(f_temp.Get("LHC/"+NXCALS_VARIABLES["LHC"][0][0].replace(":", "_").replace(".", "_")).GetMaximum("run_number"))
    except AttributeError :
        print("No beam mode data in previous fill, so processing files from the start")
        last_processed_run = FIRST_RUN
    f_temp.Close()
    del f_temp
except OSError :
    last_processed_run = FIRST_RUN

if last_processed_run <= 0 :
    last_processed_run = FIRST_RUN
    
print("Processing data from run {0}".format(last_processed_run))

import snd_run_tools
rTools = snd_run_tools.runTools(args.raw_data_dirs, "/eos/experiment/sndlhc/convertedData/commissioning/TI18/RunInfodict.root")
raw_data_times = rTools.getRunTimes(last_processed_run)

# Temporary, for running on my VM. Will move to sndonline user and remove these lines. Primary account to access NXCALS.
os.system("k5start -f ~/.Authentication/cristova.kt -u cristova")

import pytimber
ldb = pytimber.LoggingDB(source="nxcals")

# Get last completed fill
last_completed_fill = ldb.getLHCFillData()
last_fill_to_process = last_completed_fill

last_run_end = max(raw_data_times[:,2])
if last_processed_fill != last_completed_fill['fillNumber'] :
    print("Processing fills from {0} to {1}".format(last_processed_fill + 1, last_completed_fill['fillNumber']))
for i_fill in range(last_processed_fill + 1, last_completed_fill['fillNumber'] + 1) :
    print("Looking at fill {0}".format(i_fill))
    this_fill = ldb.getLHCFillData(i_fill)

    if this_fill is None :
        print("Fill {} not found. Skipping".format(i_fill))
        continue

    # First, check if the fill ends before the end of the last available run. If not, do not process it yet.
    if this_fill['endTime'] > last_run_end :
        print("Current fill end time ({0}) is after the last completed run end time ({1}). Skipping.".format(this_fill['endTime'], last_run_end))
        continue
    
    # Find runs belonging to this fill
    run_starts_before_fill_end = raw_data_times[:,1] < this_fill['endTime']
    run_ends_after_fill_start = raw_data_times[:,2] > this_fill['startTime']
    
    runs_in_fill = raw_data_times[np.logical_and(run_starts_before_fill_end, run_ends_after_fill_start)]
    
    # Open output file
#    f_out = ROOT.TFile(args.output_dir+"/fill_{0:06d}.root".format(i_fill), "RECREATE")
    f_out = ROOT.TFile("fill_{0:06d}.root".format(i_fill), "RECREATE")
    for directory_name, queries in NXCALS_VARIABLES.items() :
        f_out.mkdir(directory_name)
        f_out.cd(directory_name)

        for q, max_delta_time, scaling in queries :
            out_trees = {}
            out_vars = {}

            # Very long fills return larger-than-memory arrays. Make chunks of 12 hours, or shorter.
            time_chunks = []
            n_time_chunks = int((this_fill['endTime'] - this_fill['startTime'])/max_delta_time) + 1

            for i_chunk in range(n_time_chunks) :
                if this_fill['startTime'] + (i_chunk+1)*max_delta_time > this_fill['endTime'] :
                    time_chunks.append([this_fill['startTime'] + i_chunk*max_delta_time, this_fill['endTime']])
                else :
                    time_chunks.append([this_fill['startTime'] + i_chunk*max_delta_time, this_fill['startTime'] + (i_chunk+1)*max_delta_time])

            unix_timestamp = array.array('d', [0.])
            run_time = array.array('d', [0.])
            run_number_branch = array.array('i', [0])
            
            for i_chunk, [chunk_start, chunk_end] in enumerate(time_chunks) :
                if scaling == "last" :
                    data = ldb.get(q, chunk_end, "last", unixtime = True)
                else :
                    data = ldb.get(q, chunk_start - EPSILON, chunk_end - EPSILON, unixtime = True)


                for variable_name, d in data.items() :
                
                    print("[{0}/{1}] Processing {2}".format(i_chunk+1, n_time_chunks, variable_name))
                    if len(d[0]) == 0 :
                        print("No data, skipping.")
                        continue

                    print(d[0].shape, d[1].shape)
                    
                    if callable(scaling) :
                        d = scaling(d)
                    print(d[0].shape, d[1].shape)
                    
                    tree_name = variable_name.replace(":", "_").replace(".", "_")

                    if 'str' in d[1].dtype.name :
                        data_is_string = True
                    else :
                        data_is_string = False
                        try :
                            array_length = len(d[1][0])
                        except TypeError :
                            array_length = 1
                            
                    if tree_name not in out_trees :

                        out_trees[tree_name] = ROOT.TTree(tree_name, tree_name)
                        out_trees[tree_name].Branch("unix_timestamp", unix_timestamp, "unix_timestamp/D")
                
                        if not data_is_string :
                            out_vars[tree_name] = array.array('d', [0.]*array_length)
                            if array_length > 1 :
                                out_trees[tree_name].Branch("var", out_vars[tree_name], "var["+str(array_length)+"]/D")
                            else :
                                out_trees[tree_name].Branch("var", out_vars[tree_name], "var/D")
                        else :
                            out_vars[tree_name] = ROOT.std.string()
                            out_trees[tree_name].Branch("var", out_vars[tree_name])
                        
                        out_trees[tree_name].Branch("run_time", run_time, "run_time/D")    
                        
                        out_trees[tree_name].Branch("run_number", run_number_branch, "run_number/I")    
                
                    # Figure out run number and run time corresponding to each database entry
                    run_times = np.array([-1.]*len(d[0]))
                    run_numbers = np.array([-1]*len(d[0]))
                    
                    for raw_data_time in raw_data_times :
                        timestamps_after_run_start = d[0] > raw_data_time[1]
                        timestamps_before_run_end = d[0] < raw_data_time[2]
                
                        timestamps_in_run = np.logical_and(timestamps_after_run_start, timestamps_before_run_end)
                        
                        run_numbers[timestamps_in_run] = raw_data_time[0]
                        run_times[timestamps_in_run] = d[0][timestamps_in_run] - raw_data_time[1]
                
                    for i_data in range(len(d[0])) :
                        unix_timestamp[0] = d[0][i_data]
                        if not data_is_string :
                            if array_length == 1 :
                                out_vars[tree_name][0] = d[1][i_data]
                            else :
                                for i_element, element in enumerate(d[1][i_data]) :
                                    out_vars[tree_name][i_element] = element
                        else :
                            out_vars[tree_name].replace(0, ROOT.std.string.npos, d[1][i_data])    
                
                        run_time[0] = run_times[i_data]
                        run_number_branch[0] = run_numbers[i_data]
                
                        out_trees[tree_name].Fill()
                try :
                    del data
                except NameError :
                    pass

            for tree in out_trees.values() :
                tree.Write()
                    
    f_out.Close()
    os.system("k5start -f ~/.Authentication/cvilela.kt -u cvilela")
    os.system("xrdcp -v fill_{0:06d}.root {1}/fill_{0:06d}.root".format(i_fill, args.output_dir))
    os.system("rm fill_{0:06d}.root".format(i_fill))
    os.system("k5start -f ~/.Authentication/cristova.kt -u cristova")
