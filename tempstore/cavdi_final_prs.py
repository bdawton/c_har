import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
import seaborn as sns
import sklearn
import pandas as pd
from tailored_PRS import prs
from scipy import signal
import moving_average

print(pd.__version__)
print(np.__version__)
print(sp.__version__)
print(sns.__version__)
print(sklearn.__version__)

r_s = 0
t = 2.0  # CAN MAYBE MOVE ALL OF THIS LATER?
rate = 48000
N = int(rate * t)
fft_range = int(N / 2)

f_sim = rate
f_prs = rate
sample_freq = f_prs / 4
f_cutoff = sample_freq / 2
filter_select_range = 6

plt.rcParams['font.family'] = 'Times'
plt.rcParams['font.size'] = 16
plt.rcParams['ps.useafm'] = True
plt.rcParams['pdf.use14corefonts'] = True
plt.rcParams['text.usetex'] = True

# filt_type_list = ['$PRS_{LF}, p_{1}=0.85 (2|)$', '$PRS_{MF}, p_{1}=0.9 p_{2}=0.9 (2|4)$ ', '$PRS_{HF}, p_{1}=0.01 (4|)$', '$PRS_{BB}, p_{1}=0.5 (2|)$']
# p_1_list = [0.001]
# d_1_list = [0]
# k_1_list = [1]
# p_2_list = [0.999]  # 666 is just dummy input for funcion for unused PRS - needs fixing at some point ...
# d_2_list = [0]
# k_2_list = [0]
# seq_num_list = [2]
#
# seq_list = []
# SEQ_LIST = []
#
# for p_1, d_1, k_1, p_2, d_2, k_2, seq_num in zip(p_1_list, d_1_list, k_1_list, p_2_list, d_2_list, k_2_list,
#                                                  seq_num_list):
#
#     sequence_root_1 = PRS.PRS(p_1, d_1, k_1, t, f_prs, 0)
#     sequence_1 = np.tile(sequence_root_1, int(f_sim / f_prs))
#     sequence_root_2 = PRS.PRS(p_2, d_2, k_2, t, f_prs, 0)
#     sequence_2 = np.tile(sequence_root_2, int(f_sim / f_prs))
#     if seq_num == 1:
#         sequence = sequence_1
#     elif seq_num == 2:
#         sequence = sequence_1 * sequence_2
#     seq_list.append(sequence)

f_upper_band = 3000  #This approach is more truthful than the commented one, because by limiting the PRS root length and then tiling it, you create a different frequency response in the PRS. tThis is the one that was used in the IEEE paper. Even if the commented version gives better results, that's not what you did, so it would be incorrect. Even though I got the band targetting wrong, the rest of the explanation is correct as long as i generate PRS this way. So needs to be mimicked if ever do IRL
f_prs = f_upper_band * 2
sample_freq = f_prs / 2
f_cutoff = sample_freq / 2

sequence_root_1 = prs(0.001, 0, 1, 2, f_prs, 0)
sequence_1 = np.tile(sequence_root_1, int(f_sim / f_prs))
sequence_root_2 = prs(0.999, 0, 0, 2, f_prs, 0)
sequence_2 = np.tile(sequence_root_2, int(f_sim / f_prs))
sequence = sequence_1 * sequence_2

seq_list = [sequence]
PRS_Pxx_den_list= []
PRS_Pxx_den_list_db_smooth = []
shift_var = 270  #this is because of diffrences with MATLAB, also maybe different mocing average implemenatiaon

for prs in seq_list:

    f_bin_per, PRS_Pxx_den = signal.periodogram(prs, fs=rate, nfft=N)
    PRS_Pxx_den[PRS_Pxx_den == 0] = np.min(PRS_Pxx_den[np.nonzero(PRS_Pxx_den)]) #Replace 0 with smallest number cos of log10
    PRS_Pxx_den_list.append(PRS_Pxx_den[1:])
    PRS_Pxx_den_list_db_smooth.append((moving_average.moving_average(10 * np.log10(PRS_Pxx_den[1:]), 400) + shift_var))


#PSD-style plots
fig, ax = plt.subplots()
f_bin_per = f_bin_per[1:]
plot_var = 0


# ax.plot(x, y3, color=(1.0, 0.0, 0.0), marker='o', markersize=8, markevery=slice(250, 5000, 250), label='$x_{BB}$')
# ax.plot(x, y2, color=(0.00, 1.00, 0.00), marker='v', markersize=8, markevery=slice(0, 1000, 50), label='$x_{LF}$')
# ax.plot(x, y1, color=(1.00, 0.00, 1.00), marker='s', markersize=8, markevery=slice(2000, 3000, 50), label='$x_{BP}$')
# ax.plot(x, y0, color=(0.00, 0.00, 1.00), marker='+', markersize=8, markevery=slice(4000, 5000, 50), label='$x_{HF}$')


# COLOUR ARRAY FOR PLOTS, CHECK WITH IEEE ACCESS COLORS TO MATCH COLORS - NEED TO FIND THE BLOODY CODE!
colour_array = [(0.00, 0.00, 1.00)]


ax.plot(f_bin_per, PRS_Pxx_den_list_db_smooth[plot_var], color = colour_array[plot_var], linewidth = 1)
plt.xticks([0, 4000, 8000, 12000, 16000, 20000, 24000], ['0', '4', '8', '12', '16', '20', '24'])
plt.xlim([0, 24000])
#plt.ylim([-80,-40])
ax.set(ylabel='Power (dB)')
ax.set(xlabel='Frequency (Hz)')
ax.grid(True)


# labels = ['x-axis', 'y-axis', 'z-axis']
# fig.legend(axs[ver,hor].get_lines(), labels, loc='upper right') # This works because lines same on each subplot
#fig.subplots_adjust(hspace = 1)
#fig.suptitle('Spectra of Bipolar Sequences')
plt.tight_layout()
plt.show()




print("finished")
