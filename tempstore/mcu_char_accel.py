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
import modified_emlearn
from sklearn.metrics import classification_report

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

#nhoa_arr = np.array([0, 1, 2, 3, 4, 11])
nhoa_arr = np.array([3])


# General hand-oriented activities:
# {dribbling, playing catch, typing, writing, clapping, brushing teeth, folding clothes}

#ghoa_arr = np.array([13, 12, 5, 14, 15, 6, 16])
ghoa_arr = np.array([6])


# Eating hand-oriented activities:
# {eating pasta, eating soup, eating sandwich, eating chips, drinking}

#ehoa_arr = np.array([9, 7, 17, 8, 10])
ehoa_arr = np.array([10])


count_track_var = 1
final_count_track_var = len(nhoa_arr) * len(ghoa_arr) * len(
    ehoa_arr)

line_track_var = 0

total_accuracy_c = []

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

            for df_by_subject in watch_accel_drop_subject:
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
            sliced_watch_accel_drop_subject = []
            s_k_list = []


            for s_item in sliced_act_subject_list:
                if len(s_item[0]) >= 10:  # Let's just say minimum length 10
                    # print('keep')
                    s_k = (s_item[0][0]['subjectid'].unique()[0], 'keep')
                    s_k_list.append(s_k)
                    sliced_watch_accel_drop_subject.append(s_item)

            lf_prs_params = {'p_1': 0.85, 'd_1': 0, 'k_1': 0, 'p_2': 666, 'd_2': 666, 'k_2': 666, 'seq_num': 1}
            mf_prs_params = {'p_1': 0.9, 'd_1': 0, 'k_1': 0, 'p_2': 0.9, 'd_2': 0, 'k_2': 1, 'seq_num': 2}
            hf_prs_params = {'p_1': 0.1, 'd_1': 0, 'k_1': 1, 'p_2': 666, 'd_2': 666, 'k_2': 666, 'seq_num': 1}
            bb_prs_params = {'p_1': 0.5, 'd_1': 0, 'k_1': 0, 'p_2': 666, 'd_2': 666, 'k_2': 666, 'seq_num': 1}

            #BILLY CHANGE THESE ACCORDING TO RESULTS

            #XAXIS This example is LPF and only uses ONE sequence, be careful with number of sequences
            sequence_root_1 = PRS.prs(lf_prs_params['p_1'], lf_prs_params['d_1'], lf_prs_params['k_1'], t, f_prs, 0)
            sequence_1 = np.tile(sequence_root_1, int(f_sim / f_prs))
            sequence_root_2 = PRS.prs(lf_prs_params['p_2'], lf_prs_params['d_2'], lf_prs_params['k_2'], t, f_prs, 0)
            sequence_2 = np.tile(sequence_root_2, int(f_sim / f_prs))
            seq_num = lf_prs_params['seq_num']
            if seq_num == 1:
                x_sequence = sequence_1 # <---- HERE IS WHERE I SET X,Y,Z AXIS
            elif seq_num == 2:
                x_sequence = sequence_1 * sequence_2 # <---- OR HERE IF MF_PRS

            #YAXIS This example is LPF and only uses ONE sequence, be careful with number of sequences
            sequence_root_1 = PRS.prs(lf_prs_params['p_1'], lf_prs_params['d_1'], lf_prs_params['k_1'], t, f_prs, 0)
            sequence_1 = np.tile(sequence_root_1, int(f_sim / f_prs))
            sequence_root_2 = PRS.prs(lf_prs_params['p_2'], lf_prs_params['d_2'], lf_prs_params['k_2'], t, f_prs, 0)
            sequence_2 = np.tile(sequence_root_2, int(f_sim / f_prs))
            seq_num = lf_prs_params['seq_num']
            if seq_num == 1:
                y_sequence = sequence_1  # <---- HERE IS WHERE I SET X,Y,Z AXIS
            elif seq_num == 2:
                y_sequence = sequence_1 * sequence_2  # <---- OR HERE IF MF_PRS

            #ZAXIS This example is LPF and only uses ONE sequence, be careful with number of sequences
            sequence_root_1 = PRS.prs(lf_prs_params['p_1'], lf_prs_params['d_1'], lf_prs_params['k_1'], t, f_prs, 0)
            sequence_1 = np.tile(sequence_root_1, int(f_sim / f_prs))
            sequence_root_2 = PRS.prs(lf_prs_params['p_2'], lf_prs_params['d_2'], lf_prs_params['k_2'], t, f_prs, 0)
            sequence_2 = np.tile(sequence_root_2, int(f_sim / f_prs))
            seq_num = lf_prs_params['seq_num']
            if seq_num == 1:
                z_sequence = sequence_1  # <---- HERE IS WHERE I SET X,Y,Z AXIS
            elif seq_num == 2:
                z_sequence = sequence_1 * sequence_2  # <---- OR HERE IF MF_PRS

            c_measure_list_x = []
            c_measure_list_y = []
            c_measure_list_z = []
            features_segment_list = []
            for sliced_subject in sliced_watch_accel_drop_subject:
                for sliced_activity in sliced_subject:
                    for sliced_segment in sliced_activity:
                        sliced_segment['x_PRS'] = x_sequence
                        sliced_segment['y_PRS'] = y_sequence
                        sliced_segment['z_PRS'] = z_sequence
                        sliced_segment['x_spread'] = sliced_segment['x'] * sliced_segment['x_PRS']
                        sliced_segment['y_spread'] = sliced_segment['y'] * sliced_segment['y_PRS']
                        sliced_segment['z_spread'] = sliced_segment['z'] * sliced_segment['z_PRS']

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

                        features_raw, feature_names_raw = extract_features(cs_sliced_segment[quant_sampled_columns])
                        features_resized = np.resize(features_raw, (1, 15))
                        sub_act_features = np.concatenate((np.array(
                            [cs_sliced_segment['subjectid'].iloc[0], cs_sliced_segment['activity'].iloc[0]]),
                                                           features_resized), axis=None)
                        feature_names = [letter + feature_name for letter in ['x_', 'y_', 'z_']
                                         for feature_name in feature_names_raw]
                        feature_columns = ['subjectid', 'activity'] + feature_names
                        features_segment = pd.DataFrame(columns=feature_columns)
                        features_segment.loc[0] = sub_act_features  # No idea why loc works here and iloc doesn't
                        features_segment_list.append(features_segment)
                        c_measure_list_x.append(cs_sliced_segment['x_q_sampled'].values) #save as an array, because 50 or 200 (depending on operating mode) of these correspond to one line of features
                        c_measure_list_y.append(cs_sliced_segment['y_q_sampled'].values) #save as an array, because 50 or 200 (depending on operating mode) of these correspond to one line of features
                        c_measure_list_z.append(cs_sliced_segment['z_q_sampled'].values) #save as an array, because 50 or 200 (depending on operating mode) of these correspond to one line of features

            df_extracted_features = pd.concat(features_segment_list)
            subs_for_df = np.array(df_extracted_features['subjectid'].reset_index(drop = True))
            df_c_measure_x = pd.DataFrame(zip(subs_for_df, c_measure_list_x), columns = ['subject', 'measurements'])
            df_c_measure_x.reset_index(drop = True)
            df_c_measure_y = pd.DataFrame(zip(subs_for_df, c_measure_list_y), columns = ['subject', 'measurements'])
            df_c_measure_y.reset_index(drop = True)
            df_c_measure_z = pd.DataFrame(zip(subs_for_df, c_measure_list_z), columns = ['subject', 'measurements'])
            df_c_measure_z.reset_index(drop = True)
            df_c_measure = pd.DataFrame(zip(df_c_measure_x['subject'],df_c_measure_x['measurements'],df_c_measure_y['measurements'],df_c_measure_z['measurements']), columns = ['subject', 'cm_x', 'cm_y', 'cm_z'])

            labels = df_extracted_features["activity"]
            sub_ids = df_extracted_features["subjectid"]
            features = df_extracted_features.iloc[:, 2:17]

            #This is not a hack, this is actually probably the raeal way to do it and should be changed in other code
            labels_hack = labels.reset_index(drop = True)
            sub_ids_hack = sub_ids.reset_index(drop = True)
            features_hack = features.reset_index(drop = True)

            print(features.columns)

            # Evaluation

            # print(iter)
            mcu_sub_num = 14
            sub_ids_list_full = sub_ids.unique()
            sub_ids_list = np.array(rnd.sample(list(sub_ids_list_full), mcu_sub_num))

            i = 0

            s_id_conf_mat = np.zeros([np.size(np.unique(labels)), np.size(np.unique(labels))], dtype=int)

            y_true_list = []  # The resampled test data used in "evaluate" function
            y_pred_list = []  # The outputted predictions are already "resampled" as they are obtained from resampled test data

            for s_id in sub_ids_list:
                pull_list = np.delete(sub_ids_list, i)
                X_train = features_hack[sub_ids_hack.isin(pull_list)]
                X_test = features_hack[sub_ids_hack.isin(
                    [s_id])]  # use [] to make s_id list and use with .isin so it spits out dataframe
                y_train = labels_hack[sub_ids_hack.isin(pull_list)]
                y_test = labels_hack[sub_ids_hack.isin(
                    [s_id])]  # use [] to make s_id list and use with .isin so it spits out dataframe
                c_mea_test = df_c_measure[sub_ids_hack.isin([s_id])]  #We need for test data, all axes
                print('lol')
                # BILLY FROM HERE. YOU NEED TO FIGURE OUT HOW TO DRAW THE ARRAYS STORED IN C-MEASURES ACCORDING TO THE SUBJECT TO MATCH TEST DATA
                print(f's_id: {s_id}')

                orig_model = RandomForestClassifier(
                    n_estimators=100,
                    # Small amount of trees to fit ported model on MCU. Can be changed depending on MCU memory
                    min_samples_leaf=3,
                    random_state=r_s,
                    n_jobs=-1,  # -1 means multithreading
                )

                score, conf_mat, fit_model, y_pred, y_true, c_mea_resamp = validate(X_train, y_train, X_test, y_test,
                                                                                    orig_model,
                                                                                    c_mea_test, random_state=r_s)

                y_true_list.append(y_true)
                y_pred_list.append(y_pred)

                """# Export for MCU"""

                #Rename labels to match classifier understanding eg: a,b,c becomes 0,1,2
                class_count = 0
                y_export = pd.Series(np.zeros(len(y_true)))
                for c_class in fit_model.classes_:
                    y_export[y_true == c_class] = class_count
                    class_count = class_count + 1

                # Export resampled labels and corresponding compressive measurements to text file
                np.savetxt('lab_' + str(s_id) + '.txt', np.array(y_export, dtype=int), delimiter=",",
                           fmt='%i')  # Save labels to text file
                np.savetxt('x_c_mea_' + str(s_id) + '.txt', np.stack(c_mea_resamp['cm_x'].values), delimiter=",",
                           fmt='%f')  # Save compressive measurements to text file
                np.savetxt('y_c_mea_' + str(s_id) + '.txt', np.stack(c_mea_resamp['cm_y'].values), delimiter=",",
                           fmt='%f')  # Save compressive measurements to text file
                np.savetxt('z_c_mea_' + str(s_id) + '.txt', np.stack(c_mea_resamp['cm_z'].values), delimiter=",",
                           fmt='%f')  # Save compressive measurements to text file

                # Port classifier to C and export as .h file
                rf_c_code = modified_emlearn.convert(fit_model, method='inline')
                rf_c_code.save(file='classifier_to_test_' + str(s_id) + '.h')

                s_id_conf_mat += conf_mat


            # print("s_id_conf_mat:")
            # print(s_id_conf_mat)

            total_accuracy = s_id_conf_mat.diagonal().sum() / s_id_conf_mat.sum()
            total_accuracy_c.append(total_accuracy)
            print('total accuracy: ')
            print(total_accuracy)

            print(f"progress: {count_track_var} out of {final_count_track_var}")

            with open("log.txt", "a") as text_file:
                text_file.write(f"activities: {three_act_selection}")
                text_file.write("\n")
                text_file.write(f"progress: {count_track_var} out of {final_count_track_var}")
                text_file.write("\n")

            count_track_var = count_track_var + 1


df_output_log = pd.DataFrame(
    zip(nhoa_c, ghoa_c, ehoa_c, total_accuracy_c),
    columns=['non_hand', 'general_hand', 'eating_hand', 'total_accuracy'])  # Two lines because of columns as rows problem when intialising df

df_output_log.to_excel("accel_final_approach_3class_all.xlsx")


""""# Set plotting parameters for use in Latex publication """

plt.rcParams['font.family'] = 'Times'
plt.rcParams['font.size'] = 22
plt.rcParams['ps.useafm'] = True
plt.rcParams['pdf.use14corefonts'] = True
plt.rcParams['text.usetex'] = True

""""# Plot confusion matrix """

s_id_conf_mat_labels = np.array(fit_model.classes_)
fig = plt.figure(figsize=(8, 5))
sns_plot = sns.heatmap(
    s_id_conf_mat / np.tile(s_id_conf_mat.sum(axis=1), [s_id_conf_mat.shape[0], 1]).T * 1e2,
    cmap="Blues",
    annot=True,
    fmt='.2f',
    cbar=False,
    xticklabels=s_id_conf_mat_labels,
    yticklabels=s_id_conf_mat_labels

)
plt.show()
plt.xlabel('Estimated Type'),
plt.ylabel('Actual Type'),

"""# Output metrics"""

metrics = classification_report(np.concatenate(y_true_list), np.concatenate(y_pred_list), digits=3)
print(metrics)


with open("log.txt", "a") as text_file:
    text_file.write("finished")

print("finished")





