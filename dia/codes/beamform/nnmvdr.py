#!/usr/bin/python

import os
import pickle
import glob
import json
import argparse

import torch as th
import numpy as np
from torch.autograd import Variable

from model import MaskComputer, MaskEstimator 
from fgnt.beamforming import gev_wrapper_on_masks, mvdr_wrapper_on_masks 
from fgnt.signal_processing import audioread, audiowrite, stft, istft
import sys
filename = sys.argv[1]

num_bins = 513

def load_multichannel_data(prefix):
    audio_mat = audioread(prefix)
    return np.array(audio_mat).astype(np.float32)

def apply_beamfomer(args):
    estimator = MaskEstimator(num_bins) 
    mask_computer = MaskComputer(estimator, args.model)
    
    func_bf = mvdr_wrapper_on_masks if not args.gev else \
            gev_wrapper_on_masks

    f = args.flist.strip()
    tokens  = f.split('/')
    noisy_samples = load_multichannel_data(args.flist)
    noisy_specs   = stft(noisy_samples, time_dim=1).transpose((1, 0, 2))
    mask_n, mask_x = mask_computer.compute_masks(np.abs(noisy_specs).astype(np.float32))
    mask_n = np.median(mask_n, axis=1)
    mask_x = np.median(mask_x, axis=1)
    clean_specs   = func_bf(noisy_specs, mask_n, mask_x) 
    clean_samples = istft(clean_specs)
    #print('dumps to {}/{}.wav'.format(args.dump, tokens[-1]))
    audiowrite(clean_samples, '{}/{}'.format(args.dump, tokens[-1]), 16000, True, True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Command to apply MVDR/GEV beamformer")
    parser.add_argument("model", type=str, 
                        help="path of model states generated by train_estimator.py")
    parser.add_argument("flist", type=str, 
                        help="a list of wave to processed")
    parser.add_argument("--dump", type=str, default="enhan", dest="dump",
                        help="output directory of enhanced data")
    parser.add_argument("--gev", action='store_true', default=True, dest="gev",
                        help="apply GEV beamforming instead of MVDR")
    args = parser.parse_args()
    apply_beamfomer(args)
