import glob
import numpy as np
import pandas as pd
from quantiser import quantiser
from scipy import signal
from sklearn.ensemble import RandomForestClassifier
from itertools import chain
from feature_extraction import extract_features
from evaluate_validate import validate
import random as rnd

# == Activities and their labels ==

# Non-hand-oriented activities:
nhoa_dict = {0: 'Walking', 1: 'Jogging', 2: 'Stairs', 3: 'Sitting', 4: 'Standing', 11: 'Kicking'}
nhoa_arr = np.array([0, 1, 2, 3, 4, 11])

# General hand-oriented activities:
ghoa_dict = {5: 'Typing', 6: 'Brushing Teeth', 12: 'Playing Catch', 13: 'Dribbling Ball', 14: 'Writing', 15: 'Clapping',
             16: 'Folding Clothes'}
ghoa_arr = np.array([5, 6, 12, 13, 14, 15, 16])

# Eating hand-oriented activities:
ehoa_dict = {7: 'Eating Soup', 8: 'Eating Chips', 9: 'Eating Pasta', 10: 'Drinking', 17: 'Eating Sandwich'}
ehoa_arr = np.array([7, 8, 9, 10, 17])

# == Variables used in simulation ==

r_s = 0
rnd.seed(r_s)
sim_t = 10.0
rate = 20
N = int(rate * sim_t)
t_plot = np.linspace(0, sim_t, N, endpoint=False)
f_sim = rate
f_prs = rate
sample_freq = f_sim / 2  # Is this enough here? This means no subsampling I think

n_subject_ids = 0
min_slices = 10

count_track_var = 1
final_count_track_var = len(nhoa_arr) * len(ghoa_arr) * len(ehoa_arr)
total_accuracy_list = []
validation_iter = 1

sensor_list = glob.glob('wisdm-dataset-modified/raw/watch/gyro' + '/*')


# == Analogue filters == #

def butter_highpass_filter(input, cutoff, fs, order):
    [b, a] = signal.butter(order, cutoff, fs=fs, btype='highpass', analog=False)
    y = signal.lfilter(b, a, input)
    return y


def butter_lowpass_filter(input, cutoff, fs, order):
    [b, a] = signal.butter(order, cutoff, fs=fs, btype='lowpass', analog=False)
    y = signal.lfilter(b, a, input)
    return y


def butter_bandpass_filter(input, cutoff, fs, order):
    [b, a] = signal.butter(order, cutoff, fs=fs, btype='bandpass', analog=False)
    y = signal.lfilter(b, a, input)
    return y


# The assignments of filter to axis depends on which sensor (accel or gyro) we are considering
def filter_assign(row):
    order = 6

    if row['axis'] == 'x':
        cutoff = sample_freq / 2
        x_filtered = butter_lowpass_filter(row['sensor_reading'], cutoff, f_sim, order)
        return x_filtered
    elif row['axis'] == 'y':
        cutoff = [sample_freq / 4, 3 * sample_freq / 4]
        y_filtered = butter_bandpass_filter(row['sensor_reading'], cutoff, f_sim, order)
        return y_filtered
    elif row['axis'] == 'z':
        cutoff = sample_freq / 2
        z_filtered = butter_lowpass_filter(row['sensor_reading'], cutoff, f_sim, order)
        return z_filtered


# == Functions ==
def load_prepare(raw_data, n_ids=0):
    # Load in sensor data
    big_data = []
    for entry in raw_data:
        input_data = pd.read_csv(entry, header=None, lineterminator=";", low_memory=False, parse_dates=True)
        big_data.append(input_data)

    # Clean up and reformat data
    big_data_column_names = ['subjectid', 'activity', 'timestamp', 'x', 'y', 'z']
    df_big_data = pd.concat(big_data)
    df_big_data.columns = big_data_column_names
    df_big_data.dropna(axis=0, how="any", inplace=True)
    df_big_data = df_big_data.replace('\n', '', regex=True)
    df_big_data = df_big_data.astype({"subjectid": str})

    # Relabel activities
    label_list = range(len(df_big_data['activity'].unique()))
    type_ids = dict(zip(df_big_data['activity'].unique(), label_list))  # Doesn't matter which?
    df_big_data = df_big_data.replace({"activity": type_ids})

    # Pull out subjects that don't contain all activities (is that even possible?)
    df_big_data_dropped_subject = []
    keep_list = []
    ind_subject_ids = np.unique(df_big_data["subjectid"])
    for i_si in ind_subject_ids:
        data_drop_subject = df_big_data[df_big_data["subjectid"] == i_si]
        if set(type_ids.values()).issubset(set(data_drop_subject['activity'])):
            keep_list.append(i_si)
            df_big_data_dropped_subject.append(data_drop_subject)

    # Pull out a random subsample of #n subjects for experiments. (If you need to reduce computation time for instance)
    if n_ids == 0:
        return df_big_data_dropped_subject, label_list
    else:
        select_subject_ids = rnd.sample(keep_list, n_ids)
        df_big_data_dropped_pulled_subject = []
        for pull_subject in df_big_data_dropped_subject:
            if pull_subject['subjectid'].unique() in select_subject_ids:
                df_big_data_dropped_pulled_subject.append(pull_subject)

        return df_big_data_dropped_pulled_subject, label_list


def three_activity_selection(nhoa_array, ghoa_array, ehoa_array):
    # Loop through activities
    three_activity_list = []
    for nh_a in nhoa_array:
        for gh_a in ghoa_array:
            for eh_a in ehoa_array:
                three_activity_list.append([nh_a, gh_a, eh_a])

    three_activity_array = np.array(three_activity_list)
    # Keep both array and list
    return three_activity_list, three_activity_array


def slice_and_drop(prepared_data, min_slices_per_activity):
    subjectid_list = []
    activity_list = []
    timestamp_list = []
    axis_list = []
    sensor_reading_list = []
    for df_by_subject in prepared_data:  # Split by subject to avoid cross subject cross-contamination
        for act_by_subject in act_label_list:
            df_by_subject_act = df_by_subject[df_by_subject["activity"] == act_by_subject]
            df_by_subject_act.set_index('timestamp', inplace=True)
            df_by_subject_act.sort_index()
            df_by_subject_act.index = pd.to_datetime(df_by_subject_act.index, unit='ns', errors='coerce')
            df_by_subject_act.dropna()
            df_by_subject_act_grouped = df_by_subject_act.groupby(pd.Grouper(freq='10s', origin='start'))

            # Remove any groups that weren't sampled properly i.e: N not equal to 200 (period*sample rate)
            # There are 3 subjects that don't make the cut which are filtered out here
            for group in df_by_subject_act_grouped:
                if len(group[1]) == N:
                    subjectid_list.append(3 * [group[1]['subjectid'][0]])
                    timestamp_list.append(3 * [group[1]['x'].index[0]])  # Extract only the time information
                    activity_list.append(3 * [group[1]['activity'][0]])
                    axis_list.append(['x', 'y', 'z'])
                    sensor_reading_list.append(
                        [np.array(group[1]['x'].reset_index(drop=True)), np.array(group[1]['y'].reset_index(drop=True)),
                         np.array(group[1]['z'].reset_index(drop=True))])

    subjectid_list = list(chain.from_iterable(subjectid_list))
    timestamp_list = list(chain.from_iterable(timestamp_list))
    activity_list = list(chain.from_iterable(activity_list))
    axis_list = list(chain.from_iterable(axis_list))
    sensor_reading_list = list(chain.from_iterable(sensor_reading_list))

    df_prepared_data = pd.DataFrame(
        {'subjectid': subjectid_list, 'timestamp': timestamp_list, 'activity': activity_list, 'axis': axis_list,
         'sensor_reading': sensor_reading_list})

    # Pull out subjects that don't contain a minimum amount of segments, defined by "min_slices_per_activity"
    drop_subject = []

    for subject_id in df_prepared_data['subjectid'].unique():
        activity_counts = df_prepared_data[df_prepared_data['subjectid'] == subject_id]['activity'].value_counts()
        if activity_counts.min() < min_slices_per_activity:
            drop_subject.append(subject_id)

    df_prepared_data.drop(df_prepared_data[df_prepared_data['subjectid'].isin(drop_subject)].index, inplace=True)

    return df_prepared_data


def quantise_assign(row):
    bit_depth = 12
    dec_points = 5
    quantised = quantiser(row['filtered'], bit_depth, axis=1, dec_points=dec_points)
    return quantised


# == Simulation ==

three_act_list, three_act_array = three_activity_selection(nhoa_arr, ghoa_arr, ehoa_arr)
loaded_prepared_data, act_label_list = load_prepare(sensor_list, n_subject_ids)
df_data = slice_and_drop(loaded_prepared_data, min_slices)
df_data['filtered'] = df_data.apply(lambda row: filter_assign(row), axis=1)
df_data['filtered_quantised'] = df_data.apply(lambda row: quantise_assign(row), axis=1)

extracted_features, feature_names = extract_features(np.stack(df_data['filtered_quantised']), shape=0,
                                                     axis=1)  # Convert pd.Series of arrays into single big np.array
df_data[feature_names] = extracted_features

three_axis_feature_list = []
three_axis_activity_list = []
three_axis_subject_list = []

for uniq_timestamp in df_data['timestamp'].unique():
    sub_sample = df_data[df_data['timestamp'] == uniq_timestamp]
    sub_sample_features = np.resize(np.array(sub_sample[feature_names]), (1, 15))
    three_axis_feature_list.append(sub_sample_features)
    three_axis_activity_list.append(sub_sample['activity'].unique()[0])
    three_axis_subject_list.append(sub_sample['subjectid'].unique()[0])

three_axis_feature_names = [letter + feature_name for letter in ['x_', 'y_', 'z_'] for feature_name in feature_names]
feature_dataset_columns = ['subjectid', 'activity'] + three_axis_feature_names
feature_dataset = np.squeeze(np.array(three_axis_feature_list))
df_feature_dataset = pd.DataFrame({'subjectid': three_axis_subject_list, 'activity': three_axis_activity_list})
df_feature_dataset[three_axis_feature_names] = feature_dataset

for three_act_group in three_act_list:

    df_three_act_dataset = df_feature_dataset[df_feature_dataset['activity'].isin(three_act_group)]
    labels = df_three_act_dataset["activity"]
    sub_ids = df_three_act_dataset["subjectid"]
    features = df_three_act_dataset[three_axis_feature_names]
    sub_ids_list = sub_ids.unique()

    final_conf_mat = np.zeros([np.size(np.unique(labels)), np.size(np.unique(labels))], dtype=int)

    for iteration in range(validation_iter):
        pull_index = 0
        iter_conf_mat = np.zeros([np.size(np.unique(labels)), np.size(np.unique(labels))], dtype=int)

        for s_id in sub_ids_list:
            pull_list = np.delete(sub_ids_list, pull_index)
            X_train = features[sub_ids.isin(pull_list)]
            X_test = features[
                sub_ids.isin([s_id])]  # Use [] to make s_id list and use with .isin so it outputs dataframe
            y_train = labels[sub_ids.isin(pull_list)]
            y_test = labels[
                sub_ids.isin([s_id])]  # Use [] to make s_id list and use with .isin so it outputs dataframe
            print(f'iter: {iteration}')
            print(f's_id: {s_id}')
            print(f"pull_list: {pull_list}")
            model = RandomForestClassifier(
                n_estimators=1000,
                min_samples_leaf=3,
                random_state=r_s,
                n_jobs=-1,
            )

            score, conf_mat, fit_model, y_pred, y_true, unused_var = validate(X_train, y_train, X_test,
                                                                              y_test, model,
                                                                              random_state=r_s)
            iter_conf_mat += conf_mat
            pull_index = pull_index + 1
        final_conf_mat += iter_conf_mat

    total_accuracy = iter_conf_mat.diagonal().sum() / iter_conf_mat.sum()
    total_accuracy_list.append(total_accuracy)
    print('total accuracy: ')
    print(total_accuracy)

    print(f"progress: {count_track_var} out of {final_count_track_var}")

    with open("log.txt", "a") as text_file:
        text_file.write(f"activities: {three_act_group}")
        text_file.write("\n")
        text_file.write(f"progress: {count_track_var} out of {final_count_track_var}")
        text_file.write("\n")

    count_track_var = count_track_var + 1

df_output_log = pd.DataFrame(
    zip(three_act_array[:, 0], three_act_array[:, 1], three_act_array[:, 2], total_accuracy_list),
    columns=['non_hand', 'general_hand', 'eating_hand',
             'total_accuracy'])

df_output_log.to_excel('output_log.xlsx')

with open("log.txt", "a") as text_file:
    text_file.write("finished")

print("finished")
