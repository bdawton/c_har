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
filter_select_range = 6

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

# Pull out subject for experiments. This needs to be reworked near the end so that subjects are used for cross-validation
n_subjectids = 4
rnd.seed(r_s)  # Does this affect any other seed in the code?
select_sujectids = rnd.sample(keep_list, n_subjectids)
watch_gyro_pull_subject = []
for pull_subject in watch_gyro_drop_subject:
    if pull_subject['subjectid'].unique() in select_sujectids:
        watch_gyro_pull_subject.append(pull_subject)

# Toggle the line below to switch between all and 4 subjects
watch_gyro_drop_subject = watch_gyro_pull_subject

# Non-hand-oriented activities:
# {walking, jogging, stairs, sitting, standing, kicking}

#nhoa_arr = np.array([0, 1, 2, 3, 4, 11])
nhoa_arr = np.array([0, 1])


# General hand-oriented activities:
# {dribbling, playing catch, typing, writing, clapping, brushing teeth, folding clothes}

#ghoa_arr = np.array([13, 12, 5, 14, 15, 6, 16])
ghoa_arr = np.array([13])

# Eating hand-oriented activities:
# {eating pasta, eating soup, eating sandwich, eating chips, drinking}

#ehoa_arr = np.array([9, 7, 17, 8, 10])
ehoa_arr = np.array([9])


count_track_var = 1
final_count_track_var = len(nhoa_arr) * len(ghoa_arr) * len(
    ehoa_arr) * filter_select_range  # We DON'T NEED TO USE len(filter_select_range), because that value is already the length (see the filter loop initialisation)

line_track_var = 0

# Loop through activities
for nh_a in nhoa_arr:
    for gh_a in ghoa_arr:
        for eh_a in ehoa_arr:

            three_act_selection = [nh_a, gh_a, eh_a]

            nhoa_c.append(nh_a)
            ghoa_c.append(gh_a)
            ehoa_c.append(eh_a)

            print(f"nhoa: {nh_a}")
            print(f"ghoa: {gh_a}")
            print(f"ehoa: {eh_a}")

            # Split each subject into activities
            sliced_act_subject_dict = {}
            sliced_subject_key_list = []

            for df_by_subject in watch_gyro_drop_subject:
                sliced_act_list = []
                len_sliced_act_list = []
                per_act_sliced_list = []

                for act_by_subject in act_label_list:

                    if act_by_subject in three_act_selection:

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

            # Loop through filter configuration
            for filter_select in range(filter_select_range):
                print(f"filter: {filter_select}")
                if filter_select == 0:
                    # LF
                    p_1 = 0.85
                    d_1 = 0
                    k_1 = 0
                    p_2 = 666
                    d_2 = 666
                    k_2 = 666
                    seq_num = 1
                elif filter_select == 1:
                    # BP
                    p_1 = 0.9
                    d_1 = 0
                    k_1 = 0
                    p_2 = 0.9
                    d_2 = 0
                    k_2 = 1
                    seq_num = 2
                elif filter_select == 2:
                    # HF
                    p_1 = 0.1
                    d_1 = 0
                    k_1 = 1
                    p_2 = 666
                    d_2 = 666
                    k_2 = 666
                    seq_num = 1
                elif filter_select == 3:
                    # BB
                    p_1 = 0.5
                    d_1 = 0
                    k_1 = 0
                    p_2 = 666
                    d_2 = 666
                    k_2 = 666
                    seq_num = 1
                elif filter_select == 4:
                    sequence_ones = np.ones(int(N))
                elif filter_select == 5:
                    sequence_ones = np.ones(int(N))

                if filter_select == 4 or filter_select == 5:
                    sequence = sequence_ones
                else:
                    sequence_root_1 = PRS.PRS(p_1, d_1, k_1, t, f_prs, 0)
                    sequence_1 = np.tile(sequence_root_1, int(f_sim / f_prs))
                    sequence_root_2 = PRS.PRS(p_2, d_2, k_2, t, f_prs, 0)
                    sequence_2 = np.tile(sequence_root_2, int(f_sim / f_prs))
                    if seq_num == 1:
                        sequence = sequence_1
                    elif seq_num == 2:
                        sequence = sequence_1 * sequence_2

                features_segment_list = []
                for sliced_subject in sliced_watch_gyro_drop_subject:
                    for sliced_activity in sliced_subject:
                        for sliced_segment in sliced_activity:
                            sliced_segment['PRS'] = sequence
                            sliced_segment['x_spread'] = sliced_segment['x'] * sliced_segment['PRS']
                            sliced_segment['x_spread'] = sliced_segment['x'] * sliced_segment['PRS']
                            sliced_segment['y_spread'] = sliced_segment['y'] * sliced_segment['PRS']
                            sliced_segment['z_spread'] = sliced_segment['z'] * sliced_segment['PRS']

                            if filter_select == 5:
                                sliced_segment[quant_sampled_columns] = sliced_segment[['x', 'y', 'z']]
                                cs_sliced_segment = sliced_segment[
                                    ['subjectid', 'activity', 'x_q_sampled', 'y_q_sampled', 'z_q_sampled']]
                            else:
                                lpf = signal.butter(2,  # order
                                                    f_cutoff,  # -3db freq
                                                    btype='lowpass',
                                                    fs=f_prs,  # sampling frequency
                                                    )
                                sliced_segment[filtered_columns] = signal.lfilter(lpf[0], lpf[1],
                                                                                  sliced_segment[spread_columns],
                                                                                  axis=0)
                                B = 12  # IN THIS SITUATION USING WATCH AND PHONE SENSORS, WHAT IS A SENSIBLE VALUE FOR B AND DEC POINTS?
                                scaling_factor = int(f_sim / f_prs)
                                downsample_interval = int(scaling_factor * f_prs / sample_freq)
                                start = 0
                                cs_sliced_segment = sliced_segment[['subjectid', 'activity', 'x_filtered', 'y_filtered',
                                                                    'z_filtered']].iloc[start::downsample_interval, :]
                                cs_sliced_segment.columns = ['subjectid', 'activity', 'x_sampled', 'y_sampled',
                                                             'z_sampled']
                                cs_sliced_segment[quant_sampled_columns] = quantiser(cs_sliced_segment[sampled_columns],
                                                                                     B, axis=0,
                                                                                     dec_points=5)  # Dec_points as 5 FOR NOW.Check with raw data and hardware later
                                cs_sliced_segment = cs_sliced_segment[
                                    ['subjectid', 'activity', 'x_q_sampled', 'y_q_sampled', 'z_q_sampled']]

                            cs_sliced_segment['euclidean'] = np.linalg.norm(cs_sliced_segment[quant_sampled_columns], axis=1)
                            features_raw, feature_names_raw = extract_features(cs_sliced_segment['euclidean'], shape=0)
                            features_resized = np.resize(features_raw, (1, 5))
                            sub_act_features = np.concatenate((np.array(
                                [cs_sliced_segment['subjectid'].iloc[0], cs_sliced_segment['activity'].iloc[0]]),
                                                               features_resized), axis=None)
                            feature_names = [feature_name + '_euclidian' for feature_name in feature_names_raw]
                            feature_columns = ['subjectid', 'activity'] + feature_names
                            features_segment = pd.DataFrame(columns=feature_columns)
                            features_segment.loc[0] = sub_act_features  # No idea why loc works here and iloc doesn't
                            features_segment_list.append(features_segment)

                df_extracted_features = pd.concat(features_segment_list)

                # Evaluation

                labels = df_extracted_features["activity"]
                sub_ids = df_extracted_features["subjectid"]
                features = df_extracted_features.iloc[:, 2:7]

                print(features.columns)

                # Evaluation
                iter_conf_mat = np.zeros([np.size(np.unique(labels)), np.size(np.unique(labels))], dtype=int)

                for iter in range(1):
                    # print(iter)

                    sub_ids_list = sub_ids.unique()
                    i = 0

                    s_id_conf_mat = np.zeros([np.size(np.unique(labels)), np.size(np.unique(labels))], dtype=int)

                    for s_id in sub_ids_list:
                        pull_list = np.delete(sub_ids_list, i)
                        X_train = features[sub_ids.isin(pull_list)]
                        X_test = features[sub_ids.isin(
                            [s_id])]  # use [] to make s_id list and use with .isin so it spits out dataframe
                        y_train = labels[sub_ids.isin(pull_list)]
                        y_test = labels[sub_ids.isin(
                            [s_id])]  # use [] to make s_id list and use with .isin so it spits out dataframe
                        print(f'iter: {iter}')
                        print(f's_id: {s_id}')
                        # model_1 = SVC(kernel='linear')
                        model_2 = RandomForestClassifier(
                            n_estimators=1000,
                            min_samples_leaf=3,
                            random_state=r_s,
                            #    max_features=10,
                            n_jobs=-1,
                        )

                        orig_model = model_2  # IF YOU USE THE SVM (model_1) , YOU NEED TO ADD A STANDARDIZ

                        score, conf_mat, fit_model, y_pred, y_true, unused_var = validate(X_train, y_train, X_test,
                                                                                          y_test, orig_model,
                                                                                          random_state=r_s)

                        s_id_conf_mat += conf_mat

                    iter_conf_mat += s_id_conf_mat
                # print("iter_conf_mat:")
                # print(iter_conf_mat)

                total_accuracy = iter_conf_mat.diagonal().sum() / iter_conf_mat.sum()
                print('total accuracy: ')
                print(total_accuracy)

                if filter_select == 0:
                    # LF
                    lpf_accuracy_list.append(total_accuracy)
                elif filter_select == 1:
                    # BP
                    bpf_accuracy_list.append(total_accuracy)
                elif filter_select == 2:
                    # HF
                    hpf_accuracy_list.append(total_accuracy)
                elif filter_select == 3:
                    # BB
                    bb_accuracy_list.append(total_accuracy)
                elif filter_select == 4:
                    # BB
                    ones_accuracy_list.append(total_accuracy)
                elif filter_select == 5:
                    # BB
                    no_cs_accuracy_list.append(total_accuracy)

                print(f"progress: {count_track_var} out of {final_count_track_var}")

                with open("log.txt", "a") as text_file:
                    text_file.write(f"filter: {filter_select}")
                    text_file.write("\n")
                    text_file.write(f"activities: {three_act_selection}")
                    text_file.write("\n")
                    text_file.write(f"progress: {count_track_var} out of {final_count_track_var}")
                    text_file.write("\n")

                count_track_var = count_track_var + 1

            line_results = f"{nhoa_c[line_track_var]},{ghoa_c[line_track_var]},{ehoa_c[line_track_var]},{lpf_accuracy_list[line_track_var]} , {bpf_accuracy_list[line_track_var]}, {hpf_accuracy_list[line_track_var]},{bb_accuracy_list[line_track_var]} ,{ones_accuracy_list[line_track_var]} ,{no_cs_accuracy_list[line_track_var]}"
            with open("result_log.txt", "a") as text_file:
                text_file.write(line_results)
                text_file.write("\n")
            line_track_var = line_track_var + 1

df_output_log = pd.DataFrame(
    zip(nhoa_c, ghoa_c, ehoa_c, lpf_accuracy_list, bpf_accuracy_list, hpf_accuracy_list, bb_accuracy_list,
        ones_accuracy_list, no_cs_accuracy_list),
    columns=['non_hand', 'general_hand', 'eating_hand', 'lpf_acc', 'bpf_acc', 'hpf_acc', 'bb_acc', 'ones_acc',
             'no_cs_acc'])  # Two lines because of columns as rows problem when intialising df

df_output_log.to_excel("gyro_allsub_3class_euclidian.xlsx")

with open("log.txt", "a") as text_file:
    text_file.write("finished")

print("finished")