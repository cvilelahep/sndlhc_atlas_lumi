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
parser.add_argument("--raw_data_dir", type = str, help="Directory with SND@LHC raw data", default="/eos/experiment/sndlhc/raw_data/commissioning/TI18/data/")

args = parser.parse_args()


NXCALS_VARIABLES = {}
NXCALS_VARIABLES["LuminosityIP1"] = ["ATLAS:LUMI_TOT_INST",
                                     "ATLAS:BUNCH_LUMI_INST",
                                     "ATLAS.OFFLINE:LUMI_TOT_INST",
                                     "ATLAS.OFFLINE:BUNCH_LUMI_INST",
                                     "LHC.BRAND.1R:LuminosityBunchSum:totalLuminosityBunchSum",
                                     "LHC.BRANA.4L1:TOTAL_LUMINOSITY",
                                     "LHC.BRANA.4L1:LUMINOSITY_Q1",
                                     "LHC.BRANA.4L1:LUMINOSITY_Q2",
                                     "LHC.BRANA.4L1:LUMINOSITY_Q3",
                                     "LHC.BRANA.4L1:LUMINOSITY_Q4"]

NXCALS_VARIABLES["LuminosityOtherIPs"] = ["CMS:LUMI_TOT_INST",
                                          "CMS.OFFLINE:LUMI_TOT_INST",
                                          "LHCB:LUMI_TOT_INST",
                                          "ALICE:LUMI_TOT_INST"]

NXCALS_VARIABLES["LHC"] = ["HX:BMODE",
                           "LHC.STATS:LHC:INJECTION_SCHEME",
                           "HX:BETASTAR_IP1"]

NXCALS_VARIABLES["AutomaticScans"] = ["LHC.LUMISERVER:AutomaticScanIP%:Nominal%"]

NXCALS_VARIABLES["CollimatorSettingsIP1"] =  ["TCL.%1.B%:SET_%",
                                              "TCTP%.%1.%:SET_%"]

FIRST_FILL=7920
FIRST_RUN=4362

EPSILON = 1e-6 # To avoid rounding trouble. Look for database entries starting 1 ms before the start of the fill.

def getRunDuration(run_dir) :
    last_file = glob.glob(args.raw_data_dir+"/"+run_dir+"/data_*")[-1]
    try :
        f = ROOT.TFile(last_file)
    except OSError :
        print("Couldn't read {0}. Skipping this run...".format(last_file))
        return -1
    if hasattr(f, "event") :
        f.event.GetEntry(f.event.GetEntries()-1)
        return f.event.timestamp/0.160316/1e9
    else :
        f.data.GetEntry(f.data.GetEntries()-1)
        return f.data.evt_timestamp/0.160316/1e9
    f.Close()

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
        last_processed_run = int(f_temp.Get("LHC/"+NXCALS_VARIABLES["LHC"][0].replace(":", "_").replace(".", "_")).GetMaximum("run_number"))
    except AttributeError :
        print("No beam mode data in previous fill, so processing files from the start")
        last_processed_run = FIRST_RUN
except OSError :
    last_processed_run = FIRST_RUN

if last_processed_run <= 0 :
    last_processed_run = FIRST_RUN

processed_raw_data = next(os.walk(args.raw_data_dir))[1]

print("Processing data fom run {0}".format(last_processed_run))

raw_data_times = []
for run_dir in processed_raw_data :
    if not run_dir.startswith("run_") :
        continue

    run_number = int(run_dir.split("_")[1])

    if run_number < last_processed_run :
        continue
    
    try :
        with open(args.raw_data_dir+"/"+run_dir+"/run_timestamps.json", "r") as f_run_timestamps :
            run_timestamps = json.load(f_run_timestamps)
            if "Z" in run_timestamps["start_time"] :
                run_timezone = pytz.timezone("UTC")
            else :
                run_timezone = pytz.timezone("Europe/Zurich")

            run_start = dateutil.parser.isoparse(run_timestamps["start_time"])
            try :
                run_start = run_timezone.localize(run_start)
            except ValueError :
                pass

            try :
                run_stop = dateutil.parser.isoparse(run_timestamps["stop_time"])
                try :
                    run_stop = run_timezone.localize(run_stop)
                except ValueError :
                    pass
            except KeyError :
                run_duration = getRunDuration(run_dir)
                if run_duration < 0 :
                    continue
                run_stop = run_start + datetime.timedelta(seconds = run_duration)
                
    except FileNotFoundError :
        with open("/eos/experiment/sndlhc/convertedData/commissioning/TI18/RunInfodict.pkl", "rb") as f_run_dict :
            run_dict = pickle.load(f_run_dict)
            if run_number not in run_dict :
                print("Couldn't find run {0} timestamps in raw_data directory nor in RunInfodict.pkl".format(run_number))
                continue
            else :
                run_start = datetime.datetime.utcfromtimestamp(run_dict[run_number]["StartTime"])
                run_duration = getRunDuration(run_dir)
                if run_duration < 0 :
                    continue
                run_stop = run_start + datetime.timedelta(seconds = run_duration)
    raw_data_times.append([run_number, time.mktime(run_start.timetuple()), time.mktime(run_stop.timetuple())])

raw_data_times = np.array(raw_data_times)

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

    # First, check if the fill ends before the end of the last available run. If not, do not process it yet.
    if this_fill['endTime'] > last_run_end :
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

        for q in queries :
            data = ldb.get(q, this_fill['startTime'] - EPSILON, this_fill['endTime'], unixtime = True)
            
            for variable_name, d in data.items() :

                print("Processing {0}".format(variable_name))
                if len(d[0]) == 0 :
                    print("No data, skipping.")
                    continue

                if 'str' in d[1].dtype.name :
                    data_is_string = True
                else :
                    data_is_string = False
                    try :
                        array_length = len(d[1][0])
                    except TypeError :
                        array_length = 1
                
                tree_name = variable_name.replace(":", "_").replace(".", "_")
                out_tree = ROOT.TTree(tree_name, tree_name)

                unix_timestamp = array.array('d', [0.])
                out_tree.Branch("unix_timestamp", unix_timestamp, "unix_timestamp/D")

                if not data_is_string :
                    var = array.array('d', [0.]*array_length)
                    if array_length > 1 :
                        out_tree.Branch("var", var, "var["+str(array_length)+"]/D")
                    else :
                        out_tree.Branch("var", var, "var/D")
                else :
                    var = ROOT.std.string()
                    out_tree.Branch("var", var)

                run_time = array.array('d', [0.])
                out_tree.Branch("run_time", run_time, "run_time/D")    

                run_number_branch = array.array('i', [0])
                out_tree.Branch("run_number", run_number_branch, "run_number/I")    

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
                            var[0] = d[1][i_data]
                        else :
                            for i_element, element in enumerate(d[1][i_data]) :
                                var[i_element] = element
                    else :
                        var.replace(0, ROOT.std.string.npos, d[1][i_data])    

                    run_time[0] = run_times[i_data]
                    run_number_branch[0] = run_numbers[i_data]

                    out_tree.Fill()
                out_tree.Write()
        
    f_out.Close()
    os.system("k5start -f ~/.Authentication/cvilela.kt -u cvilela")
    os.system("xrdcp -v fill_{0:06d}.root {1}/fill_{0:06d}.root".format(i_fill, args.output_dir))
    os.system("rm fill_{0:06d}.root".format(i_fill))
    os.system("k5start -f ~/.Authentication/cristova.kt -u cristova")
