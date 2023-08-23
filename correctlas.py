# Imports
import argparse
import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Parse arguments
parser = argparse.ArgumentParser(description='Correct for discontinuities in ATLAS difference lightcurves')
parser.add_argument('in_lc', type=str, help='Input difference lightcurve .lc')
parser.add_argument('in_raw', type=str, help='Input reduced lightcurve .lc')
parser.add_argument('out', type=str, help='Output directory')
parser.add_argument('-j', '--jump1', type=bool, help='Correct first wallpaper jump?', default=True)

args = parser.parse_args()
in_lc = args.in_lc
in_raw = args.in_raw
out_dir = args.out
jump1 = args.jump1
print(in_lc)
# Check if output directory exists
if not os.path.exists(out_dir):
    try:
        os.mkdir(out_dir)
    except:
        sys.exit("Output path is not a directory.")
elif not os.path.isdir(out_dir):
    # Check if output dir is a dir
    sys.exit("Output path is not a directory.")

# Wallpaper dates adjust to make sure there are no points left behind
wp1 = 58417  # True 58417
wp2 = 58892  # True 58882
wp_buffer = 0

# Get reduced and difference .lc files from input directory
raw_lc_full = pd.read_csv(in_raw, delim_whitespace=True)
diff_lc_full = pd.read_csv(in_lc, delim_whitespace=True)


def correct_jump(diff_lc, raw_lc, flt, jump_1=False):
    if flt is not None:
        raw_lc = raw_lc[raw_lc['F'] == flt].reset_index(drop=True)
        diff_lc = diff_lc[diff_lc['F'] == flt].reset_index(drop=True)
    diff_lc = diff_lc[diff_lc['duJy'] < 45].reset_index(drop=True)
    raw_lc = raw_lc[raw_lc['###MJD'].isin(diff_lc['###MJD'])].reset_index(drop=True)

    raw_lc_1 = raw_lc[raw_lc['###MJD'] < wp1 - wp_buffer].reset_index(drop=True)['uJy'].mean()
    raw_lc_2 = raw_lc[(raw_lc['###MJD'] > wp1 + wp_buffer) &
                      (raw_lc['###MJD'] < wp2 - wp_buffer)].reset_index(drop=True)['uJy'].mean()
    raw_lc_3 = raw_lc[raw_lc['###MJD'] > wp2 + wp_buffer].reset_index(drop=True)['uJy'].mean()

    raw_shift_1 = raw_lc_2 - raw_lc_1
    raw_shift_2 = raw_lc_3 - raw_lc_2

    diff_lc_1 = diff_lc[diff_lc['###MJD'] < wp1 - wp_buffer].reset_index(drop=True)
    diff_lc_2 = diff_lc[(diff_lc['###MJD'] > wp1 + wp_buffer) & (diff_lc['###MJD'] < wp2 - wp_buffer)].reset_index(
        drop=True)
    diff_lc_3 = diff_lc[diff_lc['###MJD'] > wp2 + wp_buffer].reset_index(drop=True)

    diff_shift_1 = diff_lc_2['uJy'].mean() - diff_lc_1['uJy'].mean()
    if jump_1:
        diff_lc_2['uJy'] = np.array(diff_lc_2['uJy']) - diff_shift_1 + raw_shift_1
    diff_shift_2 = diff_lc_3['uJy'].mean() - diff_lc_2['uJy'].mean()
    diff_lc_3['uJy'] = np.array(diff_lc_3['uJy']) - diff_shift_2 + raw_shift_2

    # print(raw_shift_1, diff_shift_1)
    # print(raw_shift_2, diff_shift_2)
    #
    # print(diff_lc_1['uJy'].mean() - raw_lc_1)
    # print(diff_lc_2['uJy'].mean() - raw_lc_2)
    # print(diff_lc_3['uJy'].mean() - raw_lc_3)

    return pd.concat([diff_lc_1, diff_lc_2, diff_lc_3]).reset_index(drop=True)


corrected_o = correct_jump(diff_lc_full, raw_lc_full, 'o', jump_1=jump1)
corrected_c = correct_jump(diff_lc_full, raw_lc_full, 'c', jump_1=jump1)
diff_lc_corrected = pd.concat([corrected_o, corrected_c]).reset_index(drop=True)

# diff_lc_corrected = correct_jump(diff_lc_full, raw_lc_full, None, jump_1=jump1)

# Save corrected lightcurve
diff_lc_corrected.to_csv(os.path.join(out_dir, os.path.basename(in_lc)), sep=' ', index=False)

# Plot
plt.figure(figsize=(8, 3))
plt.plot(diff_lc_full['###MJD'], diff_lc_full['uJy'], 'b.', alpha=0.8, label='Raw')
plt.plot(diff_lc_corrected['###MJD'], diff_lc_corrected['uJy'], 'r.', alpha=0.5, label='Corrected')
plt.xlabel('MJD')
plt.ylabel('Flux (uJy)')
plt.legend()
plt.ylim([-800, 1000])
plt.show()
