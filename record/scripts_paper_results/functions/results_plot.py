import pickle
import numpy as np
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = 'Times New Roman'
from matplotlib.ticker import FormatStrFormatter
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from functions.mode_tracking import track_for_plotting





def cantilever_beam_plots(path="data",all_at_once=False):
    # # # # -----------------------------------------------------------------------------
    # # # Modal parameters plotting
    # # Load the pickle file
    with open(path+"/tracked_modaldatadata.pkl", "rb") as f:
        tracked_modaldatadata = pickle.load(f)

    with open(path+"/cluster_dict_ini.pkl", "rb") as f:
        cluster_dict_ini = pickle.load(f)

    # with open(path+"/tracked_modes.pkl", "rb") as f:
    #     tracked_clusters = pickle.load(f)
    # tracked_modaldatadata = track_for_plotting(tracked_clusters)

    # Extract data for plotting
    freqs = []
    freq_err_lower = []
    freq_err_upper = []

    damps = []
    damp_err_lower = []
    damp_err_upper = []

    # 4 or 27 or 79
    for mode in ['1', '2', '3']:
        # Extract data for plotting
        freqs = []
        freq_err_lower = []
        freq_err_upper = []

        damps = []
        damp_err_lower = []
        damp_err_upper = []


        instances = []

        #Add initial update eigenfrequencies
        instances.append(1)
        cluster = cluster_dict_ini[int(mode)-1]
        freqs.append(cluster['median_f'])
        freq_err_lower.append(np.min(cluster['median_f'] - cluster['ci_f']))
        freq_err_upper.append(np.max(cluster['median_f'] + cluster['ci_f']))

        damps.append(np.median(cluster['d']))
        damp_err_lower.append(np.min(np.median(cluster['d']) - cluster['ci_d'])/1000)
        damp_err_upper.append(np.max(np.median(cluster['d']) + cluster['ci_d'])/1000)
        
        for ii, _ in enumerate(tracked_modaldatadata):  # 1 to 92

            if mode in tracked_modaldatadata[ii]: #ii in tracked_modaldatadata and
                data = tracked_modaldatadata[ii][mode]

                
                instances.append(ii+1)
                freqs.append(data['freq'])
                freq_err_lower.append(np.min(data['freq'] - data['ci_f']))
                freq_err_upper.append(np.max(data['freq'] + data['ci_f']))

                damps.append(data['damping'])
                damp_err_lower.append(np.min(data['damping'] - data['ci_d']/1000))
                damp_err_upper.append(np.max(data['damping'] + data['ci_d']/1000))
                               
        instances = np.array(instances)
        freqs = np.array(freqs)
        damps = np.array(damps)
        freq_err_lower = np.array(freq_err_lower)
        freq_err_upper = np.array(freq_err_upper)
        damp_err_lower = np.array(damp_err_lower)
        damp_err_upper = np.array(damp_err_upper)

        # Ensure all error bars are non-negative
        freq_err_lower = np.maximum(0,freq_err_lower)
        freq_err_upper = np.maximum(0, freq_err_upper)
        damp_err_lower = np.maximum(0,damp_err_lower)
        damp_err_upper = np.maximum(0, damp_err_upper)

        # # Plotting
        fig, ax1 = plt.subplots(figsize=(8, 5))
        # Plot frequency line
        ax1.plot(instances, freqs, 'o-', color='tab:blue', label='Frequency (Hz)')
        # Plot shaded region for frequency uncertainty
        ax1.fill_between(
            instances,
            freq_err_lower,
            freq_err_upper,
            color='tab:blue',
            alpha=0.2,
            label='Freq. Uncertainty'
        )

        ax1.set_xlabel('Experiment index', fontsize=20)
        ax1.set_ylabel('Frequency [Hz]', fontsize=20, color='tab:blue')
        ax1.tick_params(axis='y', labelsize=17, labelcolor='tab:blue')
        ax1.tick_params(axis='x', labelsize=17, labelcolor='black')
        ax1.grid(which='major', color='gray', linestyle='-', linewidth=0.5)
        ax1.grid(which='minor', color='lightgray', linestyle='--', linewidth=0.3)
        ax1.set_xticks(np.array([0,10,20,30,40,50,60,70,80,90]))

        # Right y-axis for damping
        ax2 = ax1.twinx()
        ax2.plot(instances, damps, 's--', color='tab:red', label='Damping')
        ax2.fill_between(
            instances,
            damp_err_lower,
            damp_err_upper,
            color='tab:red',
            alpha=0.2,
            label='Damping Uncertainty'
        )
        ax2.set_ylabel('Damping ratio', fontsize=20, color='tab:red')
        ax2.tick_params(axis='y', labelsize=17, labelcolor='tab:red')
        # plt.title("First mode: Frequency and Damping with Uncertainty (Shaded)")
        fig.tight_layout()
        if mode == '1': 
            ax1.set_ylim(2, 5)      # Y-limit for left y-axis
        elif mode == '2':
            ax1.set_ylim(15, 35)      # Y-limit for left y-axis
        else:
            ax1.set_ylim(60, 95)      # Y-limit for left y-axis
        ax2.set_ylim(0, 0.045)     # Y-limit for right y-axis (assuming ax2 = ax1.twinx())
        xlim_2 = 90
        ax1.set_xlim(1, xlim_2)     # X-limits apply to both axes (shared x-axis)
        # Format y-axis labels to show 0 instead of 0.000
        ax2.yaxis.set_major_formatter(FormatStrFormatter('%.3f'))
        ax2.set_yticks(np.linspace(ax2.get_yticks()[0], ax2.get_yticks()[-1], len(ax1.get_yticks())))
        ax2.set_yticklabels([f"{float(tick):.3f}" if float(tick) != 0 else "0" for tick in ax2.get_yticks()])

        # Add major and minor grid lines
        ax2.grid(which='major', color='gray', linestyle='-', linewidth=0.5)
        ax2.grid(which='minor', color='lightgray', linestyle='--', linewidth=0.3)
        plt.tight_layout()
        plt.show(block=not all_at_once)


    # #-----------------------------------------------------------------------------
    # Parameter estimation plotting
    k_stiffness = []
    tipMass = []
    instances = []
    with open(path+"/tracked_updatedParams.pkl", "rb") as f:
        tracked_updatedParams = pickle.load(f)

    for ii in range(89):  # 1 to 92
        if ii == 29:
            continue
        else:
            # if ii in tracked_updatedParams:
            data = tracked_updatedParams[ii]
            instances.append(ii+2)
            k_val = data[0]
            # if ii == 76:
            #     k_stiffness.append(10)
            k_stiffness.append(k_val)
            #k_stiffness.append(10 if k_val > 25 or k_val < 5 else k_val)        
            tipMass.append(data[1]*1000)
        
    print("MAX and MIN of k_rot",max(k_stiffness),min(k_stiffness))
    print("MAX and MIN and mean of mass (0g)",max(tipMass[:28]),min(tipMass[:28]),np.mean(tipMass[:28]))
    print("MAX and MIN and mean of mass (10g)",max(tipMass[29:61]),min(tipMass[29:61]),np.mean(tipMass[29:61]))
    print("MAX and MIN and mean of mass (20g)",max(tipMass[62:]),min(tipMass[62:]),np.mean(tipMass[62:]))
    # # Set Computer Modern (LaTeX font) and mathtext rendering
    # rcParams.update({
    #     "font.family": "serif",
    #     "font.serif": ["Computer Modern"],
    #     "mathtext.fontset": "cm",  # Use Computer Modern math font
    #     "mathtext.rm": "serif",
    # })
    # Use STIX font (LaTeX-like) with MathText
    plt.rcParams.update({
        "font.family": "STIXGeneral",
        "mathtext.fontset": "stix",
    })    

    fig, ax1 = plt.subplots(figsize=(8, 5))
    # Plot frequency line
    ax1.plot(instances, k_stiffness, 'o-', color='tab:blue', label=r'$k_{\mathrm{rot}}$ [Nm/rad]')
    ax1.plot(instances, tipMass, '*--', color='tab:red', label=r'$m_{\mathrm{p}}$ [g]')
    ax1.set_xlabel('Experiment index', fontsize=20)
    ax1.set_ylabel('Parameters', fontsize=20)
    ax1.grid(which='major', color='gray', linestyle='-', linewidth=0.5)
    ax1.grid(which='minor', color='lightgray', linestyle='--', linewidth=0.3)
    ax1.tick_params(axis='both', labelsize=17, labelcolor='black')
    ax1.legend(fontsize=20, loc='upper left')
    fig.tight_layout()
    ax1.set_ylim(-0.5, 20)      # Y-limit for left y-axis
    xlim_2 = 90
    ax1.set_xlim(1, xlim_2)     # X-limits apply to both axes (shared x-axis)
    plt.tight_layout()
    plt.show(block=not all_at_once)
    # -----------------------------------------------------------------------------
    # # # # # Updated modal parameters plotting
    

    mode1 = []
    mode2 = []
    mode3 = []
    instances = []

    with open(path+"/tracked_updatedFreq.pkl", "rb") as f:
        tracked_updatedFreq = pickle.load(f)

    for ii in range(89):
        if ii == 29:
            continue
        else:
            data = tracked_updatedFreq[ii]
            instances.append(ii+2)
            mode1.append(data[0])
            mode2.append(data[1])
            mode3.append(data[2])
            
    # Main plot
    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax1.plot(instances, mode1, 'o-', color='tab:blue', label='Eigenfrequency 1')
    ax1.plot(instances, mode2, '*--', color='tab:red', label='Eigenfrequency 2')
    ax1.plot(instances, mode3, '^--', color='tab:orange', label='Eigenfrequency 3')

    ax1.set_xlabel('Experiment index', fontsize=20)
    ax1.set_ylabel('Frequency [Hz]', fontsize=20)
    ax1.grid(which='major', color='gray', linestyle='-', linewidth=0.5)
    ax1.grid(which='minor', color='lightgray', linestyle='--', linewidth=0.3)
    ax1.tick_params(axis='both', labelsize=17, labelcolor='black')
    ax1.legend(fontsize=13.8, loc='upper right', ncol=3)
    ax1.set_ylim(0, 100)
    ax1.set_xlim(1, xlim_2)     # X-limits apply to both axes (shared x-axis)
    fig.tight_layout()

    # Create inset axes
    axins = inset_axes(ax1, width="88%", height="30%", loc='center right')  # inside upper right
    axins.plot(instances, mode1, 'o-', color='tab:blue')
    xlim_2 = len(tracked_updatedFreq)
    axins.set_xlim(0, xlim_2)      # Adjust zoom range for x
    axins.set_ylim(2.5, 4.5)      # Adjust zoom range for y
    # Set inset ticks based on the same logic as main axis
    axins.set_xticks(np.arange(0, xlim_2, 10))   # Tick every 5 units
    axins.set_yticks(np.arange(2.5, 4.501, 1))   # Tick every 1 unit
    axins.grid(which='major', color='gray', linestyle='-', linewidth=0.5)
    axins.grid(which='minor', color='lightgray', linestyle='--', linewidth=0.3)
    # Format tick labels to match main plot
    axins.tick_params(labelsize=13, colors='black')

    # Optional: indicate inset region on main plot
    # ax1.indicate_inset_zoom(axins, edgecolor="black")
    # axins.set_title("Zoom on Mode 1", fontsize=10)

    # Optional: draw a rectangle on the main plot showing zoom region
    # ax1.indicate_inset_zoom(axins, edgecolor="black")

    plt.show(block=not all_at_once)



    # -----------------------------------------------------------------------------
    # # # # Modal expansion validation
    with open(path+"/modal_expansion_data.pkl", "rb") as f:
        modal_expansion_data = pickle.load(f)

    expansion = modal_expansion_data[0]
    y_expanded = expansion['y_expanded']
    data_compare = expansion['data_compare']

    t = np.linspace(0, y_expanded.shape[0] / 256, y_expanded.shape[0])   # time in seconds of data

    #fig, ax1 = plt.subplots(figsize=(8, 6))
    fig1, ax1 = plt.subplots(figsize=(8, 5))

    # ax1.plot(t, data_compare[1:],'--r', t, y_expanded[3,:], 'k')
    ax1.plot(t, data_compare, linestyle='--', color='tab:red',zorder=3)
    ax1.plot(t, y_expanded, color='tab:blue',zorder=0)
    # ax1.set_ylabel(r'$\ddot{y}(t)$ [g]', fontsize=20)
    # ax1.set_xlabel(r'$t$ [sec]', fontsize=20)
    ax1.set_ylabel(r'Acceleration [m/s$^2$]', fontsize=20)
    ax1.set_xlabel('Time [s]', fontsize=20)
    ax1.legend(['Measured', 'Modal expanded'], fontsize=18, loc='upper right')
    ax1.grid(which='major', color='gray', linestyle='-', linewidth=0.5)
    ax1.grid(which='minor', color='lightgray', linestyle='--', linewidth=0.3)
    ax1.set_xticks(np.arange(0, 120.01, 10))   # Tick every 5 units
    ax1.tick_params(axis='both', labelsize=17, labelcolor='black')
    ax1.set_ylim(-1.25, 1.25)
    ax1.set_xlim(0, 120)

    # Create inset axes
    # axins = inset_axes(ax1, width="40%", height="45%", bbox_to_anchor=(0, 0, 1, 1))
    axins = ax1.inset_axes([0.35,0.1,0.6,0.45])  # inside upper rights
    axins.plot(t, data_compare, linestyle='--', color='tab:red',zorder=3,linewidth=2)
    axins.plot(t, y_expanded, color='tab:blue',zorder=0,linewidth=2)
    axins.set_xlim(15, 16)      # Adjust zoom range for x
    axins.set_ylim(-0.5, 0.51)      # Adjust zoom range for y
    # Set inset ticks based on the same logic as main axis
    axins.set_xticks(np.arange(15, 16.01, 0.2))   # Tick every 5 units
    axins.set_yticks(np.arange(-0.5, 0.51, 0.25))   # Tick every 3 unit
    axins.grid(which='major', color='gray', linestyle='-', linewidth=0.5)
    axins.grid(which='minor', color='lightgray', linestyle='--', linewidth=0.3)
    # Format tick labels to match main plot
    axins.tick_params(labelsize=15, colors='black')

    fig1.tight_layout()
    plt.show(block=not all_at_once)


    # -----------------------------------------------------------------------------
    # # # # # Stress
    data = np.load(path+'/stress_estimation.npy')
    batch = data[0,:]

    t = np.linspace(0, batch.shape[0] / 256, batch.shape[0])   # time in seconds of data

    #fig1, ax1 = plt.subplots(figsize=(8, 6))
    fig1, ax1 = plt.subplots(figsize=(8, 3))
    ax1.plot(t,batch, color='tab:blue')
    ax1.set_ylabel('Stress [MPa]', fontsize=20)
    ax1.set_xlabel('Time [s]', fontsize=20)
    # Grid and ticks
    ax1.grid(which='major', color='gray', linestyle='-', linewidth=0.5)
    ax1.grid(which='minor', color='lightgray', linestyle='--', linewidth=0.3)
    ax1.tick_params(axis='both', labelsize=17, labelcolor='black')
    # Axis limits
    ax1.set_ylim(-20, 20)
    ax1.set_yticks(np.arange(-20, 20.1, 10))
    ax1.set_xlim(0, 120)
    # # Add legend
    # ax1.legend(fontsize=14, loc='upper left')
    fig1.tight_layout()
    plt.show(block=not all_at_once)


    # # -----------------------------------------------------------------------------
    with open(path+"/initial_model_update_comparisson.pkl", "rb") as f:
        initial_model_update_results = pickle.load(f)

    freq_error_before,freq_error_after,MAC_1,MAC_2 = initial_model_update_results
    # Bar plot for frequency error comparison
    fig, ax1 = plt.subplots(figsize=(8, 4.4), tight_layout=True)
    bar_width = 0.30
    index = np.arange(freq_error_before.shape[0])

    # Bars
    ax1.bar(index, freq_error_before, bar_width, label='Before update', color='tab:red')
    ax1.bar(index + bar_width, freq_error_after, bar_width, label='After update', color='tab:blue')

    # Axes settings
    ax1.tick_params(axis='both', labelsize=17, labelcolor='black')
    ax1.set_ylabel('Eigenfrequency discrepancy [%]', fontsize=20)
    ax1.set_xticks(index + bar_width / 2)
    ax1.set_xticklabels([f'Eigenmode {i+1}' for i in index], fontsize=20)
    ax1.set_ylim(0, 25)

    # Grids
    ax1.grid(which='major', linestyle='-', linewidth=0.75, color='gray', alpha=0.5)
    ax1.minorticks_on()
    ax1.grid(which='minor', linestyle=':', linewidth=0.5, color='gray', alpha=0.3)

    # Legend
    ax1.legend(fontsize=20, loc='upper right', ncol=2)

    # Layout
    fig1.tight_layout()
    plt.show(block=not all_at_once)

    # Bar plot for MAC comparison
    fig, ax2 = plt.subplots(figsize=(8, 4.4), tight_layout=True)

    ax2.bar(index, MAC_1, bar_width, label='Before update', color='tab:red')
    ax2.bar(index + bar_width, MAC_2, bar_width, label='After update', color='tab:blue')
    ax2.tick_params(axis='both', labelsize=17, labelcolor='black')
    # ax2.set_xlabel('Mode', fontsize=20)
    ax2.set_ylabel('MAC', fontsize=20)
    # ax2.set_title('MAC Values Comparison')
    ax2.set_xticks(index + bar_width / 2)
    ax2.set_xticklabels([f'Eigenmode {i+1}' for i in index], fontsize=20)
    ax2.set_ylim(0, 1.05)
    ax2.legend(fontsize=20, loc='lower center', ncol=2) #bbox_to_anchor=(0.5, 1.0)
    # Grids
    ax2.grid(which='major', linestyle='-', linewidth=0.75, color='gray', alpha=0.5)
    ax2.minorticks_on()
    ax2.grid(which='minor', linestyle=':', linewidth=0.5, color='gray', alpha=0.3)

    fig1.tight_layout()
    plt.show(block=not all_at_once)


    # # -----------------------------------------------------------------------------
    # with open(path+"/tracked_modes.pkl", "rb") as f:
    #     tracked_clusters = pickle.load(f)


    # num_tracked_clusters = len(list(tracked_clusters.keys()))-1
    # num_ax = int(np.ceil((num_tracked_clusters)**(1/2)))

    # # set number of columns (use 3 to demonstrate the change)
    # ncols = 3
    # # calculate number of rows
    # nrows = num_tracked_clusters // ncols + (num_tracked_clusters % ncols > 0)

    # plt.figure(figsize=(20,12))
    # counter = 0
    # for ii in range(ncols):
    #     for jj in range(nrows):
    #         if counter < num_tracked_clusters:
    #             ax = plt.subplot(nrows, ncols, counter+1)
    #             cluster_data = tracked_clusters[str(counter)]
    #             median_freq = []
    #             ids = []
    #             for x in cluster_data:
    #                 median_freq.append(x['median_f'])
    #                 ids.append(x['id'])
    #             ax.set_title(f"Cluster: {counter}, avg_freq: {round(np.mean(median_freq),3)}", y=1.0, pad=-14)
    #             ax.scatter(ids,median_freq)
    #             xlim_2 = tracked_clusters['iteration']
    #             ax.set_xlim(0,xlim_2)
    #             if np.mean(median_freq) > 60:
    #                 ax.set_ylim(0,85)
    #             elif np.mean(median_freq) > 16:
    #                 ax.set_ylim(0,30)
    #             elif np.mean(median_freq) > 5:
    #                 ax.set_ylim(0,16)
    #             else:
    #                 ax.set_ylim(0,5)

    #         counter += 1


    # plt.show(block=not all_at_once)


    if all_at_once == True:
        plt.show(block=True)
    return