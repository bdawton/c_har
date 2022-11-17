import os
import glob
import numpy as np
import pandas as pd
import tailored_prs as prs
from quantiser import quantiser
from scipy import signal
from sklearn.ensemble import RandomForestClassifier
from itertools import chain
from feature_extraction import extract_features
from evaluate_validate import validate
import random as rnd

suppress_warning_var = 1  # TRY AND DELETE THIS IF YOU CAN
if suppress_warning_var == 1:
    pd.options.mode.chained_assignment = None  # default='warn'
    print(
        "Supressing the: \"SettingWithCopyWarning: A value is trying to be set on a copy of a slice from a DataFrame.\"")
    print("regarding index sorting of pulled subject and activity dfs and the creation of prsxInput columns of df")

r_s = 0
t = 10.0  # CAN MAYBE MOVE ALL OF THIS LATER?
rate = 20
N = int(rate * t)
fft_range = int(N / 2)
rnd.seed(r_s)

f_sim = rate
f_prs = rate
sample_freq = f_prs / 4
f_cutoff = sample_freq / 2

n_subject_ids = 4

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
sensor_list = glob.glob('wisdm-dataset-modified/raw/watch/accel' + '/*')

# USE the arrays as inputs to a function BILLY SORT OUT THE ACTIVITY KEY SOMEHOW. MAYBE FIRST DEFINE THE DICTIONNARY. YOULL HAVE TO DO SOME SMALL CHANGES BUT COULD BE WORTH IT
# Non-hand-oriented activities:
nhoa_dict = {0: 'Walking', 1: 'Jogging', 2: 'Stairs', 3: 'Sitting', 4: 'Standing', 11: 'Kicking'}
nhoa_arr = np.array([0, 1, 2, 3, 4, 11])
# nhoa_arr = np.array([0])

# General hand-oriented activities:
# {typing, brushing teeth, playing catch, dribbling ball, writing, clapping , folding clothes}
ghoa_dict = {5: 'Typing', 6: 'Brushing Teeth', 12: 'Playing Catch', 13: 'Dribbling Ball', 14: 'Writing', 15: 'Clapping',
             16: 'Folding Clothes'}
ghoa_arr = np.array([5, 6, 12, 13, 14, 15, 16])
# ghoa_arr = np.array([13])

# Eating hand-oriented activities:
# {eating soup, eating chips, eating pasta, drinking, eating sandwich}
ehoa_dict = {7: 'Eating Soup', 8: 'Eating Chips', 9: 'Eating Pasta', 10: 'Drinking', 17: 'Eating Sandwich'}

ehoa_arr = np.array([7, 8, 9, 10, 17])
# ehoa_arr = np.array([9])

count_track_var = 1
final_count_track_var = len(nhoa_arr) * len(ghoa_arr) * len(ehoa_arr)
line_track_var = 0
total_accuracy_c = []


def load_prepare(raw_data, n_subject_ids):
    # Load in sensor data
    big_data = []
    for entry in raw_data:
        data = pd.read_csv(entry, header=None, lineterminator=";", low_memory=False, parse_dates=True)
        big_data.append(data)

    # Clean up and reformat data
    big_data_column_names = ['subjectid', 'activity', 'timestamp', 'x', 'y', 'z']
    df_big_data = pd.concat(big_data)
    df_big_data.columns = big_data_column_names
    df_big_data.dropna(axis=0, how="any", thresh=None, subset=None, inplace=True)
    df_big_data = df_big_data.replace('\n', '', regex=True)
    df_big_data = df_big_data.astype({"subjectid": str})

    # Relabel activities
    act_label_list = range(len(df_big_data['activity'].unique()))
    type_ids = dict(zip(df_big_data['activity'].unique(), act_label_list))  # Doesn't matter which?
    df_big_data = df_big_data.replace({"activity": type_ids})

    # Pull out subjects that don't contain all activities (is that even possible?)
    df_big_data_dropped_subject = []
    keep_list = []
    ind_subject_ids = np.unique(df_big_data["subjectid"])
    for i_si in ind_subject_ids:
        keep_list.append(i_si)
        data_drop_subject = df_big_data[df_big_data["subjectid"] == i_si]
        if set(type_ids.values()).issubset(set(data_drop_subject['activity'])):
            df_big_data_dropped_subject.append(data_drop_subject)

    # Pull out a random subsample of #n subjects for experiments. (If you need to reduce computation time for instance)
    select_subject_ids = rnd.sample(keep_list, n_subject_ids)
    df_big_data_dropped_pulled_subject = []
    for pull_subject in df_big_data_dropped_subject:
        if pull_subject['subjectid'].unique() in select_subject_ids:
            df_big_data_dropped_pulled_subject.append(pull_subject)

    return df_big_data_dropped_pulled_subject, act_label_list


def three_activity_selection(nhoa_arr, ghoa_arr, ehoa_arr):
    # Loop through activities
    three_act_list = []
    for nh_a in nhoa_arr:
        for gh_a in ghoa_arr:
            for eh_a in ehoa_arr:
                three_act_list.append([nh_a, gh_a, eh_a])

    three_act_array = np.array(three_act_list)
    # Keep both array and list, but figure out which one is best later!
    return three_act_list, three_act_array


prepared_data, act_label_list = load_prepare(sensor_list, n_subject_ids)
three_act_list, three_act_array = three_activity_selection(nhoa_arr, ghoa_arr, ehoa_arr)

#======== UP TO HERE EVERYTHING SEEMS OK
# Billy FROM HERE. YOU ARE TRYING TO DO ALL THE SLICING TOGETHER FIRST BEFORE SPLITTING INTO THE ACTIVITIES LATER ON
#for three_act_selection in three_act_list: #Is separating dateset really necessary at this stage? Can I do all the slicing and shit first


sliced_act_subject_dict = {}
sliced_subject_key_list = []
loop_var = 0
subjectid_list = []
activity_list = []
timestamp_list=[]
axis_list = []
sensor_reading_list = []
for df_by_subject in prepared_data: #yes you need to split by subject here (you will do ALL subjects in dataset, not just triple selection) to avoid cross subject contamination.
    sliced_act_list = []
    len_sliced_act_list = []
    per_act_sliced_list = []
    per_act_sliced_list_test = []
    for act_by_subject in act_label_list:
        df_by_subject_act = df_by_subject[df_by_subject["activity"] == act_by_subject]
        df_by_subject_act.set_index('timestamp', inplace=True)
        df_by_subject_act.sort_index()
        df_by_subject_act.index = pd.to_datetime(df_by_subject_act.index, unit='ns', errors='coerce')
        df_by_subject_act.dropna()
        df_by_subject_act_grouped = df_by_subject_act.groupby(pd.Grouper(freq='10s', origin='start'))

#========= CAN I REPLACE ALL THIS WITH AN APPLY COMMAND

        per_act_slice_counter = 0
        pull_sliced_list = []

#Remove any groups that weren't sampled properly i.e: N not equal to 200 (period*sample rate)


        for group in df_by_subject_act_grouped:
            if len(group[1]) == N:  # Sequence equal to N?
                subjectid_list.append(3 * [group[1]['subjectid'][0]])
                timestamp_list.append(3 * [group[1]['x'].index[0]]) #extract just time info
                activity_list.append(3 * [group[1]['activity'][0]])
                axis_list.append(['x','y','z'])
                sensor_reading_list.append([np.array(group[1]['x'].reset_index(drop=True)),np.array(group[1]['y'].reset_index(drop=True)),np.array(group[1]['z'].reset_index(drop=True))])

subjectid_list = list(chain.from_iterable(subjectid_list))
timestamp_list = list(chain.from_iterable(timestamp_list))
activity_list = list(chain.from_iterable(activity_list))
axis_list = list(chain.from_iterable(axis_list))
sensor_reading_list = list(chain.from_iterable(sensor_reading_list))

df_prepared_data = pd.DataFrame({'subjectid':subjectid_list, 'timestamp':timestamp_list, 'activity':activity_list ,'axis': axis_list, 'sensor_reading' :sensor_reading_list})

#BILLY YOU GOT TO HERE

# Pull out subjects that don't contain any (or a minimum amount? Like fall between a certain range?)
drop_subject = []

for subject_id in df_prepared_data['subjectid'].unique():
    activity_counts = df_prepared_data[df_prepared_data['subjectid']==subject_id]['activity'].value_counts()
    if activity_counts.min() < 10: #This is set to 10 as minimum number of segments for a subject before explusion. Can be varied later if needed
        drop_subject.append(subject_id)

df_prepared_data.drop(df_prepared_data[df_prepared_data['subjectid'].isin(drop_subject)].index, inplace=True)


#======= OK BILLY YOU GOT TO HERE!

 #
 # s_item = 0
 #    #print(len(s_item[0]))
 #    if len(s_item[0]) >= 10:  # This is the minimum amount of datapoints requried for the lass. SO this subject needs at least 10 slices of activity "bla"
 #        #print('keep')
 #        s_k = (s_item[0][0]['subjectid'].unique()[0], 'keep')
 #        s_k_list.append(s_k)
 #        sliced_drop_subject.append(s_item)
# ==== up to here is fine I think, so clean up and figure out where the extra list layer is coming from.

#   lf_prs_params = {'p_1': 0.85, 'd_1': 0, 'k_1': 0, 'p_2': 666, 'd_2': 666, 'k_2': 666, 'seq_num': 1}
#             mf_prs_params = {'p_1': 0.9, 'd_1': 0, 'k_1': 0, 'p_2': 0.9, 'd_2': 0, 'k_2': 1, 'seq_num': 2}
#             hf_prs_params = {'p_1': 0.1, 'd_1': 0, 'k_1': 1, 'p_2': 666, 'd_2': 666, 'k_2': 666, 'seq_num': 1}
#             bb_prs_params = {'p_1': 0.5, 'd_1': 0, 'k_1': 0, 'p_2': 666, 'd_2': 666, 'k_2': 666, 'seq_num': 1}
#
#             # BILLY CHANGE THESE ACCORDING TO RESULTS
#
#             # XAXIS is LPF and only uses ONE sequence, be careful with number of sequences
#             sequence_root_1 = prs.prs(lf_prs_params['p_1'], lf_prs_params['d_1'], lf_prs_params['k_1'], t, f_prs, 0)
#             sequence_1 = np.tile(sequence_root_1, int(f_sim / f_prs))
#             sequence_root_2 = prs.prs(lf_prs_params['p_2'], lf_prs_params['d_2'], lf_prs_params['k_2'], t, f_prs, 0)
#             sequence_2 = np.tile(sequence_root_2, int(f_sim / f_prs))
#             seq_num = lf_prs_params['seq_num']
#             if seq_num == 1:
#                 x_sequence = sequence_1  # <---- HERE IS WHERE I SET X,Y,Z AXIS
#             elif seq_num == 2:
#                 x_sequence = sequence_1 * sequence_2  # <---- OR HERE IF MF_prs
#
#             # YAXIS is HPF and only uses ONE sequence, be careful with number of sequences
#             sequence_root_1 = prs.prs(hf_prs_params['p_1'], hf_prs_params['d_1'], hf_prs_params['k_1'], t, f_prs, 0)
#             sequence_1 = np.tile(sequence_root_1, int(f_sim / f_prs))
#             sequence_root_2 = prs.prs(hf_prs_params['p_2'], hf_prs_params['d_2'], hf_prs_params['k_2'], t, f_prs, 0)
#             sequence_2 = np.tile(sequence_root_2, int(f_sim / f_prs))
#             seq_num = hf_prs_params['seq_num']
#             if seq_num == 1:
#                 y_sequence = sequence_1  # <---- HERE IS WHERE I SET X,Y,Z AXIS
#             elif seq_num == 2:
#                 y_sequence = sequence_1 * sequence_2  # <---- OR HERE IF MF_prs
#
#             # ZAXIS is HPF and only uses ONE sequence, be careful with number of sequences
#             sequence_root_1 = prs.prs(hf_prs_params['p_1'], hf_prs_params['d_1'], hf_prs_params['k_1'], t, f_prs, 0)
#             sequence_1 = np.tile(sequence_root_1, int(f_sim / f_prs))
#             sequence_root_2 = prs.prs(hf_prs_params['p_2'], hf_prs_params['d_2'], hf_prs_params['k_2'], t, f_prs, 0)
#             sequence_2 = np.tile(sequence_root_2, int(f_sim / f_prs))
#             seq_num = hf_prs_params['seq_num']
#             if seq_num == 1:
#                 z_sequence = sequence_1  # <---- HERE IS WHERE I SET X,Y,Z AXIS
#             elif seq_num == 2:
#                 z_sequence = sequence_1 * sequence_2  # <---- OR HERE IF MF_prs
#
#             features_segment_list = []
#             for sliced_subject in sliced_drop_subject:
#                 for sliced_activity in sliced_subject:
#                     for sliced_segment in sliced_activity:
#                         sliced_segment['x_prs'] = x_sequence
#                         sliced_segment['y_prs'] = y_sequence
#                         sliced_segment['z_prs'] = z_sequence
#                         sliced_segment['x_spread'] = sliced_segment['x'] * sliced_segment['x_prs']
#                         sliced_segment['y_spread'] = sliced_segment['y'] * sliced_segment['y_prs']
#                         sliced_segment['z_spread'] = sliced_segment['z'] * sliced_segment['z_prs']
#
#                         lpf = signal.butter(2,  # order
#                                             f_cutoff,  # -3db freq
#                                             btype='lowpass',
#                                             fs=f_prs,  # sampling frequency
#                                             )
#                         sliced_segment[filtered_columns] = signal.lfilter(lpf[0], lpf[1],
#                                                                           sliced_segment[spread_columns],
#                                                                           axis=0)
#                         B = 12  # IN THIS SITUATION USING WATCH AND PHONE SENSORS, WHAT IS A SENSIBLE VALUE FOR B AND DEC POINTS?
#                         scaling_factor = int(f_sim / f_prs)
#                         downsample_interval = int(scaling_factor * f_prs / sample_freq)
#                         start = 0
#                         cs_sliced_segment = sliced_segment[['subjectid', 'activity', 'x_filtered', 'y_filtered',
#                                                             'z_filtered']].iloc[start::downsample_interval, :]
#                         cs_sliced_segment.columns = ['subjectid', 'activity', 'x_sampled', 'y_sampled',
#                                                      'z_sampled']
#                         cs_sliced_segment[quant_sampled_columns] = quantiser(cs_sliced_segment[sampled_columns],
#                                                                              B, axis=0,
#                                                                              dec_points=5)  # Dec_points as 5 FOR NOW.Check with raw data and hardware later
#                         cs_sliced_segment = cs_sliced_segment[
#                             ['subjectid', 'activity', 'x_q_sampled', 'y_q_sampled', 'z_q_sampled']]
#
#                         features_raw, feature_names_raw = extract_features(cs_sliced_segment[quant_sampled_columns])
#                         features_resized = np.resize(features_raw, (1, 15))
#                         sub_act_features = np.concatenate((np.array(
#                             [cs_sliced_segment['subjectid'].iloc[0], cs_sliced_segment['activity'].iloc[0]]),
#                                                            features_resized), axis=None)
#                         feature_names = [letter + feature_name for letter in ['x_', 'y_', 'z_']
#                                          for feature_name in feature_names_raw]
#                         feature_columns = ['subjectid', 'activity'] + feature_names
#                         features_segment = pd.DataFrame(columns=feature_columns)
#                         features_segment.loc[0] = sub_act_features  # No idea why loc works here and iloc doesn't
#                         features_segment_list.append(features_segment)
#
#             df_extracted_features = pd.concat(features_segment_list)
#
#             # Evaluation
#
#             labels = df_extracted_features["activity"]
#             sub_ids = df_extracted_features["subjectid"]
#             features = df_extracted_features.iloc[:, 2:17]
#
#             print(features.columns)
#
#             # Evaluation
#             iter_conf_mat = np.zeros([np.size(np.unique(labels)), np.size(np.unique(labels))], dtype=int)
#
#             for iter in range(1):
#                 # print(iter)
#
#                 sub_ids_list = sub_ids.unique()
#                 i = 0
#
#                 s_id_conf_mat = np.zeros([np.size(np.unique(labels)), np.size(np.unique(labels))], dtype=int)
#
#                 for s_id in sub_ids_list:
#                     pull_list = np.delete(sub_ids_list, i)
#                     X_train = features[sub_ids.isin(pull_list)]
#                     X_test = features[sub_ids.isin(
#                         [s_id])]  # use [] to make s_id list and use with .isin so it spits out dataframe
#                     y_train = labels[sub_ids.isin(pull_list)]
#                     y_test = labels[sub_ids.isin(
#                         [s_id])]  # use [] to make s_id list and use with .isin so it spits out dataframe
#                     print(f'iter: {iter}')
#                     print(f's_id: {s_id}')
#                     # model_1 = SVC(kernel='linear')
#                     model_2 = RandomForestClassifier(
#                         n_estimators=1000,
#                         min_samples_leaf=3,
#                         random_state=r_s,
#                         #    max_features=10,
#                         n_jobs=-1,
#                     )
#
#                     orig_model = model_2  # IF YOU USE THE SVM (model_1) , YOU NEED TO ADD A STANDARDIZ
#
#                     score, conf_mat, fit_model, y_pred, y_true, unused_var = validate(X_train, y_train, X_test,
#                                                                                       y_test, orig_model,
#                                                                                       random_state=r_s)
#
#                     s_id_conf_mat += conf_mat
#
#                 iter_conf_mat += s_id_conf_mat
#             # print("iter_conf_mat:")
#             # print(iter_conf_mat)
#
#             total_accuracy = iter_conf_mat.diagonal().sum() / iter_conf_mat.sum()
#             total_accuracy_c.append(total_accuracy)
#             print('total accuracy: ')
#             print(total_accuracy)
#
#             print(f"progress: {count_track_var} out of {final_count_track_var}")
#
#             with open("log.txt", "a") as text_file:
#                 text_file.write(f"activities: {three_act_selection}")
#                 text_file.write("\n")
#                 text_file.write(f"progress: {count_track_var} out of {final_count_track_var}")
#                 text_file.write("\n")
#
#             count_track_var = count_track_var + 1
#
# df_output_log = pd.DataFrame(
#     zip(nhoa_c, ghoa_c, ehoa_c, total_accuracy_c),
#     columns=['non_hand', 'general_hand', 'eating_hand',
#              'total_accuracy'])  # Two lines because of columns as rows problem when intialising df
#
# # df_output_log.to_excel(MAKETHISDEPEND ONINPUTVARS.xlsx")
#
# with open("log.txt", "a") as text_file:
#     text_file.write("finished")
#
# print("finished")
