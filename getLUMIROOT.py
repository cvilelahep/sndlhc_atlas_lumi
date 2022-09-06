import argparse
import array
import ROOT

import time
import datetime

parser = argparse.ArgumentParser(description='Get luminosity from NXCALS and save to ROOT TTrees')

parser.add_argument("-o", "--output_dir", type = str, help="Directory to store the ROOT files", default="./")
parser.add_argument("start_time", type = str, help="Start time in Y-m-d H:M:S format")
parser.add_argument("end_time", type = str, help="Start time in Y-m-d H:M:S format")
parser.add_argument("--nxcals_variables", nargs='+', default=[], help="List of nxcals variables to extract")

args = parser.parse_args()

import pytimber

ldb = pytimber.LoggingDB(source="nxcals")

run_start_unix = time.mktime(datetime.datetime.strptime(args.start_time, "%Y-%m-%d %H:%M:%S").timetuple())

for variable in args.nxcals_variables :
    print("Getting {0}".format(variable))
    
    fetched_data = ldb.get(variable, args.start_time, args.end_time, unixtime=True)

    if len(fetched_data[variable][0]) < 2 :
        continue

    if fetched_data[variable][1].dtype == '<U8' :
        data_is_string = True
    else :
        data_is_string = False

    out_file = ROOT.TFile(args.output_dir+"/"+variable.replace(":", ".")+".root", "RECREATE")
    out_tree = ROOT.TTree("sndlhc_lumi", "NXCALS Luminosity for SND@LHC")

    unix_timestamp = array.array('d', [0.])
    out_tree.Branch("unix_timestamp", unix_timestamp, "unix_timestamp/D")
    if not data_is_string :
        var = array.array('d', [0.])
        out_tree.Branch("var", var, "var/D")
    else :
        var = ROOT.std.string()
        out_tree.Branch("var", var)

    run_time = array.array('d', [0.])
    out_tree.Branch("run_time", run_time, "run_time/D")    

    for entry in range(len(fetched_data[variable][0])) :
        unix_timestamp[0] = fetched_data[variable][0][entry]
        if not data_is_string :
            var[0] = fetched_data[variable][1][entry]
        else :
            var.replace(0, ROOT.std.string.npos, fetched_data[variable][1][entry])

        run_time[0] = unix_timestamp[0] - run_start_unix
        out_tree.Fill()

    out_tree.Write()
    out_file.Close()
