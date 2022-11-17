# I need f-domain plots of all average activity signals for GYRO and ACCEL
# I need f-domain plots of all PRS I'm using

import os
import glob
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy import signal
from scipy.fft import fft
from scipy.fftpack import fftfreq
import moving_average

suppress_warning_var = 1
if suppress_warning_var == 1:
    pd.options.mode.chained_assignment = None  # default='warn'
    print(
        "Supressing the: \"SettingWithCopyWarning: A value is trying to be set on a copy of a slice from a DataFrame.\"")
    print("regarding index sorting of pulled subject and activity dfs and the creation of PRSxInput columns of df")

r_s = 0
t = 10.0  # CAN MAYBE MOVE ALL OF THIS LATER?
rate = 20
N = int(rate * t)

f_sim = rate
f_prs = rate
sample_freq = f_prs / 4
f_cutoff = sample_freq / 2
filter_select_range = 6

plt.rcParams['font.family'] = 'Times'
plt.rcParams['font.size'] = 12 #These ones are set to 12 because it is a more crowded plot
plt.rcParams['axes.titlesize'] = 12 #These ones are set to 12 because it is a more crowded plot
plt.rcParams['ps.useafm'] = True
plt.rcParams['pdf.use14corefonts'] = True
plt.rcParams['text.usetex'] = True

nhoa_c = []
ghoa_c = []
ehoa_c = []

filter_select_range = 6
filter_select_list = []
p1_list = []
d1_list = []
k1_list = []
p2_list = []
d2_list = []
k2_list = []
seq_num_list = []
lpf_accuracy_list = []
bpf_accuracy_list = []
hpf_accuracy_list = []
bb_accuracy_list = []
ones_accuracy_list = []
no_cs_accuracy_list = []

spread_columns = ['x_spread', 'y_spread', 'z_spread']
filtered_columns = ['x_filtered', 'y_filtered', 'z_filtered']
sampled_columns = ['x_sampled', 'y_sampled', 'z_sampled']
quant_sampled_columns = ['x_q_sampled', 'y_q_sampled', 'z_q_sampled']

# Get file paths
data_folder = 'wisdm-dataset_mod/raw'  # raw text files
device_list = glob.glob(data_folder + '/*')
sensor_list = glob.glob(data_folder + '/*/*')
label_list = 'wisdm-dataset_mod/raw/activity_key_w_numbers.txt'
for device in device_list:
    device_name = os.path.basename(device)
    device_str = np.array(list(map(lambda x: os.path.basename(x), device_list)))
    device_types = np.unique(device_str)

    for sensor in sensor_list:
        sensor_name = os.path.basename(sensor)
        sensor_str = np.array(list(map(lambda x: os.path.basename(x), sensor_list)))
        sensor_types = np.unique(sensor_str)
gyro_watch_list = glob.glob('wisdm-dataset_mod/raw/watch/gyro' + '/*')


# Load in watch gyro data
big_data_gyro_watch = []
for entry in gyro_watch_list:
    data_gyro_watch = pd.read_csv(entry, header=None, lineterminator=";", low_memory=False, parse_dates=True)
    big_data_gyro_watch.append(data_gyro_watch)

# Clean up and reformat data
big_data_column_names = ['subjectid', 'activity', 'timestamp', 'x', 'y', 'z']
df_big_data_gyro_watch = pd.concat(big_data_gyro_watch)
df_big_data_gyro_watch.columns = big_data_column_names
df_big_data_gyro_watch.dropna(axis=0, how="any", thresh=None, subset=None, inplace=True)
df_big_data_gyro_watch = df_big_data_gyro_watch.replace('\n', '', regex=True)
df_big_data_gyro_watch = df_big_data_gyro_watch.astype({"subjectid": str})

act_label_list = range(len(df_big_data_gyro_watch['activity'].unique()))
type_ids = dict(zip(df_big_data_gyro_watch['activity'].unique(), act_label_list))  # Doesn't matter which?
df_big_data_gyro_watch = df_big_data_gyro_watch.replace({"activity": type_ids})

# Pull out subjects that don't contain all activities (is that even possible?)
watch_gyro_drop_subject = []
keep_drop = []
keep_list = []
ind_subjectids = np.unique(df_big_data_gyro_watch["subjectid"])

for i_si in ind_subjectids:
    data_drop_subject = df_big_data_gyro_watch[df_big_data_gyro_watch["subjectid"] == i_si]
    if set(type_ids.values()).issubset(set(data_drop_subject['activity'])):
        # print('keep')
        k_d = (i_si, 'keep')
        keep_list.append(i_si)
        watch_gyro_drop_subject.append(data_drop_subject)
    else:
        # print('drop')
        k_d = (i_si, 'drop')
    keep_drop.append(k_d)
df_keep_drop = pd.DataFrame(keep_drop, columns=['subjectid', 'k_d'])

# Non-hand-oriented activities:
# {walking, jogging, stairs, sitting, standing, kicking}

nhoa_arr = np.array([0, 1, 2, 3, 4, 11])


# General hand-oriented activities:
# {dribbling, playing catch, typing, writing, clapping, brushing teeth, folding clothes}

ghoa_arr = np.array([13, 12, 5, 14, 15, 6, 16])

# Eating hand-oriented activities:
# {eating pasta, eating soup, eating sandwich, eating chips, drinking}

ehoa_arr = np.array([9, 7, 17, 8, 10])


count_track_var = 1
final_count_track_var = len(nhoa_arr) * len(ghoa_arr) * len(ehoa_arr) * filter_select_range  # We DON'T NEED TO USE len(filter_select_range), because that value is already the length (see the filter loop initialisation)

line_track_var = 0

# Loop through activities


# Split each subject into activities
sliced_act_subject_dict = {}
sliced_subject_key_list = []

for df_by_subject in watch_gyro_drop_subject:
    sliced_act_list = []
    len_sliced_act_list = []
    per_act_sliced_list = []

    for act_by_subject in act_label_list:

        df_by_subject_act = df_by_subject[df_by_subject["activity"] == act_by_subject]
        df_by_subject_act.set_index('timestamp', inplace=True)
        df_by_subject_act.sort_index()
        df_by_subject_act.index = pd.to_datetime(df_by_subject_act.index, unit='ns', errors='coerce')
        df_by_subject_act.dropna()
        df_by_subject_act_grouped = df_by_subject_act.groupby(pd.Grouper(freq='10s', origin='start'))

        per_act_slice_counter = 0

        pull_sliced_list = []
        nan_loc = []
        loc_var = 0
        per_act_slice_len_list = []

        for x in df_by_subject_act_grouped:
            per_act_slice_len_list.append(len(x[1]))
            if len(x[1]) == N:  # Sequence equal to N?
                pull_sliced_list.append(x[1])
            if np.where(x[1].isnull())[0].size > 0:
                nan_loc.append(loc_var)
            loc_var = loc_var + 1

        per_act_sliced_list = per_act_sliced_list + pull_sliced_list

    sliced_act_list.append(per_act_sliced_list)
    per_act_slice_counter = per_act_slice_counter + 1

    subject_key = df_by_subject["subjectid"].unique()[0]
    sliced_subject_key_list.append(subject_key)
    sliced_act_subject_dict[subject_key] = sliced_act_list  # 0 length entries haven't been dropped

sliced_act_subject_list = list(sliced_act_subject_dict.values())

# Pull out subjects that don't contain any (or a minimum amount? Like fall between a certain range?)
sliced_watch_gyro_drop_subject = []
s_k_list = []

for s_item in sliced_act_subject_list:
    if len(s_item[0]) >= 10:  # Let's just say minimum length 10
        # print('keep')
        s_k = (s_item[0][0]['subjectid'].unique()[0], 'keep')
        s_k_list.append(s_k)
        sliced_watch_gyro_drop_subject.append(s_item)

x_sa_dict = {}
y_sa_dict = {}
z_sa_dict = {}

x_sd_slice = []
y_sd_slice = []
z_sd_slice = []

for sd_item in sliced_watch_gyro_drop_subject:
    for sd_slice in sd_item[0]:
        x_sd_slice.append(sd_slice[['subjectid','activity','x']])
        y_sd_slice.append(sd_slice[['subjectid','activity','y']])
        z_sd_slice.append(sd_slice[['subjectid','activity','z']])

for act_sd in act_label_list:
    x_sa_list = []
    y_sa_list = []
    z_sa_list = []
    for x_sa, y_sa, z_sa in zip(x_sd_slice, y_sd_slice, z_sd_slice):
        sa_key = int(x_sa['activity'].unique())
        # print(sa_key)
        if sa_key == act_sd:
            x_sa_list.append(x_sa['x'])
            y_sa_list.append(y_sa['y'])
            z_sa_list.append(z_sa['z'])
    x_sa_dict[act_sd] = x_sa_list
    y_sa_dict[act_sd] = y_sa_list
    z_sa_dict[act_sd] = z_sa_list

x_av_act = {}
y_av_act = {}
z_av_act = {}

X_av_act = {}
Y_av_act = {}
Z_av_act = {}

XP_av_act = {}
YP_av_act = {}
ZP_av_act = {}

XP_av_act_db_smooth = {}
YP_av_act_db_smooth = {}
ZP_av_act_db_smooth = {}


for av_act in act_label_list:
    x_average = np.mean(x_sa_dict[av_act], axis = 0)
    X_AVERAGE = fft(x_average)
    X_AVERAGE_ABS = np.abs(X_AVERAGE)
    # X_AVERAGE_POS = 2 * (X_AVERAGE_ABS[1:len(X_AVERAGE_ABS) // 2])  # *2 for amplitude makeup
    X_AVERAGE_POS = 2 * (X_AVERAGE_ABS[:len(X_AVERAGE_ABS) // 2])  # *2 for amplitude makeup
    X_AVERAGE_POS[0] = 0
    f_bin_per, XPxx_den = signal.periodogram(x_average, fs = rate,nfft= N)
    x_av_act[av_act] = x_average
    X_av_act[av_act] = X_AVERAGE_POS
    XP_av_act[av_act] = XPxx_den[1:]
    XP_av_act_db_smooth[av_act] = moving_average.moving_average(10 * np.log10(XPxx_den[1:]), 4)
    # XP_av_act[av_act] = XPxx_den

    y_average = np.mean(y_sa_dict[av_act], axis = 0)
    Y_AVERAGE = fft(y_average)
    Y_AVERAGE_ABS = np.abs(Y_AVERAGE)
    # Y_AVERAGE_POS = 2 * (Y_AVERAGE_ABS[1:len(Y_AVERAGE_ABS) // 2])  # *2 for amplitude makeup
    Y_AVERAGE_POS = 2 * (Y_AVERAGE_ABS[:len(Y_AVERAGE_ABS) // 2])  # *2 for amplitude makeup
    Y_AVERAGE_POS[0] = 0
    f_bin_per, YPxx_den = signal.periodogram(y_average, fs = rate,nfft= N)
    y_av_act[av_act] = y_average
    Y_av_act[av_act] = Y_AVERAGE_POS
    YP_av_act[av_act] = YPxx_den[1:]
    YP_av_act_db_smooth[av_act] = moving_average.moving_average(10 * np.log10(YPxx_den[1:]), 4)
    # YP_av_act[av_act] = YPxx_den

    z_average = np.mean(z_sa_dict[av_act], axis = 0)
    Z_AVERAGE = fft(z_average)
    Z_AVERAGE_ABS = np.abs(Z_AVERAGE)
    # Z_AVERAGE_POS = 2 * (Z_AVERAGE_ABS[1:len(Z_AVERAGE_ABS) // 2])  # *2 for amplitude makeup
    Z_AVERAGE_POS = 2 * (Z_AVERAGE_ABS[:len(Z_AVERAGE_ABS) // 2])  # *2 for amplitude makeup
    Z_AVERAGE_POS[0] = 0
    f_bin_per, ZPxx_den = signal.periodogram(z_average, fs = rate,nfft= N)
    z_av_act[av_act] = z_average
    Z_av_act[av_act] = Z_AVERAGE_POS
    ZP_av_act[av_act] = ZPxx_den[1:]
    ZP_av_act_db_smooth[av_act] = moving_average.moving_average(10 * np.log10(ZPxx_den[1:]), 4)
    # ZP_av_act[av_act] = ZPxx_den



act_text_in_order = ['Walking' ,'Jogging', 'Climbing Stairs' ,'Sitting' ,'Standing' ,'Typing' ,'Brushing Teeth' ,'Eating Soup', 'Eating Chips', 'Eating Pasta', 'Drinking','Ball Kicking', 'Ball Catching', 'Dribbling (Basketball)', 'Writing', 'Clapping', 'Folding Clothes', 'Eating Sandwich']

# Plot average signals before filtering
f_bins = fftfreq(N, 1 / rate)
# f_bins_pos = f_bins[1:len(f_bins) // 2]  # remove DC component
f_bin_per = f_bin_per[1:]
f_bins_pos = f_bins[:len(f_bins) // 2]  # remove DC component
# f_bin_per = f_bin_per[:]


#PSD-style plots
fig, axs = plt.subplots(6, 3)
act_var = 0


colour_array = [(0.00, 0.0, 1.0),(1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]

for hor in range(3):
    for ver in range(6):
        print(act_var)

        axs[ver,hor].plot(f_bin_per, XP_av_act_db_smooth[act_var], color=colour_array[0], linestyle = 'solid' ,linewidth = 1)
        axs[ver,hor].plot(f_bin_per, YP_av_act_db_smooth[act_var], color=colour_array[1], linestyle = 'dotted'  ,linewidth = 1)
        axs[ver,hor].plot(f_bin_per, ZP_av_act_db_smooth[act_var], color=colour_array[2], linestyle = 'dashed'  ,linewidth = 1)
        axs[ver,hor].set_title(act_text_in_order[act_var])
        if hor == 0:
            axs[ver,hor].set(ylabel='Power (dB)')
        if ver == 5:
            axs[ver,hor].set(xlabel='Frequency (Hz)')
        axs[ver,hor].grid(True)
        act_var += 1

labels = ['x-axis', 'y-axis', 'z-axis']
fig.legend(axs[ver,hor].get_lines(), labels, loc='upper right') # This works because lines same on each subplot
fig.subplots_adjust(hspace = 1)
fig.suptitle('Gyroscope')
# fig.tight_layout()
plt.show()

#
# fig, axs = plt.subplots(6, 3)
# axs[0, 0].semilogy(f_bin_per, XP_av_act[0] ,f_bin_per, YP_av_act[0],f_bin_per, ZP_av_act[0])
# axs[0, 0].set_title('Axis [0, 0]')
# axs[0, 1].semilogy(f_bin_per, XP_av_act[1] ,f_bin_per, YP_av_act[1],f_bin_per, ZP_av_act[1])
# axs[0, 1].set_title('Axis [0, 0]')
# axs[0, 2].semilogy(f_bin_per, XP_av_act[2] ,f_bin_per, YP_av_act[2],f_bin_per, ZP_av_act[2])
# axs[0, 2].set_title('Axis [0, 0]')
# axs[1, 0].semilogy(f_bin_per, XP_av_act[3] ,f_bin_per, YP_av_act[3],f_bin_per, ZP_av_act[3])
# axs[1, 0].set_title('Axis [0, 0]')
# axs[1, 1].semilogy(f_bin_per, XP_av_act[4] ,f_bin_per, YP_av_act[4],f_bin_per, ZP_av_act[4])
# axs[1, 1].set_title('Axis [0, 0]')
# axs[1, 2].semilogy(f_bin_per, XP_av_act[5] ,f_bin_per, YP_av_act[5],f_bin_per, ZP_av_act[5])
# axs[1, 2].set_title('Axis [0, 0]')
# axs[2, 0].semilogy(f_bin_per, XP_av_act[6] ,f_bin_per, YP_av_act[6],f_bin_per, ZP_av_act[6])
# axs[2, 0].set_title('Axis [0, 0]')
# axs[2, 1].semilogy(f_bin_per, XP_av_act[7] ,f_bin_per, YP_av_act[7],f_bin_per, ZP_av_act[7])
# axs[2, 1].set_title('Axis [0, 0]')
# axs[2, 2].semilogy(f_bin_per, XP_av_act[8] ,f_bin_per, YP_av_act[8],f_bin_per, ZP_av_act[8])
# axs[2, 2].set_title('Axis [0, 0]')
# axs[3, 0].semilogy(f_bin_per, XP_av_act[9] ,f_bin_per, YP_av_act[9],f_bin_per, ZP_av_act[9])
# axs[3, 0].set_title('Axis [0, 0]')
# axs[3, 1].semilogy(f_bin_per, XP_av_act[10] ,f_bin_per, YP_av_act[10],f_bin_per, ZP_av_act[10])
# axs[3, 1].set_title('Axis [0, 0]')
# axs[3, 2].semilogy(f_bin_per, XP_av_act[11] ,f_bin_per, YP_av_act[11],f_bin_per, ZP_av_act[11])
# axs[3, 2].set_title('Axis [0, 0]')
# axs[4, 0].semilogy(f_bin_per, XP_av_act[12] ,f_bin_per, YP_av_act[12],f_bin_per, ZP_av_act[12])
# axs[4, 0].set_title('Axis [0, 0]')
# axs[4, 1].semilogy(f_bin_per, XP_av_act[13] ,f_bin_per, YP_av_act[13],f_bin_per, ZP_av_act[13])
# axs[4, 1].set_title('Axis [0, 0]')
# axs[4, 2].semilogy(f_bin_per, XP_av_act[14] ,f_bin_per, YP_av_act[14],f_bin_per, ZP_av_act[14])
# axs[4, 2].set_title('Axis [0, 0]')
# axs[5, 0].semilogy(f_bin_per, XP_av_act[15] ,f_bin_per, YP_av_act[15],f_bin_per, ZP_av_act[15])
# axs[5, 0].set_title('Axis [0, 0]')
# axs[5, 1].semilogy(f_bin_per, XP_av_act[16] ,f_bin_per, YP_av_act[16],f_bin_per, ZP_av_act[16])
# axs[5, 1].set_title('Axis [0, 0]')
# axs[5, 2].semilogy(f_bin_per, XP_av_act[17] ,f_bin_per, YP_av_act[17],f_bin_per, ZP_av_act[17])
# axs[5, 2].set_title('Axis [0, 0]')

#
# fig, axs = plt.subplots(6, 3)
# axs[0, 0].plot(f_bins_pos, X_av_act[0],f_bins_pos,Y_av_act[0],f_bins_pos, Z_av_act[0])
# axs[0, 0].set_title('Axis [0, 0]')
# axs[0, 1].plot(f_bins_pos, X_av_act[1],f_bins_pos,Y_av_act[1],f_bins_pos, Z_av_act[1])
# axs[0, 1].set_title('Axis [0, 0]')
# axs[0, 2].plot(f_bins_pos, X_av_act[2],f_bins_pos,Y_av_act[2],f_bins_pos, Z_av_act[2])
# axs[0, 2].set_title('Axis [0, 0]')
# axs[1, 0].plot(f_bins_pos, X_av_act[3],f_bins_pos,Y_av_act[3],f_bins_pos, Z_av_act[3])
# axs[1, 0].set_title('Axis [0, 0]')
# axs[1, 1].plot(f_bins_pos, X_av_act[4],f_bins_pos,Y_av_act[4],f_bins_pos, Z_av_act[4])
# axs[1, 1].set_title('Axis [0, 0]')
# axs[1, 2].plot(f_bins_pos, X_av_act[5],f_bins_pos,Y_av_act[5],f_bins_pos, Z_av_act[5])
# axs[1, 2].set_title('Axis [0, 0]')
# axs[2, 0].plot(f_bins_pos, X_av_act[6],f_bins_pos,Y_av_act[6],f_bins_pos, Z_av_act[6])
# axs[2, 0].set_title('Axis [0, 0]')
# axs[2, 1].plot(f_bins_pos, X_av_act[7],f_bins_pos,Y_av_act[7],f_bins_pos, Z_av_act[7])
# axs[2, 1].set_title('Axis [0, 0]')
# axs[2, 2].plot(f_bins_pos, X_av_act[8],f_bins_pos,Y_av_act[8],f_bins_pos, Z_av_act[8])
# axs[2, 2].set_title('Axis [0, 0]')
# axs[3, 0].plot(f_bins_pos, X_av_act[9],f_bins_pos,Y_av_act[9],f_bins_pos, Z_av_act[9])
# axs[3, 0].set_title('Axis [0, 0]')
# axs[3, 1].plot(f_bins_pos, X_av_act[10],f_bins_pos,Y_av_act[10],f_bins_pos, Z_av_act[10])
# axs[3, 1].set_title('Axis [0, 0]')
# axs[3, 2].plot(f_bins_pos, X_av_act[11],f_bins_pos,Y_av_act[11],f_bins_pos, Z_av_act[11])
# axs[3, 2].set_title('Axis [0, 0]')
# axs[4, 0].plot(f_bins_pos, X_av_act[12],f_bins_pos,Y_av_act[12],f_bins_pos, Z_av_act[12])
# axs[4, 0].set_title('Axis [0, 0]')
# axs[4, 1].plot(f_bins_pos, X_av_act[13],f_bins_pos,Y_av_act[13],f_bins_pos, Z_av_act[13])
# axs[4, 1].set_title('Axis [0, 0]')
# axs[4, 2].plot(f_bins_pos, X_av_act[14],f_bins_pos,Y_av_act[14],f_bins_pos, Z_av_act[14])
# axs[4, 2].set_title('Axis [0, 0]')
# axs[5, 0].plot(f_bins_pos, X_av_act[15],f_bins_pos,Y_av_act[15],f_bins_pos, Z_av_act[15])
# axs[5, 0].set_title('Axis [0, 0]')
# axs[5, 1].plot(f_bins_pos, X_av_act[16],f_bins_pos,Y_av_act[16],f_bins_pos, Z_av_act[16])
# axs[5, 1].set_title('Axis [0, 0]')
# axs[5, 2].plot(f_bins_pos, X_av_act[17],f_bins_pos,Y_av_act[17],f_bins_pos, Z_av_act[17])
# axs[5, 2].set_title('Axis [0, 0]')




# for ax in axs.flat:
#     ax.set(xlabel='x-label', ylabel='y-label')
#
# # Hide x labels and tick labels for top plots and y ticks for right plots.
# for ax in axs.flat:
#     ax.label_outer()



#
# fft_x_average =

print("finished")