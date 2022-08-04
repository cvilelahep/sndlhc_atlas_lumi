import glob
import numpy as np

def getLumi(lumi_path) :
    lumi_files = glob.glob(lumi_path+"/sndlhc_atlas_lumi_*.csv")
    lumi = []
    for lumi_file in lumi_files :
        lumi.append(np.genfromtxt(lumi_file, delimiter=',', skip_header=1, dtype=[('timestamp', 'datetime64[ms]'),  ('inst_lumi', 'f4')]))
    lumi = np.concatenate(lumi)
    return lumi
