import os
import glob
import argparse
import tarfile

import ROOT
import numpy as np

import datetime

parser = argparse.ArgumentParser(description='Get luminosity from ATLAS and save to ROOT files')

parser.add_argument("-o", "--output_dir", type = str, help="Directory to store the ROOT files", required=True)
parser.add_argument("--atlas_dir", type = str, help = "Directory with ATLAS luminosity", default = "/eos/project/a/atlas-datasummary/public/lumifiles/{}/lumi/")
parser.add_argument("--raw_data_dirs", type = str, help="Directories with SND@LHC raw data", default="/eos/experiment/sndlhc/raw_data/physics/2022/,/eos/experiment/sndlhc/raw_data/physics/2023_reprocess_24/,/eos/experiment/sndlhc/raw_data/physics/2024/run_241/,/eos/experiment/sndlhc/raw_data/physics/2024/run_242/,/eos/experiment/sndlhc/raw_data/physics/2024/run_243/,/eos/experiment/sndlhc/raw_data/physics/2024/run_244/")


args = parser.parse_args()

FIRST_FILL=7920
FIRST_RUN=4362

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
        last_processed_run = int(f_temp.Get("atlas_lumi").GetMaximum("run_number"))
    except AttributeError :
        print("No beam mode data in previous fill, so processing files from the start")
        last_processed_run = FIRST_RUN
    f_temp.Close()
    del f_temp
except OSError :
    last_processed_run = FIRST_RUN

if last_processed_run <= 0 :
    last_processed_run = FIRST_RUN
    
print("Processing data fom run {0}".format(last_processed_run))

import snd_run_tools
rTools = snd_run_tools.runTools(args.raw_data_dirs, "/eos/experiment/sndlhc/convertedData/commissioning/TI18/RunInfodict.root")
raw_data_times = rTools.getRunTimes(last_processed_run)

last_run_end = max(raw_data_times[:,2])

os.makedirs(args.output_dir, exist_ok = True)

for year in range(2022, datetime.date.today().year+1) :
    for atlas_lumi_tgz in glob.glob(args.atlas_dir.format(year)+"/*.tgz") :
        
        fill_number = os.path.split(atlas_lumi_tgz)[-1][:-4]
    
        if os.path.isfile(args.output_dir+"/fill_00"+fill_number+".root") :
            continue

        print(fill_number)

        with tarfile.open(atlas_lumi_tgz, mode = "r:gz") as atlas_tar :
            tar_member = atlas_tar.getmember(fill_number+"/"+fill_number+"_lumi_ATLAS.txt")
            with atlas_tar.extractfile(tar_member) as f :
                data = np.genfromtxt(f, usecols = (0, 2))
    
                unix_timestamps = np.array(data[:,0])
                lumi = np.array(data[:,1])

                # Check if this fill ends after the most recent available run, in which case do not process it yet.
                if unix_timestamps[-1] > last_run_end :
                    print("Current fill end time ({0}) is after the last completed run end time ({1}). Skipping.".format(unix_timestamps[-1], last_run_end))
                    continue

                # Find runs belonging to this fill
#                run_starts_before_fill_end = raw_data_times[:,1] < unix_timestamps[1]
#                run_ends_after_fill_start = raw_data_times[:,2] > unix_timestamps[0]
    
#                runs_in_fill = raw_data_times[np.logical_and(run_starts_before_fill_end, run_ends_after_fill_start)]

                # Figure out run numbers and run time corresponding to each lumi reading
                run_times = np.array([-1.]*len(lumi))
                run_numbers = np.array([-1]*len(lumi))

                for raw_data_time in raw_data_times :
                    timestamps_after_run_start = unix_timestamps > raw_data_time[1]
                    timestamps_before_run_end = unix_timestamps < raw_data_time[2]

                    timestamps_in_run = np.logical_and(timestamps_after_run_start,
                                                       timestamps_before_run_end)

                    run_numbers[timestamps_in_run] = raw_data_time[0]
                    run_times[timestamps_in_run] = unix_timestamps[timestamps_in_run] - raw_data_time[1]
                
                
                rdf = ROOT.RDF.MakeNumpyDataFrame({"unix_timestamp" : unix_timestamps,
                                                   "var" : lumi,
                                                   "run_time" : run_times,
                                                   "run_number" : run_numbers})
    
                rdf.Snapshot('atlas_lumi', args.output_dir+"/fill_00"+fill_number+".root")
    
                del rdf
                del unix_timestamps
                del lumi
                del run_times
                del run_numbers
                del data
                
