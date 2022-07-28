import lumi_tools
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--lumi_path", dest="lumi_path", help="Path to csv files containing ATLAS luminosity", required=True)
parser.add_argument("-f", "--run_summary_file", dest="run_summary_file", help="Path to run_summary_file", required=True)
options = parser.parse_args()

lumi = lumi_tools.getLumi(options.lumi_path)

runs = np.genfromtxt('run_summary.csv', delimiter=',', dtype=[('run_number', 'i4'), ('start_time', 'datetime64[ms]'), ('end_time', 'datetime64[ms]'), ('reco_prescale_factor', int)])
