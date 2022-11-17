import os
import glob
import wave
import struct
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt
import moving_average



abs_path = os.path.abspath(__file__)
abs_dir = os.path.dirname(abs_path)
data_folder = abs_dir + '/VehicleData'
group_list = glob.glob(data_folder + '/*')
remove_list = (data_folder + "/G10", data_folder + "/G15")

for r in remove_list:
    group_list.remove(r)

"""# Simulation Parameters"""
rand_seed = 0
exclude_types = ['Bus', 'Truck']
x_hold = {}
y_hold = {}
big_table_data = {}
big_table_label = {}
target_types = None
type_ids = None

for group in group_list:

    """# load wav files"""

    file_list = glob.glob(group + '/*/*')
    group_name = os.path.basename(group)
    print(f"loading in {group_name}")
    label_str = np.array(list(map(lambda xl: os.path.basename(os.path.dirname(xl)), file_list)))
    vehicle_types = np.array(['NoVeh', 'Car', 'Scooter', 'Bus', 'Truck'])
    # vehicle_types = np.unique(label_str)  # to automatically extract vehicle types, use this line
    type_ids = dict(zip(range(len(vehicle_types)), vehicle_types))
    raw_label = np.empty(len(label_str), dtype=int)
    for k, v in type_ids.items():
        raw_label[label_str == v] = k

    data = None
    for i in range(len(file_list)):
        with wave.open(file_list[i], 'rb') as w:
            num_sample = w.getnframes()
            sample_size = w.getsampwidth()
            f_sim = w.getframerate()
            ch = w.getnchannels()
            # read all the data
            raw_data = w.readframes(num_sample)

        # allocate memory for output
        if data is None:
            data = np.empty([len(raw_label), num_sample * ch], dtype=int)
        # convert binary to integer
        pack_str = '<{0}{1}'.format(num_sample * ch, {1: 'b', 2: 'h', 3: 'i', 4: 'i', 8: 'q'}[sample_size])
        data[i, :] = np.array(list(struct.unpack(pack_str, raw_data)))

    big_table_label[group_name] = raw_label
    big_table_data[group_name] = data

mean_novehs_list = []
mean_cars_list = []
mean_scooters_list = []

for g in big_table_data:
    reg_table_data = big_table_data[g]
    reg_label_data = big_table_label[g]
    group_novehs = reg_table_data[reg_label_data == 0]
    group_cars = reg_table_data[reg_label_data == 1]
    group_scooter = reg_table_data[reg_label_data == 2]
    mean_group_novehs = group_novehs.mean(axis = 0)
    mean_group_cars = group_cars.mean(axis=0)
    mean_group_scooter = group_scooter.mean(axis=0)
    mean_novehs_list.append(mean_group_novehs)
    mean_cars_list.append(mean_group_cars)
    mean_scooters_list.append(mean_group_scooter)

mean_novehs = np.array(mean_novehs_list).mean(axis=0)
mean_cars = np.array(mean_cars_list).mean(axis=0)
mean_scooters = np.array(mean_scooters_list).mean(axis=0)

clear_groups = ['G1', 'G2', 'G4', 'G5', 'G8', 'G11', 'G13']
mean_clear_novehs_list = []
mean_clear_cars_list = []
mean_clear_scooters_list = []

for g_clear in clear_groups:
    clear_table_data = big_table_data[g_clear]
    clear_label_data = big_table_label[g_clear]
    group_clear_novehs = clear_table_data[clear_label_data == 0]
    group_clear_cars = clear_table_data[clear_label_data == 1]
    group_clear_scooter = clear_table_data[clear_label_data == 2]
    mean_group_clear_novehs = group_clear_novehs.mean(axis = 0)
    mean_group_clear_cars = group_clear_cars.mean(axis=0)
    mean_group_clear_scooter = group_clear_scooter.mean(axis=0)
    mean_clear_novehs_list.append(mean_group_clear_novehs)
    mean_clear_cars_list.append(mean_group_clear_cars)
    mean_clear_scooters_list.append(mean_group_clear_scooter)
    
mean_clear_novehs = np.array(mean_clear_novehs_list).mean(axis=0)
mean_clear_cars = np.array(mean_clear_cars_list).mean(axis=0)
mean_clear_scooters = np.array(mean_clear_scooters_list).mean(axis=0)

rainy_groups = ['G6', 'G7', 'G16']
mean_rainy_novehs_list = []
mean_rainy_cars_list = []
mean_rainy_scooters_list = []

for g_rainy in rainy_groups:
    rainy_table_data = big_table_data[g_rainy]
    rainy_label_data = big_table_label[g_rainy]
    group_rainy_novehs = rainy_table_data[rainy_label_data == 0]
    group_rainy_cars = rainy_table_data[rainy_label_data == 1]
    group_rainy_scooter = rainy_table_data[rainy_label_data == 2]
    mean_group_rainy_novehs = group_rainy_novehs.mean(axis=0)
    mean_group_rainy_cars = group_rainy_cars.mean(axis=0)
    mean_group_rainy_scooter = group_rainy_scooter.mean(axis=0)
    mean_rainy_novehs_list.append(mean_group_rainy_novehs)
    mean_rainy_cars_list.append(mean_group_rainy_cars)
    mean_rainy_scooters_list.append(mean_group_rainy_scooter)

mean_rainy_novehs = np.array(mean_rainy_novehs_list).mean(axis=0)
mean_rainy_cars = np.array(mean_rainy_cars_list).mean(axis=0)
mean_rainy_scooters = np.array(mean_rainy_scooters_list).mean(axis=0)

windy_groups = ['G3', 'G9', 'G12', 'G14']
mean_windy_novehs_list = []
mean_windy_cars_list = []
mean_windy_scooters_list = []

for g_windy in windy_groups:
    windy_table_data = big_table_data[g_windy]
    windy_label_data = big_table_label[g_windy]
    group_windy_novehs = windy_table_data[windy_label_data == 0]
    group_windy_cars = windy_table_data[windy_label_data == 1]
    group_windy_scooter = windy_table_data[windy_label_data == 2]
    mean_group_windy_novehs = group_windy_novehs.mean(axis=0)
    mean_group_windy_cars = group_windy_cars.mean(axis=0)
    mean_group_windy_scooter = group_windy_scooter.mean(axis=0)
    mean_windy_novehs_list.append(mean_group_windy_novehs)
    mean_windy_cars_list.append(mean_group_windy_cars)
    mean_windy_scooters_list.append(mean_group_windy_scooter)

mean_windy_novehs = np.array(mean_windy_novehs_list).mean(axis=0)
mean_windy_cars = np.array(mean_windy_cars_list).mean(axis=0)
mean_windy_scooters = np.array(mean_windy_scooters_list).mean(axis=0)

title_list = ['Cars', 'Scooters', 'No Vehicles']
plot_list = [mean_cars, mean_scooters, mean_novehs]
psd_list = []
psd_list_db_smooth = []

for plot in plot_list:
    f_bin_per, psd = signal.periodogram(plot, fs=f_sim, nfft=num_sample)
    f_bin_per = f_bin_per[1:]
    psd[psd == 0] = np.min(psd[np.nonzero(psd)])  # Replace 0 with smallest number cos of log10
    psd_list.append(psd[1:])
    psd_list_db_smooth.append(moving_average.moving_average(10 * np.log10(psd[1:]), 400))


""""# Set plotting parameters for use in Latex publication """

plt.rcParams['font.family'] = 'Times'
plt.rcParams['font.size'] = 12
plt.rcParams['ps.useafm'] = True
plt.rcParams['pdf.use14corefonts'] = True
plt.rcParams['text.usetex'] = True

for psd_smooth, title in zip(psd_list_db_smooth, title_list):
    plt.plot(f_bin_per, psd_smooth, label = title)

plt.legend()
plt.show()
# #
# # x = np.squeeze(matlab_file_6['x'][0])
# # y3 = np.squeeze(matlab_file_6['y'][3])
# # maxy3 = np.max(y3)
# # y3 = y3 / maxy3
# # y0 = np.squeeze(matlab_file_6['y'][0])
# # y0 = y0 / maxy3  # Normalization, though this should already have been done prior to import?
# # y1 = np.squeeze(matlab_file_6['y'][1])
# # y1 = y1 / maxy3
# # y2 = np.squeeze(matlab_file_6['y'][2])
# # y2 = y2 / maxy3
# # # y2 = y2/np.max(y2)*(np.max(y2)/np.max(y3))
# # fig, ax = plt.subplots()
# # ax.plot(x, y3, color=(1.0, 0.0, 0.0), marker='o', markersize=8, markevery=slice(250, 5000, 250), label='$x_{BB}$')
# # ax.plot(x, y2, color=(0.00, 1.00, 0.00), marker='v', markersize=8, markevery=slice(0, 1000, 50), label='$x_{LF}$')
# # ax.plot(x, y1, color=(1.00, 0.00, 1.00), marker='s', markersize=8, markevery=slice(2000, 3000, 50), label='$x_{BP}$')
# # ax.plot(x, y0, color=(0.00, 0.00, 1.00), marker='+', markersize=8, markevery=slice(4000, 5000, 50), label='$x_{HF}$')
# # plt.xticks([0, 8000, 16000, 24000, 32000, 40000, 48000], ['0', '4', '8', '12', '16', '20', '24'])
# # plt.xlim([0, 48000])
# # ax.set(xlabel='Frequency (kHz)', ylabel='Amplitude')
# # ax.grid()
# # plt.legend(loc='upper right')
# # plt.show()
#
#
#
#
#
#
#
# #PSD-style plots
# fig, axs = plt.subplots(6, 3)
# act_var = 0
#
#
# colour_array = [(0.00, 0.0, 1.0),(1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
#
# plt.plot
#
#
# for hor in range(3):
#     for ver in range(6):
#         print(act_var)
#
#         axs[ver,hor].plot(f_bin_per, XP_av_act_db_smooth[act_var], color=colour_array[0], linestyle = 'solid' ,linewidth = 1)
#         axs[ver,hor].plot(f_bin_per, YP_av_act_db_smooth[act_var], color=colour_array[1], linestyle = 'dotted'  ,linewidth = 1)
#         axs[ver,hor].plot(f_bin_per, ZP_av_act_db_smooth[act_var], color=colour_array[2], linestyle = 'dashed'  ,linewidth = 1)
#         axs[ver,hor].set_title(act_text_in_order[act_var])
#         if hor == 0:
#             axs[ver,hor].set(ylabel='Power (dB)')
#         if ver == 5:
#             axs[ver,hor].set(xlabel='Frequency (Hz)')
#         axs[ver,hor].grid(True)
#         act_var += 1
#
# labels = ['x-axis', 'y-axis', 'z-axis']
# fig.legend(axs[ver,hor].get_lines(), labels, loc='upper right') # This works because lines same on each subplot
# fig.subplots_adjust(hspace = 1)
# fig.suptitle('Accelerometer')
# #fig.tight_layout()
# plt.show()


print("finished")