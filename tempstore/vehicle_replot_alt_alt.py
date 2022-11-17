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

reg_novehs_list = []
reg_cars_list = []
reg_scooters_list = []

mean_reg_novehs_list = []
mean_reg_cars_list = []
mean_reg_scooters_list = []

reg_groups = ['G1', 'G2', 'G4', 'G5', 'G8', 'G11', 'G13','G6', 'G7', 'G16','G3', 'G9', 'G12', 'G14']

for g_reg in reg_groups:
    reg_table_data = big_table_data[g_reg]
    reg_label_data = big_table_label[g_reg]
    reg_group_novehs = reg_table_data[reg_label_data == 0]
    reg_group_cars = reg_table_data[reg_label_data == 1]
    reg_group_scooters = reg_table_data[reg_label_data == 2]
    reg_novehs_list.append(reg_group_novehs)
    reg_cars_list.append(reg_group_cars)
    reg_scooters_list.append(reg_group_scooters)

psd_reg_group_novehs = signal.periodogram(np.concatenate(reg_novehs_list, axis = 0), fs=f_sim, nfft=num_sample, axis=1)
psd_reg_group_cars = signal.periodogram(np.concatenate(reg_cars_list, axis = 0), fs=f_sim, nfft=num_sample, axis=1)
psd_reg_group_scooters = signal.periodogram(np.concatenate(reg_scooters_list, axis = 0), fs=f_sim, nfft=num_sample, axis=1)
mean_reg_novehs = psd_reg_group_novehs[1].mean(axis=0)
mean_reg_cars = psd_reg_group_cars[1].mean(axis=0)
mean_reg_scooters = psd_reg_group_scooters[1].mean(axis=0)

clear_groups = ['G1', 'G2', 'G4', 'G5', 'G8', 'G11', 'G13']
clear_novehs_list = []
clear_cars_list = []
clear_scooters_list = []

mean_clear_novehs_list = []
mean_clear_cars_list = []
mean_clear_scooters_list = []

for g_clear in clear_groups:
    clear_table_data = big_table_data[g_clear]
    clear_label_data = big_table_label[g_clear]
    clear_group_novehs = clear_table_data[clear_label_data == 0]
    clear_group_cars = clear_table_data[clear_label_data == 1]
    clear_group_scooters = clear_table_data[clear_label_data == 2]
    clear_novehs_list.append(clear_group_novehs)
    clear_cars_list.append(clear_group_cars)
    clear_scooters_list.append(clear_group_scooters)

psd_clear_group_novehs = signal.periodogram(np.concatenate(clear_novehs_list, axis = 0), fs=f_sim, nfft=num_sample, axis=1)
psd_clear_group_cars = signal.periodogram(np.concatenate(clear_cars_list, axis = 0), fs=f_sim, nfft=num_sample, axis=1)
psd_clear_group_scooters = signal.periodogram(np.concatenate(clear_scooters_list, axis = 0), fs=f_sim, nfft=num_sample, axis=1)
mean_clear_novehs = psd_clear_group_novehs[1].mean(axis=0)
mean_clear_cars = psd_clear_group_cars[1].mean(axis=0)
mean_clear_scooters = psd_clear_group_scooters[1].mean(axis=0)

rainy_groups = ['G6', 'G7', 'G16']
rainy_novehs_list = []
rainy_cars_list = []
rainy_scooters_list = []

mean_rainy_novehs_list = []
mean_rainy_cars_list = []
mean_rainy_scooters_list = []

for g_rainy in rainy_groups:
    rainy_table_data = big_table_data[g_rainy]
    rainy_label_data = big_table_label[g_rainy]
    rainy_group_novehs = rainy_table_data[rainy_label_data == 0]
    rainy_group_cars = rainy_table_data[rainy_label_data == 1]
    rainy_group_scooters = rainy_table_data[rainy_label_data == 2]
    rainy_novehs_list.append(rainy_group_novehs)
    rainy_cars_list.append(rainy_group_cars)
    rainy_scooters_list.append(rainy_group_scooters)

psd_rainy_group_novehs = signal.periodogram(np.concatenate(rainy_novehs_list, axis = 0), fs=f_sim, nfft=num_sample, axis=1)
psd_rainy_group_cars = signal.periodogram(np.concatenate(rainy_cars_list, axis = 0), fs=f_sim, nfft=num_sample, axis=1)
psd_rainy_group_scooters = signal.periodogram(np.concatenate(rainy_scooters_list, axis = 0), fs=f_sim, nfft=num_sample, axis=1)
mean_rainy_novehs = psd_rainy_group_novehs[1].mean(axis=0)
mean_rainy_cars = psd_rainy_group_cars[1].mean(axis=0)
mean_rainy_scooters = psd_rainy_group_scooters[1].mean(axis=0)


windy_groups = ['G3', 'G9', 'G12', 'G14']
windy_novehs_list = []
windy_cars_list = []
windy_scooters_list = []

mean_windy_novehs_list = []
mean_windy_cars_list = []
mean_windy_scooters_list = []

for g_windy in windy_groups:
    windy_table_data = big_table_data[g_windy]
    windy_label_data = big_table_label[g_windy]
    windy_group_novehs = windy_table_data[windy_label_data == 0]
    windy_group_cars = windy_table_data[windy_label_data == 1]
    windy_group_scooters = windy_table_data[windy_label_data == 2]
    windy_novehs_list.append(windy_group_novehs)
    windy_cars_list.append(windy_group_cars)
    windy_scooters_list.append(windy_group_scooters)

psd_windy_group_novehs = signal.periodogram(np.concatenate(windy_novehs_list, axis = 0), fs=f_sim, nfft=num_sample, axis=1)
psd_windy_group_cars = signal.periodogram(np.concatenate(windy_cars_list, axis = 0), fs=f_sim, nfft=num_sample, axis=1)
psd_windy_group_scooters = signal.periodogram(np.concatenate(windy_scooters_list, axis = 0), fs=f_sim, nfft=num_sample, axis=1)
mean_windy_novehs = psd_windy_group_novehs[1].mean(axis=0)
mean_windy_cars = psd_windy_group_cars[1].mean(axis=0)
mean_windy_scooters = psd_windy_group_scooters[1].mean(axis=0)

title_list = ['Cars', 'Scooters', 'No Vehicles']
reg_plot_list = [mean_reg_cars, mean_reg_scooters, mean_reg_novehs]
clear_plot_list = [mean_clear_cars, mean_clear_scooters, mean_clear_novehs]
rainy_plot_list = [mean_rainy_cars, mean_rainy_scooters, mean_rainy_novehs]
windy_plot_list = [mean_windy_cars, mean_windy_scooters, mean_windy_novehs]
reg_psd_list_db_smooth = []
clear_psd_list_db_smooth = []
rainy_psd_list_db_smooth = []
windy_psd_list_db_smooth = []
f_bin_per = psd_reg_group_novehs[0][1:]
shift_down_var = 100

plt.rcParams['font.family'] = 'Times'
plt.rcParams['font.size'] = 16
plt.rcParams['ps.useafm'] = True
plt.rcParams['pdf.use14corefonts'] = True
plt.rcParams['text.usetex'] = True

colour_array = [(1.00, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, 1.0, 0.0)]
marker_array = ['o','x','v']

for reg_plot in reg_plot_list:
    reg_psd_list_db_smooth.append((moving_average.moving_average(10 * np.log10(reg_plot[1:]), 400) - shift_down_var))

fig, ax = plt.subplots()
for plot_var in range(3):
    ax.plot(f_bin_per, reg_psd_list_db_smooth[plot_var], color = colour_array[plot_var], marker = marker_array[plot_var], markevery=(4000,4000), label=title_list[plot_var])

plt.xticks([0, 4000, 8000, 12000, 16000, 20000, 24000], ['0', '4', '8', '12', '16', '20', '24'])
plt.xlim([0, 24000])
plt.ylim([-130,-50])
ax.set(xlabel='Frequency (kHz)', ylabel='Power (dB)')
ax.grid()
leg = plt.legend(loc='best')
leg.set_draggable(state=True)
plt.tight_layout()
fig.show()


for clear_plot in clear_plot_list:
    clear_psd_list_db_smooth.append((moving_average.moving_average(10 * np.log10(clear_plot[1:]), 400) - shift_down_var))

fig, ax = plt.subplots()
for plot_var in range(3):
    ax.plot(f_bin_per, clear_psd_list_db_smooth[plot_var], color = colour_array[plot_var], marker = marker_array[plot_var], markevery=(4000,4000), label=title_list[plot_var])

plt.xticks([0, 4000, 8000, 12000, 16000, 20000, 24000], ['0', '4', '8', '12', '16', '20', '24'])
plt.xlim([0, 24000])
plt.ylim([-130,-50])
ax.set(xlabel='Frequency (kHz)', ylabel='Power (dB)')
ax.grid()
leg = plt.legend(loc='best')
leg.set_draggable(state=True)
plt.tight_layout()
fig.show()


for windy_plot in windy_plot_list:
    windy_psd_list_db_smooth.append((moving_average.moving_average(10 * np.log10(windy_plot[1:]), 400) - shift_down_var))

fig, ax = plt.subplots()
for plot_var in range(3):
    ax.plot(f_bin_per, windy_psd_list_db_smooth[plot_var], color = colour_array[plot_var], marker = marker_array[plot_var], markevery=(4000,4000), label=title_list[plot_var])

plt.xticks([0, 4000, 8000, 12000, 16000, 20000, 24000], ['0', '4', '8', '12', '16', '20', '24'])
plt.xlim([0, 24000])
plt.ylim([-130,-50])
ax.set(xlabel='Frequency (kHz)', ylabel='Power (dB)')
ax.grid()
leg = plt.legend(loc='best')
leg.set_draggable(state=True)
plt.tight_layout()
fig.show()


for rainy_plot in rainy_plot_list:
    rainy_psd_list_db_smooth.append((moving_average.moving_average(10 * np.log10(rainy_plot[1:]), 400) - shift_down_var))

fig, ax = plt.subplots()
for plot_var in range(3):
    ax.plot(f_bin_per, rainy_psd_list_db_smooth[plot_var], color = colour_array[plot_var], marker = marker_array[plot_var], markevery=(4000,4000), label=title_list[plot_var])

plt.xticks([0, 4000, 8000, 12000, 16000, 20000, 24000], ['0', '4', '8', '12', '16', '20', '24'])
plt.xlim([0, 24000])
plt.ylim([-130,-50])
ax.set(xlabel='Frequency (kHz)', ylabel='Power (dB)')
ax.grid()
leg = plt.legend(loc='best')
leg.set_draggable(state=True)
plt.tight_layout()
fig.show()


print("finished")