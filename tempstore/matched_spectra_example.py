import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
import seaborn as sns
import sklearn
import pandas as pd
import tailored_PRS as PRS
import scipy.fft
import moving_average

print(pd.__version__)
print(np.__version__)
print(sp.__version__)
print(sns.__version__)
print(sklearn.__version__)


#
# r_s = 0
# t = 10.0  # CAN MAYBE MOVE ALL OF THIS LATER?
# rate = 20
# N = int(rate * t)
# fft_range = int(N / 2)
#
# f_sim = rate
# f_prs = rate
# sample_freq = f_prs / 4
# f_cutoff = sample_freq / 2
# filter_select_range = 6
#
# plt.rcParams['font.family'] = 'Times'
# plt.rcParams['font.size'] = 16
# plt.rcParams['axes.titlesize'] = 16
# plt.rcParams['ps.useafm'] = True
# plt.rcParams['pdf.use14corefonts'] = True
# plt.rcParams['text.usetex'] = True
#
# filt_type_list = ['$PRS_{LP}, p_{1}=0.85 (2)$', '$PRS_{BP}, p_{1}=0.9 p_{2}=0.9 (2|4)$ ', '$PRS_{LP}, p_{1}=0.1 (4)$', '$PRS_{BB}, p_{1}=0.5 (2)$']
# p_1_list = [0.85, 0.9, 0.1, 0.5]
# d_1_list = [0, 0, 0, 0]
# k_1_list = [0, 0, 1, 0]
# p_2_list = [666, 0.9, 666, 666]  # 666 is just dummy input for funcion for unused PRS - needs fixing at some point ...
# d_2_list = [666, 0, 666, 666]
# k_2_list = [666, 1, 666, 666]
# seq_num_list = [1, 2, 1, 1]
#
# seq_list = []
# SEQ_LIST = []
#
# for p_1, d_1, k_1, p_2, d_2, k_2, seq_num in zip(p_1_list, d_1_list, k_1_list, p_2_list, d_2_list, k_2_list,
#                                                  seq_num_list):
#
#     sequence_root_1 = PRS.prs(p_1, d_1, k_1, t, f_prs, 0)
#     sequence_1 = np.tile(sequence_root_1, int(f_sim / f_prs))
#     sequence_root_2 = PRS.prs(p_2, d_2, k_2, t, f_prs, 0)
#     sequence_2 = np.tile(sequence_root_2, int(f_sim / f_prs))
#     if seq_num == 1:
#         sequence = sequence_1
#     elif seq_num == 2:
#         sequence = sequence_1 * sequence_2
#     seq_list.append(sequence)
#
# filt_var = 0
# PRS_Pxx_den_list= []
# PRS_Pxx_den_list_db_smooth = []
#
# for prs in seq_list:
#
#     f_bin_per, PRS_Pxx_den = signal.periodogram(prs, fs=rate, nfft=N)
#     PRS_Pxx_den[PRS_Pxx_den == 0] = np.min(PRS_Pxx_den[np.nonzero(PRS_Pxx_den)]) #Replace 0 with smallest number cos of log10
#     PRS_Pxx_den_list.append(PRS_Pxx_den[1:])
#     PRS_Pxx_den_list_db_smooth.append(moving_average.moving_average(10 * np.log10(PRS_Pxx_den[1:]), 4))
#     filt_var = filt_var + 1
#     print(filt_var)
#
#
# #PSD-style plots
# fig, axs = plt.subplots(2, 2)
# f_bin_per = f_bin_per[1:]
# plot_var = 0
#
#

#
#
# for hor in range(2):
#     for ver in range(2):
#
#         axs[ver,hor].plot(f_bin_per, PRS_Pxx_den_list_db_smooth[plot_var], color = colour_array[plot_var], linewidth = 1)
#         axs[ver,hor].set_title(filt_type_list[plot_var])
#         if hor == 0:
#             axs[ver,hor].set(ylabel='Power (dB)')
#         if ver == 1:
#             axs[ver,hor].set(xlabel='Frequency (Hz)')
#         axs[ver,hor].grid(True)
#         plot_var += 1
#
# # labels = ['x-axis', 'y-axis', 'z-axis']
# # fig.legend(axs[ver,hor].get_lines(), labels, loc='upper right') # This works because lines same on each subplot
# fig.subplots_adjust(hspace = 0.4)
# #fig.suptitle('Spectra of Bipolar Sequences')
# # fig.tight_layout()
# plt.show()
#
# #
# # lp_array = PRS_Pxx_den_list[2]
# # lp_array[lp_array<np.max(lp_array)/10] = 0
# # LP_ARRAY = scipy.fft.ifft(lp_array)
# # temp = scipy.fft.fft(LP_ARRAY)
# # extended_LP = np.concatenate([LP_ARRAY,LP_ARRAY])
# # extended_temp = scipy.fft.fft(extended_LP)
# #

# # t = np.arange(400)
# # n = np.zeros((400,), dtype=float)
# # n[15:25] = 1
# # n[25:42] = 1
# # n[42:61] = 1
# # # plt.stem(n)
# # # plt.show()
# #
# # s = scipy.fft.ifft(n)
# # plt.plot(t, s.real, 'b-')
# # plt.legend('real')
# # plt.show()
# #
# # ss = scipy.fft.fft(s.real)



f_sim = 1000
f_prs = f_sim/2
t = 2
N = f_sim * t
t_n = np.linspace(0.0,t,int(f_sim),endpoint=False)
t_n = t_n.reshape(int(N/2), 1)

frequencies = np.array([0, 1, 3, 4, 11,13,24,42,50,70])

sines_unit = np.sin(2.0 * np.pi * frequencies * t_n)
#sines_amp = [0.4, 0.5, 0.7, 0.8, 0.9, 0.9]
sines_amp = [0.75, 0.8, 0.85, 0.9, 1, 1, 0.65, 0.5, 0.4, 0.3]
sines = np.multiply(sines_unit,sines_amp)
signal = np.sum(sines, axis=1)

SIGNAL = scipy.fft.fft(signal,N)
SIGNAL = (2*np.abs(SIGNAL))
SIGNAL = SIGNAL[0:int(len(signal)/2)]
SIGNAL[0] = 0

filt_type_list = ['$PRS_{LP}, p_{1}=0.85 (2)$', '$PRS_{BP}, p_{1}=0.9 p_{2}=0.9 (2|4)$ ', '$PRS_{LP}, p_{1}=0.1 (4)$', '$PRS_{BB}, p_{1}=0.5 (2)$']
p_1_list = [0.85, 0.9, 0.1, 0.5]
d_1_list = [0, 0, 0, 0]
k_1_list = [0, 0, 1, 0]
p_2_list = [666, 0.9, 666, 666]  # 666 is just dummy input for funcion for unused PRS - needs fixing at some point ...
d_2_list = [666, 0, 666, 666]
k_2_list = [666, 1, 666, 666]
seq_num_list = [1, 2, 1, 1]

seq_list = []
SEQ_LIST = []

for p_1, d_1, k_1, p_2, d_2, k_2, seq_num in zip(p_1_list, d_1_list, k_1_list, p_2_list, d_2_list, k_2_list,
                                                 seq_num_list):

    sequence_root_1 = PRS.prs(p_1, d_1, k_1, t, f_prs, 0)
    sequence_1 = np.tile(sequence_root_1, int(1))
    sequence_root_2 = PRS.prs(p_2, d_2, k_2, t, f_prs, 0)
    sequence_2 = np.tile(sequence_root_2, int(1))
    if seq_num == 1:
        sequence = sequence_1
    elif seq_num == 2:
        sequence = sequence_1 * sequence_2
    seq_list.append(sequence)

lp = seq_list[0]

LP = scipy.fft.fft(lp,N)
LP = (2*np.abs(LP))
LP = LP[0:int(len(lp)/2)]
LP[0] = 0

LP_ATT = LP/100
LP[LP<(LP/100)] = LP_ATT[LP<(LP/10)]

SIGNAL = SIGNAL/np.max(SIGNAL)
LP = moving_average.moving_average(LP, 4)
LP = LP/np.max(LP)


#PSD-style plots
fig, axs = plt.subplots(2, 2)
plot_var = 0
f_bin_per = np.arange(0,500)

colour_array = [(0.00, 1.00, 0.00), (1.00, 0.00, 1.00), (0.00, 0.00, 1.00), (1.0, 0.0, 0.0)]

axs[0, 0].plot(t_n, lp, color=colour_array[0], linewidth=1)
axs[0, 1].plot(f_bin_per, LP, color=colour_array[1], linewidth=1)
axs[1, 0].plot(t_n, signal, color=colour_array[2], linewidth=1)
axs[1, 1].plot(f_bin_per, SIGNAL, color=colour_array[3], linewidth=1)



