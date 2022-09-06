import argparse
import ROOT

parser = argparse.ArgumentParser(description='Get luminosity from NXCALS and save to ROOT TTrees')

parser.add_argument("-o", "--output_dir", type = str, help="Directory to store the ROOT files", default="./")
parser.add_argument("start_time", type = str, help="Start time in Y-m-d H:M:S format")
parser.add_argument("end_time", type = str, help="Start time in Y-m-d H:M:S format")
parser.add_argument("--nxcals_variables", nargs='+', default=[], help="List of nxcals variables to extract")

args = parser.parse_args()

import pytimber

ldb = pytimber.LoggingDB(source="nxcals")

for variable in args.nxcals_variables :
    
    fetched_data = ldb.get(variable, args.start_time, args.end_time, unixtime=True)
    
    print(fetched_data)
