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
    group_scooters = reg_table_data[reg_label_data == 2]
    psd_group_novehs = signal.periodogram(group_novehs, fs=f_sim, nfft=num_sample, axis=1)
    psd_group_cars = signal.periodogram(group_cars, fs=f_sim, nfft=num_sample, axis=1)
    psd_group_scooters = signal.periodogram(group_scooters, fs=f_sim, nfft=num_sample, axis=1)

    mean_group_novehs = psd_group_novehs[1].mean(axis=0)
    mean_group_cars = psd_group_cars[1].mean(axis=0)
    mean_group_scooter = psd_group_scooters[1].mean(axis=0)
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
    group_clear_scooters = clear_table_data[clear_label_data == 2]
    psd_group_clear_novehs = signal.periodogram(group_clear_novehs, fs=f_sim, nfft=num_sample, axis=1)
    psd_group_clear_cars = signal.periodogram(group_clear_cars, fs=f_sim, nfft=num_sample, axis=1)
    psd_group_clear_scooters = signal.periodogram(group_clear_scooters, fs=f_sim, nfft=num_sample, axis=1)

    mean_group_clear_novehs = psd_group_clear_novehs[1].mean(axis=0)
    mean_group_clear_cars = psd_group_clear_cars[1].mean(axis=0)
    mean_group_clear_scooters = psd_group_clear_scooters[1].mean(axis=0)
    mean_clear_novehs_list.append(mean_group_clear_novehs)
    mean_clear_cars_list.append(mean_group_clear_cars)
    mean_clear_scooters_list.append(mean_group_clear_scooters)

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
    group_rainy_scooters = rainy_table_data[rainy_label_data == 2]
    psd_group_rainy_novehs = signal.periodogram(group_rainy_novehs, fs=f_sim, nfft=num_sample, axis=1)
    psd_group_rainy_cars = signal.periodogram(group_rainy_cars, fs=f_sim, nfft=num_sample, axis=1)
    psd_group_rainy_scooters = signal.periodogram(group_rainy_scooters, fs=f_sim, nfft=num_sample, axis=1)

    mean_group_rainy_novehs = psd_group_rainy_novehs[1].mean(axis=0)
    mean_group_rainy_cars = psd_group_rainy_cars[1].mean(axis=0)
    mean_group_rainy_scooters = psd_group_rainy_scooters[1].mean(axis=0)
    mean_rainy_novehs_list.append(mean_group_rainy_novehs)
    mean_rainy_cars_list.append(mean_group_rainy_cars)
    mean_rainy_scooters_list.append(mean_group_rainy_scooters)

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
    group_windy_scooters = windy_table_data[windy_label_data == 2]
    psd_group_windy_novehs = signal.periodogram(group_windy_novehs, fs=f_sim, nfft=num_sample, axis=1)
    psd_group_windy_cars = signal.periodogram(group_windy_cars, fs=f_sim, nfft=num_sample, axis=1)
    psd_group_windy_scooters = signal.periodogram(group_windy_scooters, fs=f_sim, nfft=num_sample, axis=1)

    mean_group_windy_novehs = psd_group_windy_novehs[1].mean(axis=0)
    mean_group_windy_cars = psd_group_windy_cars[1].mean(axis=0)
    mean_group_windy_scooters = psd_group_windy_scooters[1].mean(axis=0)
    mean_windy_novehs_list.append(mean_group_windy_novehs)
    mean_windy_cars_list.append(mean_group_windy_cars)
    mean_windy_scooters_list.append(mean_group_windy_scooters)

mean_windy_novehs = np.array(mean_windy_novehs_list).mean(axis=0)
mean_windy_cars = np.array(mean_windy_cars_list).mean(axis=0)
mean_windy_scooters = np.array(mean_windy_scooters_list).mean(axis=0)

title_list = ['Cars', 'Scooters', 'No Vehicles']
plot_list = [mean_cars, mean_scooters, mean_novehs]
clear_plot_list = [mean_clear_cars, mean_clear_scooters, mean_clear_novehs]
rainy_plot_list = [mean_rainy_cars, mean_rainy_scooters, mean_rainy_novehs]
windy_plot_list = [mean_windy_cars, mean_windy_scooters, mean_windy_novehs]
psd_list_db_smooth = []
clear_psd_list_db_smooth = []
rainy_psd_list_db_smooth = []
windy_psd_list_db_smooth = []
f_bin_per = psd_group_novehs[0][1:]
shift_down_var = 100

plt.rcParams['font.family'] = 'Times'
plt.rcParams['font.size'] = 12
plt.rcParams['ps.useafm'] = True
plt.rcParams['pdf.use14corefonts'] = True
plt.rcParams['text.usetex'] = True

colour_array = [(1.00, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, 1.0, 0.0)]
marker_array = ['o','x','v']

for plot in plot_list:

    psd_list_db_smooth.append((moving_average.moving_average(10 * np.log10(plot[1:]), 400) - shift_down_var))

fig, ax = plt.subplots()
for plot_var in range(3):
    ax.plot(f_bin_per, psd_list_db_smooth[plot_var], color = colour_array[plot_var], marker = marker_array[plot_var], markevery=(4000,4000), label=title_list[plot_var])

plt.xticks([0, 4000, 8000, 12000, 16000, 20000, 24000], ['0', '4', '8', '12', '16', '20', '24'])
plt.xlim([0, 24000])
plt.ylim([-130,-50])
ax.set(xlabel='Frequency (kHz)', ylabel='Power (dB)')
ax.grid()
leg = plt.legend(loc='best')
leg.set_draggable(state=True)
fig.tight_layout()
fig.show()

for plot_clear in clear_plot_list:

    clear_psd_list_db_smooth.append((moving_average.moving_average(10 * np.log10(plot_clear[1:]), 400) - shift_down_var))

fig, ax = plt.subplots()
for plot_var in range(3):
    ax.plot(f_bin_per, clear_psd_list_db_smooth[plot_var], color = colour_array[plot_var], marker = marker_array[plot_var], markevery=(4000,4000), label=title_list[plot_var])

plt.xticks([0, 4000, 8000, 12000, 16000, 20000, 24000], ['0', '4', '8', '12', '16', '20', '24'])
plt.xlim([0, 24000])
plt.ylim([-130,-50])
ax.set(xlabel='Frequency (kHz)', ylabel='Power (dB)')
ax.grid()
fig.legend(loc='upper right')
fig.tight_layout()
fig.show()

for plot_rainy in rainy_plot_list:

    rainy_psd_list_db_smooth.append((moving_average.moving_average(10 * np.log10(plot_rainy[1:]), 400) - shift_down_var))

fig, ax = plt.subplots()
for plot_var in range(3):
    ax.plot(f_bin_per, rainy_psd_list_db_smooth[plot_var], color = colour_array[plot_var], marker = marker_array[plot_var], markevery=(4000,4000), label=title_list[plot_var])

plt.xticks([0, 4000, 8000, 12000, 16000, 20000, 24000], ['0', '4', '8', '12', '16', '20', '24'])
plt.xlim([0, 24000])
plt.ylim([-130,-50])
ax.set(xlabel='Frequency (kHz)', ylabel='Power (dB)')
ax.grid()
fig.legend(loc='upper right')
fig.tight_layout()
fig.show()

for plot_windy in windy_plot_list:

    windy_psd_list_db_smooth.append((moving_average.moving_average(10 * np.log10(plot_windy[1:]), 400) - shift_down_var))

fig, ax = plt.subplots()
for plot_var in range(3):
    ax.plot(f_bin_per, windy_psd_list_db_smooth[plot_var], color = colour_array[plot_var], marker = marker_array[plot_var], markevery=(4000,4000), label=title_list[plot_var])

plt.xticks([0, 4000, 8000, 12000, 16000, 20000, 24000], ['0', '4', '8', '12', '16', '20', '24'])
plt.xlim([0, 24000])
plt.ylim([-130,-50])
ax.set(xlabel='Frequency (kHz)', ylabel='Power (dB)')
ax.grid()
fig.legend(loc='upper right')
fig.tight_layout()
fig.show()



print("finished")