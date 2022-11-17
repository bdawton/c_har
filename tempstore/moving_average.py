import numpy as np
from scipy.ndimage.filters import uniform_filter1d

def moving_average(input_arr, window_size):


    averaged_signal = uniform_filter1d(input_arr, size=window_size)

    return averaged_signal

#Billy this is very simple for now, but I will add functionality such as array type check later etc. It also help me remeber the fucntion name lol