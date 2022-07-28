import argparse
import datetime
import numpy as np
import matplotlib.pyplot as plt
import csv
import gc

import lumi_tools

#from memory_profiler import profile

import ROOT

# Which runs have a reco file
runs_with_reco = [0, 1]#, 2, 3, 4, 5, 6, 7, 8]

rate_label = r"Single-track events with $|\theta_{\mathrm{I.P.}}| < 0.1 \, \mathrm{rad}$"
rate_bin_width = 500 # in milliseconds

logo_location = "/afs/cern.ch/user/c/cvilela/Large__SND_Logo_blue.png"

converted_runs_location = "/eos/experiment/sndlhc/convertedData/commissioning/TI18/"
reconstructed_runs_location = "/afs/cern.ch/work/c/cvilela/private/tempRecoJul18/"
lumi_file = "/afs/cern.ch/user/c/cvilela/sndlhc_atlas_lumi/sndlhc_atlas_lumi_0000.csv"

color_inst = 'navy'
color_integrated = 'chocolate'
color_run_band = 'royalblue'
muon_rate_color = 'black'
total_rate_color = 'tab:gray'


def recalc_integrated(data) :
    # assume first dt is the same as second dt
    last_t = data[0]['timestamp'] - (data[1]['timestamp'] - data[0]['timestamp'])

    this_integrated_lumi = 0
    integrated_lumi = []

    for d in data :
        this_integrated_lumi += d['inst_lumi']*(d['timestamp']-last_t)/np.timedelta64(1, 's')/1.e6
        integrated_lumi.append(this_integrated_lumi)
        last_t = d['timestamp']
    return np.array(integrated_lumi)

def draw_inst(data, axis, color, mask = None) :
    axis.set_ylabel('Instantaneous luminosity [$\mu$b$^{-1}$s$^{-1}$]', color=color)
    axis.tick_params(axis='y', labelcolor=color)
    if mask is not None :
        axis.plot(data[mask]['timestamp'], data[mask]['inst_lumi'], label = "Instantaneous luminosity", color = color)
    else :
        axis.plot(data['timestamp'], data['inst_lumi'], label = "Instantaneous luminosity", color = color)
    axis.set_ylim(0, axis.get_ylim()[1]*1.2)


def draw_integrated(data, axis, color, mask = None) :
    axis.set_ylabel('Integrated luminosity [pb$^{-1}$]', color=color)
    if mask is not None :
        axis.plot(data[mask]['timestamp'], recalc_integrated(data[mask]), label = "Integrated luminosity", color = color)
    else :
        axis.plot(data['timestamp'], recalc_integrated(data), label = "Integrated luminosity", color = color)
    axis.tick_params(axis='y', labelcolor=color)
    axis.set_ylim(0, axis.get_ylim()[1]*1.2)

def draw_sndlhcruns(data, axis) :
    y_range = axis.get_ylim()

    max_run_length = np.timedelta64(0, "s")
    for run in data :
        if (run[2]-run[1]) > max_run_length :
            max_run_length = run[2]-run[1]
    for run in data :
        axis.fill( [run[1], run[2], run[2], run[1]], [0., 0., y_range[1], y_range[1]], color = color_run_band, alpha = 0.1, edgecolor = None)
        if (run[2] - run[1])*2.0 < max_run_length :
            continue
        axis.text( run[1]+(run[2]-run[1])/2, y = 0.8*y_range[1], s = "Run\n{0}".format(run[0]), ha = 'center')

#@profile
def getMuonEvents(runNumber, run_start) :
    data= ROOT.TChain("rawConv")
    data.SetAutoDelete(True)
    data.Add(converted_runs_location+"/run_00{0}/sndsw_raw-000[0-9].root".format(runNumber))
    reco = ROOT.TChain("rawConv")
    # Reco TChain leaks memory, for some reason
    
    reco.SetAutoDelete(True)
    reco.Add(reconstructed_runs_location+"/run_00{0}/sndsw_raw-000[0-9]_muonReco.root".format(runNumber))

    ipMuon_timestamps = []
    all_timestamps = []
    for i_event in range(data.GetEntries()) :
        reco.GetEntry(i_event)
        data.GetEntry(i_event)
        
        all_timestamps.append(run_start + np.timedelta64(int(data.EventHeader.GetEventTime()*6.25), "ns"))
        
        if len(reco.Reco_MuonTracks) != 1 :
            continue

        mom = reco.Reco_MuonTracks.At(0).getFittedState().getMom()

        thetaz = np.arctan2((mom.X()**2 + mom.Y()**2)**0.5, mom.Z())

        if abs(thetaz) > 0.1 :
            continue

        ipMuon_timestamps.append(run_start + np.timedelta64(int(data.EventHeader.GetEventTime()*6.25), "ns"))
    del data
    del reco
    return ipMuon_timestamps, all_timestamps
        
def addLogo(fig) :

    try :
        im = plt.imread(logo_location)
        newax = fig.add_axes([0.125,0.2,0.175,0.175], anchor='NW', zorder=100)
        newax.imshow(im)
        newax.axis('off')
    except :
        print("Error getting logo")
        pass
            
def main(lumi_path, plot_rate = False) :
    runs = np.genfromtxt('run_summary.csv', delimiter=',', dtype=[('run_number', 'i4'), ('start_time', 'datetime64[ms]'), ('end_time', 'datetime64[ms]'), ('reco_prescale_factor', int)])

    lumi = lumi_tools.getLumi(lumi_path)
    
    fig_no_rate, ax_inst_no_rate = plt.subplots(figsize = (10, 5))
    addLogo(fig_no_rate)
    draw_inst(lumi, ax_inst_no_rate, color_inst)
    ax_integrated_no_rate = ax_inst_no_rate.twinx()
    draw_integrated(lumi, ax_integrated_no_rate, color_integrated)
    
    draw_sndlhcruns(runs, ax_inst_no_rate)
    
    ax_inst_no_rate.set_title("LHC Run 3")
    
    fig_name = "sndlhc_lumi"
    
    plt.savefig(fig_name+".png", dpi=300)
    plt.savefig(fig_name+".pdf", dpi=300)
    
    plt.draw()
    plt.clf()
    plt.close("all")
    plt.close()
    gc.collect()
    print("Plotted no rate")
 
    if not plot_rate :
        return
    
    if len(runs_with_reco) :
        fig, (ax_inst, ax_totrate) = plt.subplots(figsize = (10, 5), nrows = 2, sharex = True)
    
        addLogo(fig)
        
        draw_inst(lumi, ax_inst, color_inst, ~badlumi)
        ax_integrated = ax_inst.twinx()
        draw_integrated(lumi, ax_integrated, color_integrated, ~badlumi)
    
        draw_sndlhcruns(runs, ax_inst)
    
        ax_inst.set_title("LHC Run 3")
    
        ax_murate = ax_totrate.twinx()
        
        for this_i_run, i_run in enumerate(runs_with_reco) :
        
            nbins = int((runs[i_run][2]-runs[i_run][1])/np.timedelta64(rate_bin_width, 's'))
            bin_width = (runs[i_run][2]-runs[i_run][1])/np.timedelta64(1, 's')/nbins
    
            ip_muons, all_events = getMuonEvents(runs[i_run][0], runs[i_run][1])
    
    
            if this_i_run :
                n, bins, _ = ax_totrate.hist(all_events, bins = nbins, range = (runs[i_run][1], runs[i_run][2]), histtype = "step", color = total_rate_color, weights = [1./bin_width]*len(all_events))
            else :
               n, bins, _ = ax_totrate.hist(all_events, bins = nbins, range = (runs[i_run][1], runs[i_run][2]), histtype = "step", color = total_rate_color, weights = [1./bin_width]*len(all_events), label = "All events")     
            err = np.sqrt(n*bin_width)/bin_width
            x = (bins[:-1] + bins[1:])/2
            ax_totrate.errorbar(x, n, yerr = err, color = total_rate_color, fmt = 'none')
    
            if this_i_run :
                n, bins, _ = ax_murate.hist(ip_muons, bins = nbins, range = (runs[i_run][1], runs[i_run][2]), histtype = "step", color = muon_rate_color, weights = [1.*runs[i_run]['reco_prescale_factor']/bin_width]*len(ip_muons))
            else :
                n, bins, _ = ax_murate.hist(ip_muons, bins = nbins, range = (runs[i_run][1], runs[i_run][2]), histtype = "step", color = muon_rate_color, weights = [1.*runs[i_run]['reco_prescale_factor']/bin_width]*len(ip_muons), label = rate_label)
            err = np.sqrt(n*bin_width/runs[i_run]['reco_prescale_factor'])/bin_width*runs[i_run]['reco_prescale_factor']
            x = (bins[:-1] + bins[1:])/2
            ax_murate.errorbar(x, n, yerr = err, color = muon_rate_color, fmt = 'none')
    
            if not this_i_run :
                ax_totrate.legend(loc = 'upper left')
                ax_murate.legend(loc = 'upper right')
                
            del ip_muons
            del all_events
            
        ax_totrate.tick_params(axis='y', labelcolor=total_rate_color)
        ax_murate.tick_params(axis='y', labelcolor=muon_rate_color)
        ax_murate.set_xlabel("Date")
        ax_murate.set_ylim((0, ax_murate.get_ylim()[1]*1.1))
        ax_totrate.set_ylim((0, ax_totrate.get_ylim()[1]*1.1))
    
        ax_murate.set_ylabel(r"Event rate [s$^{-1}$]", color = muon_rate_color)
        ax_totrate.set_ylabel(r"Event rate [s$^{-1}$]", color = total_rate_color)
        
        fig_name += "_rate"
    
        plt.savefig(fig_name+".png", dpi=300)
        plt.savefig(fig_name+".pdf", dpi=300)
    
        plt.draw()
        plt.clf()
        plt.close("all")
        plt.close()
        gc.collect()
    
        print("Plotted with rate")
        
        proc_min = np.min(runs[runs_with_reco]["start_time"])
        proc_max = np.max(runs[runs_with_reco]["end_time"])
    
        sub_intervals = [["proconly", runs_with_reco, proc_min, proc_max]]
    
        for i_run in runs_with_reco :
            sub_intervals.append([str(runs[i_run]["run_number"]), [i_run], runs[i_run]['start_time'], runs[i_run]['end_time']])
        
        for interval in sub_intervals :
            mask = np.logical_and(~badlumi, lumi['timestamp'] > interval[2])
            mask = np.logical_and(mask, lumi['timestamp'] < interval[3])
        
            fig_proconly, (ax_inst_proconly, ax_totrate_proconly) = plt.subplots(figsize = (10, 5), nrows = 2, sharex = True)
    
            addLogo(fig_proconly)
            
            draw_inst(lumi, ax_inst_proconly, color_inst, mask)
            ax_integrated_proconly = ax_inst_proconly.twinx()
            draw_integrated(lumi, ax_integrated_proconly, color_integrated, mask)
    
            draw_sndlhcruns(runs[interval[1]], ax_inst_proconly)
    
            ax_murate_proconly = ax_totrate_proconly.twinx()
            
            ax_inst_proconly.set_title("LHC Run 3")
            
            for this_i_run, i_run in enumerate(interval[1]) :
        
                nbins = int((runs[i_run][2]-runs[i_run][1])/np.timedelta64(rate_bin_width, 's'))
                bin_width = (runs[i_run][2]-runs[i_run][1])/np.timedelta64(1, 's')/nbins
                
                ip_muons, all_events = getMuonEvents(runs[i_run][0], runs[i_run][1])
    
                if this_i_run :
                    n, bins, _ = ax_totrate_proconly.hist(all_events, bins = nbins, range = (runs[i_run][1], runs[i_run][2]), histtype = "step", color = total_rate_color, weights = [1./bin_width]*len(all_events))
                else :
                    n, bins, _ = ax_totrate_proconly.hist(all_events, bins = nbins, range = (runs[i_run][1], runs[i_run][2]), histtype = "step", color = total_rate_color, weights = [1./bin_width]*len(all_events), label = "All events")
                err = np.sqrt(n*bin_width)/bin_width
                x = (bins[:-1] + bins[1:])/2
                ax_totrate_proconly.errorbar(x, n, yerr = err, color = total_rate_color, fmt = 'none')
    
                if this_i_run :
                    n, bins, _ = ax_murate_proconly.hist(ip_muons, bins = nbins, range = (runs[i_run][1], runs[i_run][2]), histtype = "step", color = muon_rate_color, weights = [1.*runs[i_run]["reco_prescale_factor"]/bin_width]*len(ip_muons))
                else :
                    n, bins, _ = ax_murate_proconly.hist(ip_muons, bins = nbins, range = (runs[i_run][1], runs[i_run][2]), histtype = "step", color = muon_rate_color, weights = [1.*runs[i_run]["reco_prescale_factor"]/bin_width]*len(ip_muons), label = rate_label)
                err = np.sqrt(n*bin_width/runs[i_run]["reco_prescale_factor"])/bin_width*runs[i_run]["reco_prescale_factor"]
                x = (bins[:-1] + bins[1:])/2
                ax_murate_proconly.errorbar(x, n, yerr = err, fmt = 'none', color = muon_rate_color)
                
                if not this_i_run :
                    ax_totrate_proconly.legend(loc = 'upper left')
                    ax_murate_proconly.legend(loc = 'upper right')
    
                del ip_muons
                del all_events
                
            ax_murate_proconly.tick_params(axis='y', labelcolor=muon_rate_color)
            ax_totrate_proconly.tick_params(axis='y', labelcolor=total_rate_color)
            ax_murate_proconly.set_xlabel("Date")
            ax_murate_proconly.set_ylim((0, ax_murate_proconly.get_ylim()[1]*1.1))
            ax_totrate_proconly.set_ylim((0, ax_totrate_proconly.get_ylim()[1]*1.1))
            ax_murate_proconly.set_ylabel(r"Event rate [s$^{-1}$]", color = muon_rate_color)
            ax_totrate_proconly.set_ylabel(r"Event rate [s$^{-1}$]", color = total_rate_color)
            
            plt.savefig(fig_name+"_"+interval[0]+".png", dpi=300)
            plt.savefig(fig_name+"_"+interval[0]+".pdf", dpi=300)
            print("Plotted with rate sub {0}".format(interval[0]))
    
            plt.draw()
            plt.clf()
            plt.close("all")
            plt.close()
            gc.collect()

if __name__ == "__main__" :
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--lumi_path", dest="lumi_path", help="Path to csv files containing ATLAS luminosity", required=True)
    options = parser.parse_args()

    

    main(options.lumi_path)
