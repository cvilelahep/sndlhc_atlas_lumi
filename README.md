# getATLASLumi.py
Gets the luminosity from NXCALS using pytimber (needs access permission). Inputs are run number (just for plot title and output file name), start date and end date. Produces a CSV file and optionally a plot.

# run_summary.csv
The list of runs that will be shown. Edited by hand. The last number is a pre-scale factor for muon reconstruction, which should be roughly inversely proportional to the integrated luminosity for the run.

# runReco.sh
This script will run the muon reconstruction for the runs in run_summary.csv.

# makeSummaryPlot.py
Produces the luminosity summary plots.
