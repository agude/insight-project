from scipy import optimize
import numpy as np

def best_position(tag_kde, all_kde, coords):
    X, Y = zip(*coords)
    x_max = max(X)
    x_min = min(X)
    y_max = max(Y)
    y_min = min(Y)

    # Start in the center of the map
    start_x = x_min + (x_max-x_min)/2.
    start_y = y_min + (y_max-y_min)/2.

    # Define the function to minimize, the - is to find the maximum
    def fn(pos, tag_kde=tag_kde, all_kde=all_kde):
        result = -tag_kde(pos) / all_kde(pos)
        return result

    #print "Start:", (start_x, start_y)
    peak_fit = optimize.basinhopping(
        fn,
        (start_x, start_y),
        stepsize = 0.15,
        )

    peak_lon = peak_fit['x'][0]
    peak_lat = peak_fit['x'][1]

    return peak_lon, peak_lat, start_x, start_y
