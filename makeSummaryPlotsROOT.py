import argparse
import ROOT

ROOT.gROOT.SetBatch()
ROOT.gStyle.SetOptStat(0)

import glob
import os

parser = argparse.ArgumentParser(description='Luminosity summary plots for SND@LHC run')

parser.add_argument("--raw_data_dir", type = str, help="Raw data directory", required = True)
parser.add_argument("--lumi_dir", type = str, help="Luminosity directory", required = True)
parser.add_argument("-o", "--output_dir", type = str, help="Directory to store the output ROOT files", default="./")

args = parser.parse_args()

BIN_WIDTH = 1 # Bin width in seconds.
LUMI_SCALE = 4.5 # Scale to roughly normalize luminosity (in nb-1 s-1) to SND@LHC event rate.

LIN_PLOT_MAX_SCALE = 2 # Set linear scale plots to this times the event rate maximum
LOG_PLOT_MAX_SCALE = 1000

LOG_SCALE_MIN = 0.001

data_files = glob.glob(args.raw_data_dir+"/data_*.root")

f = ROOT.TFile(data_files[0])

if hasattr(f, "event") :
    tree_name = "event"
    branch_name = "timestamp"
elif hasattr(f, "data") :
    tree_name = "data"
    branch_name = "evt_timestamp"
else :
    print("Data file not valid. Exitting.")
    exit(-1)

del f

events = ROOT.TChain(tree_name)
for f in data_files :
    events.Add(f)

events.GetEntry(events.GetEntries()-1)
last_time = getattr(events, branch_name)*6.25/1e9

n_bins = int(last_time/BIN_WIDTH)+1

out_file = ROOT.TFile(args.output_dir+"/lumi_plots.root", "RECREATE")

out_file.mkdir("Histograms")
out_file.cd("/Histograms")

events.Draw(branch_name+"*6.25/1e9>>h_event_rate("+str(n_bins)+", 0, "+str(n_bins*BIN_WIDTH)+")", "1./"+str(BIN_WIDTH), "goff")
h_event_rate = ROOT.gDirectory.Get("h_event_rate")
h_event_rate.SetTitle(";Run time [s];Event rate [s^{-1}]")
h_event_rate.Write()

ATLAS_lumi_summary = [["ATLAS.LUMI_TOT_INST", "ATLAS", ROOT.kOrange+1],
                      ["ATLAS.OFFLINE.LUMI_TOT_INST", "ATLAS (offline)", ROOT.kViolet-2]]

BRAN_lumi_summary = [ ["LHC.BRANA.4L1.TOTAL_LUMINOSITY", "BRAN A 4L1 (left of ATLAS)", ROOT.kAzure+5],
                      ["LHC.BRANA.4L1.LUMINOSITY_Q1", "BRAN A 4L1 Q1", ROOT.kOrange+1],
                      ["LHC.BRANA.4L1.LUMINOSITY_Q2", "BRAN A 4L1 Q2", ROOT.kViolet-2],
                      ["LHC.BRANA.4L1.LUMINOSITY_Q3", "BRAN A 4L1 Q3", ROOT.kCyan-3],
                      ["LHC.BRANA.4L1.LUMINOSITY_Q4", "BRAN A 4L1 Q4", ROOT.kRed-3],
                      ["LHC.BRAND.1R.LuminosityBunchSum.totalLuminosityBunchSum", "BRAN D 1R (right of ATLAS)", ROOT.kSpring-6]]

other_lumi_summary = [["ALICE.LUMI_TOT_INST", "ALICE", ROOT.kOrange+1],
                      ["LHCB.LUMI_TOT_INST", "LHCb", ROOT.kCyan-3],
                      ["CMS.LUMI_TOT_INST", "CMS", ROOT.kViolet-2]]

beam_mode_strings = []
beam_mode_times = []

f_beam_modes = ROOT.TFile(args.lumi_dir+"/HX.BMODE.root")
for entry in f_beam_modes.sndlhc_lumi :
    beam_mode_strings.append(str(entry.var))
    beam_mode_times.append(entry.run_time)

print(beam_mode_strings)
print(beam_mode_times)

canvi = []
canvi_log = []
canvi_ratios = []
legi = []

evt_rate_maximum = h_event_rate.GetMaximum()

mode_lines = []
mode_texts = []

for i_mode in range(len(beam_mode_strings)) :
    mode_lines.append(ROOT.TLine(beam_mode_times[i_mode], -0.1,
                                  beam_mode_times[i_mode], 3./4*LIN_PLOT_MAX_SCALE*evt_rate_maximum))
    mode_lines[-1].SetLineStyle(2)
    mode_lines[-1].SetLineColor(ROOT.kGray)
    mode_lines[-1].Draw()

    print(beam_mode_strings[i_mode])
    mode_texts.append(ROOT.TText(beam_mode_times[i_mode], 3./4*LIN_PLOT_MAX_SCALE*evt_rate_maximum - 0.05*evt_rate_maximum*(i_mode%4), beam_mode_strings[i_mode]))
    mode_texts[-1].SetTextAngle(60)
    mode_texts[-1].SetTextSize(0.02)
    mode_texts[-1].SetTextFont(82)
    mode_texts[-1].SetTextAlign(22)

mode_lines_log = []
mode_texts_log = []

for i_mode in range(len(beam_mode_strings)) :
    mode_lines_log.append(ROOT.TLine(beam_mode_times[i_mode], LOG_SCALE_MIN,
                                  beam_mode_times[i_mode], LOG_PLOT_MAX_SCALE/100*evt_rate_maximum))
    mode_lines_log[-1].SetLineStyle(2)
    mode_lines_log[-1].SetLineColor(ROOT.kGray)
    mode_lines_log[-1].Draw()

    print(beam_mode_strings[i_mode])
    mode_texts_log.append(ROOT.TText(beam_mode_times[i_mode], LOG_PLOT_MAX_SCALE/100*evt_rate_maximum*(0.5**(i_mode%4)), beam_mode_strings[i_mode]))
    mode_texts_log[-1].SetTextAngle(60)
    mode_texts_log[-1].SetTextSize(0.02)
    mode_texts_log[-1].SetTextFont(82)
    mode_texts_log[-1].SetTextAlign(22)

for c_name, data_list in [["evt_rate_ATLAS_lumi_summary", ATLAS_lumi_summary],
                          ["evt_rate_BRAN_IP1_lumi_summary", BRAN_lumi_summary],
                          ["evt_rate_other_IPs_lumi_summary", other_lumi_summary]]:

    if len(data_list) == 0 :
        continue
        
    canvi.append(ROOT.TCanvas(c_name))
    h_event_rate.SetMaximum(LIN_PLOT_MAX_SCALE*evt_rate_maximum)
    h_event_rate.SetMinimum(-0.1)
    h_event_rate.DrawCopy()

    canvi_log.append(ROOT.TCanvas(c_name+"_log"))
    h_event_rate.SetMaximum(LOG_PLOT_MAX_SCALE*evt_rate_maximum)
    h_event_rate.SetMinimum(LOG_SCALE_MIN)
    h_event_rate.DrawCopy()
    canvi_log[-1].SetLogy()

    canvi_ratios.append(ROOT.TCanvas(c_name+"_ratios"))
    h_base = h_event_rate.Clone("h_base")
    h_base.Reset()
    h_base.SetMaximum(LUMI_SCALE*2)
    h_base.SetTitle(";Run time [s];Instantaneous luminosity / event rate [#mub]")
    h_base.Draw("HIST")


    legi.append(ROOT.TLegend(0.1, 0.75, 0.9, 0.9))
    legi[-1].SetNColumns(2)
    legi[-1].AddEntry(h_event_rate, "SND@LHC Event rate", "l")

    for l in data_list :
        if os.path.exists(args.lumi_dir+"/"+l[0]+".root") :
            f_lumi = ROOT.TFile(args.lumi_dir+"/"+l[0]+".root")
        
            out_file.cd("/Histograms")
            
            if f_lumi.sndlhc_lumi.GetEntries() > 2*n_bins :
                this_n_bins = n_bins
                this_bin_width = BIN_WIDTH
            else :
                this_n_bins = int(f_lumi.sndlhc_lumi.GetEntries()/2.)
                this_bin_width = BIN_WIDTH*(n_bins/float(this_n_bins))
            
            f_lumi.sndlhc_lumi.Draw("run_time>>h_"+l[0]+"("+str(this_n_bins)+", 0, "+str(this_n_bins*this_bin_width)+")", "var", "goff")
            f_lumi.sndlhc_lumi.Draw("run_time>>denom_"+l[0]+"("+str(this_n_bins)+", 0, "+str(this_n_bins*this_bin_width)+")", "", "goff")
            
            h_lumi = ROOT.gDirectory.Get("h_"+l[0])
            h_lumi.Divide(ROOT.gDirectory.Get("denom_"+l[0]))
            
            h_lumi.SetLineColor(l[2])
            h_lumi.SetTitle(l[1])
            
            h_lumi.Write()

            h_ratio = h_lumi.Clone("h_"+l[0]+"_ratio")
            for i_bin in range(1, h_ratio.GetNbinsX() + 1) :
                if h_event_rate.GetBinContent(h_event_rate.FindBin(h_ratio.GetBinCenter(i_bin))) > 0 :
                    h_ratio.SetBinContent(i_bin, h_ratio.GetBinContent(i_bin)/h_event_rate.GetBinContent(h_event_rate.FindBin(h_ratio.GetBinCenter(i_bin))))
                else :
                    h_ratio.SetBinContent(i_bin, 0)

            h_lumi.Scale(1./LUMI_SCALE)
            
            canvi[-1].cd()
            h_lumi.Draw("SAMEHIST")

            canvi_log[-1].cd()
            h_lumi.Draw("SAMEHIST")

            canvi_ratios[-1].cd()
            h_ratio.DrawCopy("SAMEHIST")
            
            legi[-1].AddEntry(h_lumi, l[1], "l")
            
            f_lumi.Close()

    canvi[-1].cd()
    canvi[-1].Update()

    for line in mode_lines :
        line.Draw()

    for text in mode_texts :
        text.Draw()

    lumi_axis = ROOT.TGaxis(canvi[-1].GetUxmax(), canvi[-1].GetUymin(), canvi[-1].GetUxmax(), canvi[-1].GetUymax(), canvi_log[-1].GetUymin()*LUMI_SCALE/1000., canvi[-1].GetUymax()*LUMI_SCALE/1000., 510, "+L")
    lumi_axis.SetTextFont(ROOT.gStyle.GetTextFont())
    lumi_axis.SetLabelFont(ROOT.gStyle.GetLabelFont("Y"))
    lumi_axis.SetTitleFont(ROOT.gStyle.GetTitleFont("Y"))
    lumi_axis.SetTitle("Instantaneous luminosity [nb^{-1}s^{-1}]")
    lumi_axis.Draw()
    legi[-1].Draw()
    out_file.cd()
    canvi[-1].Write()

    canvi_log[-1].cd()
    canvi_log[-1].Update()

    for line in mode_lines_log :
        line.Draw()

    for text in mode_texts_log :
        text.Draw()

    lumi_axis_log = ROOT.TGaxis(canvi_log[-1].GetUxmax(), LOG_SCALE_MIN, canvi_log[-1].GetUxmax(), LOG_PLOT_MAX_SCALE*evt_rate_maximum, LOG_SCALE_MIN*LUMI_SCALE/1000., LOG_PLOT_MAX_SCALE*evt_rate_maximum*LUMI_SCALE/1000., 510, "+LG")
    lumi_axis_log.SetTextFont(ROOT.gStyle.GetTextFont())
    lumi_axis_log.SetLabelFont(ROOT.gStyle.GetLabelFont("Y"))
    lumi_axis_log.SetTitleFont(ROOT.gStyle.GetTitleFont("Y"))
    lumi_axis_log.SetTitle("Instantaneous luminosity [nb^{-1}s^{-1}]")
    lumi_axis_log.Draw()
    legi[-1].Draw()
    out_file.cd()
    canvi_log[-1].Write()

    canvi_ratios[-1].cd()
    legi[-1].Draw()
    out_file.cd()
    canvi_ratios[-1].Write()

out_file.Close()
