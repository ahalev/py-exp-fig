import csv
import os
import sys


try:
    from matplotlib import pyplot as plt
except ImportError:
    plt = None


def track_savefig(fname, *args, show=False, tracker_file=None, **kwargs):
    if plt is None:
        raise ImportError("matplotlib must be installed to use 'savefig'")

    plt.savefig(fname, *args, **kwargs)
    track_save_to(fname, tracker_file)

    if show:
        plt.show()


def track_savetable(table, fname, print_out=False, tracker_file=None):
    with open(fname, 'w') as f:
        f.write(table)

    track_save_to(fname, tracker_file)

    if print_out:
        print(table)


def track_save_to(fname, tracker_file=None):
    save_script_result(sys.argv[0], fname, tracker_file)
    return fname


def save_script_result(script, fname, tracker_file=None):
    if tracker_file is None:
        tracker_file = os.path.join(os.getcwd(), 'figure_tracker.csv')

    write_header = not os.path.exists(tracker_file)

    with open(tracker_file, 'a') as csv_f:
        writer = csv.DictWriter(csv_f, ('script', 'figure'))

        if write_header:
            writer.writeheader()

        writer.writerow({'script': script, 'figure': fname})
