# I need to drop subjects, and then split each subect into activities, and cut a into 10s per activity, then combine into subject. Then do some other kind of test - like cut off stuff outside of quartiles?
# Then finally I have per subject data. From there I can figure out how to do personal, and impersonal per/activity test
# Also re-write the code to remove anything I don't need'

import os
import glob
import numpy as np
import scipy as sp
import matplotlib
import seaborn as sns
import sklearn
import pandas as pd
import tailored_PRS as PRS
from quantiser import quantiser
from scipy import signal
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import StratifiedKFold
from imblearn.under_sampling import RandomUnderSampler
from feature_extraction import extract_features
from evaluate_validate import validate
import matplotlib.pyplot as plt
import copy
import random as rnd

print(pd.__version__)
print(np.__version__)
print(sp.__version__)
print(matplotlib.__version__)
print(sns.__version__)
print(sklearn.__version__)


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
fft_range = int(N / 2)

f_sim = rate
f_prs = rate
sample_freq = f_prs / 4
f_cutoff = sample_freq / 2

nhoa_c = []
ghoa_c = []
ehoa_c = []

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
accel_watch_list = glob.glob('wisdm-dataset_mod/raw/watch/accel' + '/*')


# Load in watch accel data
big_data_accel_watch = []
for entry in accel_watch_list:
    data_accel_watch = pd.read_csv(entry, header=None, lineterminator=";", low_memory=False, parse_dates=True)
    big_data_accel_watch.append(data_accel_watch)

# Clean up and reformat data
big_data_column_names = ['subjectid', 'activity', 'timestamp', 'x', 'y', 'z']
df_big_data_accel_watch = pd.concat(big_data_accel_watch)
df_big_data_accel_watch.columns = big_data_column_names
df_big_data_accel_watch.dropna(axis=0, how="any", thresh=None, subset=None, inplace=True)
df_big_data_accel_watch = df_big_data_accel_watch.replace('\n', '', regex=True)
df_big_data_accel_watch = df_big_data_accel_watch.astype({"subjectid": str})

act_label_list = range(len(df_big_data_accel_watch['activity'].unique()))
type_ids = dict(zip(df_big_data_accel_watch['activity'].unique(), act_label_list))  # Doesn't matter which?
df_big_data_accel_watch = df_big_data_accel_watch.replace({"activity": type_ids})

# Pull out subjects that don't contain all activities (is that even possible?)
watch_accel_drop_subject = []
keep_drop = []
keep_list = []
ind_subjectids = np.unique(df_big_data_accel_watch["subjectid"])

for i_si in ind_subjectids:
    data_drop_subject = df_big_data_accel_watch[df_big_data_accel_watch["subjectid"] == i_si]
    if set(type_ids.values()).issubset(set(data_drop_subject['activity'])):
        # print('keep')
        k_d = (i_si, 'keep')
        keep_list.append(i_si)
        watch_accel_drop_subject.append(data_drop_subject)
    else:
        # print('drop')
        k_d = (i_si, 'drop')
    keep_drop.append(k_d)
df_keep_drop = pd.DataFrame(keep_drop, columns=['subjectid', 'k_d'])

# Pull out subject for experiments. This needs to be reworked near the end so that subjects are used for cross-validation
n_subjectids = 4
rnd.seed(r_s)  # Does this affect any other seed in the code?
select_sujectids = rnd.sample(keep_list, n_subjectids)
watch_accel_pull_subject = []
for pull_subject in watch_accel_drop_subject:
    if pull_subject['subjectid'].unique() in select_sujectids:
        watch_accel_pull_subject.append(pull_subject)

# Toggle the line below to switch between all and 4 subjects
#watch_accel_drop_subject = watch_accel_pull_subject

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
final_count_track_var = len(nhoa_arr) * len(ghoa_arr) * len(
    ehoa_arr)

line_track_var = 0

total_accuracy_c = []

# Loop through activities


all_act_selection = [0, 1, 2, 3, 4, 11, 13, 12, 5, 14, 15, 6, 16, 9, 7, 17, 8, 10]


# print(f"nhoa: {nh_a}")
# print(f"ghoa: {gh_a}")
# print(f"ehoa: {eh_a}")

# Split each subject into activities
sliced_act_subject_dict = {}
sliced_subject_key_list = []

# Split each subject into activities
sliced_act_subject_dict = {}
sliced_subject_key_list = []

for df_by_subject in watch_accel_drop_subject:
    sliced_act_list = []
    len_sliced_act_list = []
    per_act_sliced_list = []

    for act_by_subject in act_label_list:

        if act_by_subject in all_act_selection:

            df_by_subject_act = df_by_subject[df_by_subject["activity"] == act_by_subject]
            df_by_subject_act.set_index('timestamp', inplace=True)
            df_by_subject_act.sort_index()
            df_by_subject_act.index = pd.to_datetime(df_by_subject_act.index, unit='ns', errors='coerce')
            df_by_subject_act.dropna()
            df_by_subject_act_grouped = df_by_subject_act.groupby(pd.Grouper(freq='10s', origin='start'))

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

    subject_key = df_by_subject["subjectid"].unique()[0]
    sliced_subject_key_list.append(subject_key)
    sliced_act_subject_dict[subject_key] = sliced_act_list  # 0 length entries haven't been dropped

sliced_act_subject_list = list(sliced_act_subject_dict.values())

# Pull out subjects that don't contain any (or a minimum amount? Like fall between a certain range?)
sliced_watch_accel_drop_subject = []
s_k_list = []


for s_item in sliced_act_subject_list:
    if len(s_item[0]) >= 10:  # Let's just say minimum length 10
        # print('keep')
        s_k = (s_item[0][0]['subjectid'].unique()[0], 'keep')
        s_k_list.append(s_k)
        sliced_watch_accel_drop_subject.append(s_item)


a_list = []
for a in sliced_watch_accel_drop_subject:
    ac = copy.copy(a)
    aa = ac.pop()
    b_counts = []
    b_vals = []
    b_subjects = []
    for b in aa:
        #counts = int(b['activity'].value_counts())
        val = b['activity'][0]
        subject = b['subjectid'][0]
        #print(val)
        #print(counts)
        #b_counts.append(counts)
        b_vals.append(val)
        b_subjects.append(subject)
    df_b = pd.DataFrame({'subject' : subject, 'activity' : b_vals}) #, 'counts' : b_counts})
    a_list.append(df_b)
df_a = pd.concat(a_list)
df_a_g = df_a.groupby(['subject']).value_counts()
df_a_g.sort_index(inplace = True)
df_a_r = df_a_g.reset_index()
df_a_s = df_a_r.sort_values(['subject', 'activity'], ascending=[True, True])

df_f = pd.DataFrame(index=df_a['subject'].unique(), columns = [df_a['activity'].unique()])
fill_var = 0
for su in df_a['subject'].unique():
    temp_step = np.array(df_a_s[0].loc[df_a_s['subject'] == su])
    print(su)
    df_f.loc[su] = temp_step
    fill_var = fill_var + 18

df_f.to_excel("total_data_accel.xlsx")

print("finished")
