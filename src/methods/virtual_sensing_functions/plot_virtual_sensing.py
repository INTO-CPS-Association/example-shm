import matplotlib.pyplot as plt
import numpy as np

def plot_virtual_sensing(plot: list[bool], disp: np.ndarray, acc_filtered: np.ndarray, data: np.ndarray) -> None: 
    """
    Plot vitrual sensing results
    Args:
        plot (list[bool]): List of bools to determine what to plot
        disp (np.ndarray):
        acc_filtered (np.ndarray):
        data (np.ndarray):
    Returns:
        None
    Plots:

    """
    DOF = [0, 5, 8, 11, 14, 17]
    if plot[0] == 1:
        plt.figure()
        for ii in DOF:
            plt.plot(acc_filtered[ii,:])
    
    if plot[1] == 1:
        plt.figure()
        for ii in range(data.shape[0]):
            plt.plot(data[ii,:])

    if plot[2] == 1:
        a_data = np.load("record/simulate_beam/beam_simulation_acc.npy")
        plt.figure()
        for ii in range(a_data.shape[0]):
            plt.plot(a_data[ii,:])

    if plot[3] == 1:
        plt.figure()
        for ii in DOF:
            plt.plot(disp[ii,:])
    
    if plot[4] == 1:
        d_data = np.load("record/simulate_beam/beam_simulation_u.npy")
        plt.figure()
        for ii in DOF:
            plt.plot(d_data[ii,:])
    
    plt.show()