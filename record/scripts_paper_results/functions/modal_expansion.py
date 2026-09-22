import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, AutoMinorLocator
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from scipy.fft import fft, ifft
from scipy import signal
from numpy.polynomial import Polynomial
import functions.fun_cantilever_beam_new as beam_new

def modal_expansion_run(data,params,model_pars,plot=False):
    #print("Modal expansion")

    # Experimental data transformation
    y = data
    ms, N = y.shape #Reshape y if it is transposed
    if N < ms:
        y = y.T
        ms, N = y.shape
    if N % 2 == 0: # Needed because of frequency integration?
        N -= 1
        y = y[:, :N]

    
    # plot_spectral_density(y,params)

    # Band-pass filtering of data
    try:
        filter_order = params.get('filter_order', 4)
        filter_type = params.get('filter_type', 'bandpass')
        filter_cut_off = params.get('filter_cut-off', np.array([0,10**6]))
        if filter_type is not None:
            sos = signal.butter(filter_order, filter_cut_off, filter_type, analog=False, fs = params['Fs'], output='sos')
            y = signal.sosfilt(sos, y)
             
    except Exception as e:
            print(f"Unexpected error: {e}")

    # plot_spectral_density(y,params)

    #Integration:
    disp = frequency_based_integration(y,params,order=params.get('detrend_integration_order',1))

    # Find non-measured DOF
    model_pars['modes'] = params['expansion_modes'] #Number of model modes g must be <= to n_m
    #print("modes",model_pars['modes'])
    model_pars['dofs_sel'] = params['sensor_loc']
    _, _, _, myModel, _ = beam_new.eval_yafem_model(model_pars)
    model_pars['dofs_sel'] = myModel.dofs
    _, _, Phi_selected, myModel2, _ = beam_new.eval_yafem_model(model_pars)
    non_measured_loc, id_no_sensors, id_sensors = find_unique_dofs(myModel2.dofs,params['sensor_loc'])
    #print(id_sensors,id_no_sensors)
    #Estimate displacements based on all sensors, even the validation sensor
    Phi_alpha_S = Phi_selected[id_sensors,:] #Mode shapes of the measuremed locations
    Phi_beta_S = Phi_selected[id_no_sensors,:] #Mode shapes of the unmeasuremed locations
    
    # Estimate displacements
    d_alpha = disp
    q_hat = np.linalg.pinv(Phi_alpha_S) @ d_alpha #Find modal coordinates of measured points
    d_beta = Phi_beta_S @ q_hat
    d_hat = np.zeros((myModel2.ndof,N)) # np.zeros((unconstrained_model_loc.shape[0],y.shape[1]))
    for idx, loc in enumerate(id_sensors):
            d_hat[loc,:] = d_alpha[idx,:]
    for idx, loc in enumerate(id_no_sensors):
            d_hat[loc,:] = d_beta[idx,:]

    # h = 1e-3
    # y_height = h/2

    # s = myModel.my_elements[params['beam_elements'][0]].s_phi.shape[0]
    # stress_beam = np.zeros((len(params['beam_elements']),s,N)) # s x m
    # strain_beam = np.zeros((len(params['beam_elements']),s,N)) # s x m
    # moment_beam = np.zeros((len(params['beam_elements']),s,N)) # s x m

    # for idx, beam_element in enumerate(params['beam_elements']):
    #     I = myModel.my_elements[beam_element].I
    #     moment_beam[idx,:] = (myModel.my_elements[beam_element].s_phi @ disp) # [Nm]
    #     stress_beam[idx,:] = (myModel.my_elements[beam_element].s_phi @ disp) * - y_height / I / 10**6 # [MPa]
    #     strain_beam[idx,:] = (myModel.my_elements[beam_element].e_phi @ disp)

    # L   = 0.530  # [m] ruler length
    # l1  = 0.030  # [m] distance from the beam top to the top accelerometer
    # l2  = 0.0675 # [m] distance between the tip and the middle accelerometers
    # l3  = 0.070 # [m] distance between the supports
    # l4 = 0.128925

    # nodes = np.array([[8,0.0,L        ,0.0], # tip mass
    #                 [7,0.0,L-l1     ,0.0], # acc 1
    #                 [6,0.0,L-l1-1*l2,0.0], # acc 3
    #                 [5,0.0,L-l1-2*l2,0.0], # acc 2
    #                 [4,0.0,L-l1-3*l2,0.0], # acc 4
    #                 [3,0.0,l4        ,0.0], # support 2
    #                 [2,0.0,l4-l3     ,0.0], # support 1
    #                 [1,0.0,0.0      ,0.0],
    #                 ])

    # fig, (ax1) = plt.subplots(1,1,figsize=(8, 6), tight_layout=True)
    # nodes_height = np.flip(nodes[:,2])
    # t = np.linspace(0, N / params['Fs'], N)
    # for beam_element, _ in enumerate(stress_beam[:,0]):
    #     label_str1 = "Ele." + str(beam_element+1) + "node:" + str(beam_element+1)
    #     # label_str2 = "Ele." + str(beam_element+1) + "node:" + str(beam_element+2)
    #     plt.plot(t,stress_beam[beam_element,1]/10+nodes_height[beam_element]*1000,label=label_str1)
    #     # plt.plot(t,stress_beam[beam_element,2]+nodes_height[beam_element+1]*1000,label=label_str2)
    # for i, txt in enumerate([1,2,3,4,5,6,7,8]):
    #     plt.annotate("Node "+str(txt), (0, nodes_height[i]*1000))
    # plt.legend()
    # sys.stdout.flush()

    # fig, (ax1,ax2,ax3) = plt.subplots(3,1,figsize=(6, 6), tight_layout=True)
    # t = np.linspace(0, N / params['Fs'], N)
    # ax1.plot(t,y[0,:])
    # ax1.set_ylabel("acceleration")
    # ax1.grid()

    # ax2.plot(t,d_hat[14,:])
    # ax2.set_ylabel("displacement")
    # ax2.grid()

    # ax3.plot(t,stress_beam[-1,1,:])
    # ax3.set_ylabel("stress")
    # ax3.grid()
    # plt.show()

    # fig, (ax2,ax3) = plt.subplots(2,1,figsize=(6, 4), tight_layout=True)
    # t = np.linspace(0, N / params['Fs'], N)
    # ax2.plot(t,d_hat[5,:])
    # ax2.set_ylabel("displacement")
    # ax2.grid()

    # ax3.plot(t,stress_beam[2,1,:])
    # ax3.set_ylabel("stress")
    # ax3.grid()

    # plt.show()

    # max_disp = np.max(abs(d_hat[:,:]),axis=1)*1000
    # rms = np.sqrt(np.mean(d_hat[-3,:]**2))

    # if max(max_disp) > 4 and max(max_disp) < 6:
    #     fig, (ax2) = plt.subplots(1,1,figsize=(6, 2), tight_layout=True)
    #     t = np.linspace(0, N / params['Fs'], N)
    #     for idx in [0,5,8,11,14,17]:
    #         ax2.plot(t,d_hat[idx,:],label=str(idx))
    #         ax2.set_ylabel("displacement") 
    #     ax2.legend()
    #     ax2.grid()
    #     plt.show(block=False)

    #     breakpoint()
    
    # fig, (ax2) = plt.subplots(1,1,figsize=(6, 2), tight_layout=True)
    # t = np.linspace(0, N / params['Fs'], N)
    # for idx in [0,1,2,3]:
    #     ax2.plot(t,disp[idx,:],label=str(idx))
    #     ax2.set_ylabel("displacement") 
    # ax2.legend()

    # plt.show()

    return d_hat


def find_unique_dofs(a: np.ndarray[int], b: np.ndarray[int]) -> tuple[np.ndarray[int], list[int], list[int]]:
    """
    Find the unique DOFs in a that are not in b, and return their indices.
    Args:
        a (np.ndarray[int]): Array of indecies of DOFs for the model
        b (np.ndarray[int]): Array of indecies of DOFs for the sensors
    Returns:
        unqiue_DOF (np.ndarray[int]): Array of indecies of unique DOFs in a that are not in b
        unique_ids (list[int]): List of indices of unique DOFs in a
        non_unique_ids (list[int]): List of indices of DOFs in a that are also in b

    """
    # remove dof from array
    unqiue_DOF = []
    unique_ids = []
    for id, dof in enumerate(a): #Go through the DOFs of a
        add_dof = True
        for dof2 in b: #Go through the DOFs of b
            if np.array_equal(dof,dof2): #If DOF_a is equa to DOF_b
                add_dof = False #Do not add DOF to list of unique DOF
        if add_dof == True: #Add DOF to unique list
            unqiue_DOF.append(dof)
            unique_ids.append(id)
    unqiue_DOF = np.array(unqiue_DOF)

    #Find the non unqiue indices
    non_unique_ids = []
    for ii, dof2 in enumerate(b):
        for jj, dof in enumerate(a):
            if np.array_equal(dof,dof2):
                non_unique_ids.append(jj)



    return unqiue_DOF, unique_ids, non_unique_ids

def modal_expansion_validation(data,params,model_pars,plot=False):
    #Find DOF that are measured, and not validation DOF
    measure_loc, measure_id_data, validation_id = find_unique_dofs(params['sensor_loc'],params['validation_sensor_loc'])
    if len(measure_id_data) < len(params['expansion_modes']):
        raise ValueError("Number of modes are larger than the number of non-validation sensors")
    model_pars['modes'] = params['expansion_modes'] #Number of model modes g must be <= to n_m
         
    model_pars['dofs_sel'] = params['sensor_loc']
    _, _, _, myModel, _ = beam_new.eval_yafem_model(model_pars) #Fetch myModel

    model_pars['dofs_sel'] = myModel.dofs
    omega, Phi_all, Phi_selected, myModel, _ = beam_new.eval_yafem_model(model_pars)
    
    #Find DOF that are estimated, and not validation DOF
    estimate_loc, estimate_id, non_validation_sensor_id = find_unique_dofs(model_pars['dofs_sel'],measure_loc)

    #Find the location id of the validation sensor for the whole model/globally
    _, _, id_validation_sensor = find_unique_dofs(model_pars['dofs_sel'],params['validation_sensor_loc'])

    #Construct mode shape matrix for measured and non-measured points
    Phi_alpha_S = Phi_selected[non_validation_sensor_id,:] #Mode shapes of the measuremed locations
    Phi_beta_S = Phi_selected[estimate_id,:] #Mode shapes of the unmeasuremed locations
    
    # Experimental data transformation
    y = data
    ms, N = y.shape #Reshape y if it is transposed
    if N < ms:
        y = y.T
        ms, N = y.shape
    if N % 2 == 0: # Needed because of frequency integration?
        N -= 1
        y = y[:, :N]

    # Band-pass filtering of data
    try:
        filter_order = params.get('filter_order', 4)
        filter_type = params.get('filter_type', 'low')
        filter_cut_off = params.get('filter_cut-off', np.array([10**6]))
        if filter_type is not None:
            sos = signal.butter(filter_order, filter_cut_off, filter_type, analog=False, fs = params['Fs'], output='sos')
            y = signal.sosfilt(sos, y)
    except Exception as e:
            print(f"Unexpected error: {e}")

    # Validation
    q_alpha = y[measure_id_data,:]
    q = np.linalg.pinv(Phi_alpha_S) @ q_alpha #Find modal coordinates of measured points
    q_beta = Phi_beta_S @ q #Find accelerations as modal coordinates that is non-measured (expansion)
    q_hat = np.zeros((model_pars['dofs_sel'].shape[0],N)) #q for both measured and non-measured poins
    for id, loc in enumerate(non_validation_sensor_id):
            q_hat[loc,:] = q_alpha[id,:]
    for id, loc in enumerate(estimate_id):
            q_hat[loc,:] = q_beta[id,:]

    if plot == True:
        fig_ax = plot_validation(q_hat[id_validation_sensor,:][0],y[validation_id,:][0],params)
        plt.show(block=True)
        sys.stdout.flush()

    expansion_validation = {}
    expansion_validation['y_expanded'] = q_hat[id_validation_sensor,:][0]
    expansion_validation['data_compare'] = y[validation_id,:][0]

    return expansion_validation



    

def frequency_based_integration(y,params,order = 2):
    ms, N = y.shape

     # Displacement estimation with frequency-domain integration
    if params['output_type'] == 0:
        Disp = y
    else: #If the output type is not displacements apply frequency based integration
        y_ = y - np.mean(y, axis=1, keepdims=True)
        YY = fft(y_.T, axis=0)
        Y = YY.T
        Nh = (N + 1) // 2
        cK = np.arange(1, Nh)
        D = np.zeros_like(Y, dtype=complex)
        omj = 1j * 2 * np.pi * cK * params['Fs'] / N
        
        if params['output_type'] == 1: #Velocity outputs
            D[:, 1:Nh] = Y[:, 1:Nh] / omj
            D[:, Nh:] = np.conj(np.flip(D[:, 1:Nh], axis=1))
        elif params['output_type'] == 2: #Acceleration outputs
            D[:, 1:Nh] = Y[:, 1:Nh] / (omj ** 2)
            D[:, Nh:] = np.conj(np.flip(D[:, 1:Nh], axis=1))
        else:
            raise ValueError('Unknown measurement type - please fix.')

        #Convert from frequency to physical domain
        Disp2 = ifft(D.T, axis=0)
        #print(f"Disp2: {Disp2.shape}")
        x = np.arange(Disp2.shape[0])  # Time indices or sample points
        Disp1 = np.zeros_like(Disp2)  # Initialize the detrended array with the same shape
        for i in range(Disp2.shape[1]):  # Loop over each column (sensor)
            # Fit a second-order polynomial to the data (column-wise)
            poly_coeffs = Polynomial.fit(x, Disp2[:, i], order)
            # Calculate the trend (second-order polynomial evaluated at x)
            trend = poly_coeffs(x)
            # Subtract the trend from the data
            Disp1[:, i] = Disp2[:, i] - trend
        Disp = Disp1.T

    if np.linalg.norm(np.imag(Disp)) > np.linalg.norm(np.real(Disp)) * 1e-8:
        raise ValueError('The displacements are complex-valued - please fix.')
    else:
        Disp = np.real(Disp)
    
    return Disp

def plot_spectral_density(y,params):
    # Spectrum test
    fig1, (ax1) = plt.subplots(1,1,figsize=(8, 6), tight_layout=True)
    fs = params['Fs']  # Sampling frequency (Hz)
    duration = 2*60
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)
    # Applying FFT
    for ii, y_data in enumerate(y[:,0]):
        fft_result = np.fft.fft(y[ii,:])
        freq = np.fft.fftfreq(t.shape[-1], d=1/fs)

        # Plotting the spectrum
        ax1.plot(freq[:-1], np.abs(fft_result))
        ax1.set_xlabel('Frequency (Hz)')
        ax1.set_ylabel('Amplitude')
        ax1.set_xlim(0,fs/2)
    ax1.legend(["acc1,node7","acc2,node6","acc3,node5","acc4,node4"])
    ax1.set_title("Filtered FFT")
    plt.show(block=False)

def plot_validation(d_hat,data_compare,params):

    t = np.linspace(0, d_hat.shape[0] / params['Fs'], d_hat.shape[0])   # time in seconds of data

    #fig, ax1 = plt.subplots(figsize=(8, 6))
    fig, ax1 = plt.subplots(figsize=(12, 4))

    # ax1.plot(t, data_compare[1:],'--r', t, y_expanded[3,:], 'k')
    ax1.plot(t, data_compare*9.81, linestyle='--', color='tab:red',zorder=3)
    ax1.plot(t, d_hat*9.81, color='tab:blue',zorder=0)
    # ax1.set_ylabel(r'$\ddot{y}(t)$ [g]', fontsize=20)
    # ax1.set_xlabel(r'$t$ [sec]', fontsize=20)
    ax1.set_ylabel(r'Acceleration [m/s$^2$]', fontsize=20)
    ax1.set_xlabel('Time [s]', fontsize=20)
    ax1.legend(['Measured', 'Modal expanded'], fontsize=18, loc='upper left')
    ax1.grid(which='major', color='gray', linestyle='-', linewidth=0.5)
    ax1.grid(which='minor', color='lightgray', linestyle='--', linewidth=0.3)
    ax1.set_xticks(np.arange(0, 120.01, 10))   # Tick every 5 units
    ax1.tick_params(axis='both', labelsize=17, labelcolor='black')
    ax1.set_ylim(-12, 12)
    ax1.set_xlim(0, 120)

    # Create inset axes
    # axins = inset_axes(ax1, width="40%", height="45%", bbox_to_anchor=(0, 0, 1, 1))
    axins = ax1.inset_axes([0.55,0.1,0.4,0.45])  # inside upper rights
    axins.plot(t, data_compare*9.81, linestyle='--', color='tab:red',zorder=3)
    axins.plot(t, d_hat*9.81, color='tab:blue',zorder=0)
    axins.set_xlim(45, 46)      # Adjust zoom range for x
    axins.set_ylim(-5, 5.01)      # Adjust zoom range for y
    # Set inset ticks based on the same logic as main axis
    axins.set_xticks(np.arange(45, 46.01, 0.2))   # Tick every 5 units
    axins.set_yticks(np.arange(-5, 5.01, 2.5))   # Tick every 3 unit
    axins.grid(which='major', color='gray', linestyle='-', linewidth=0.5)
    axins.grid(which='minor', color='lightgray', linestyle='--', linewidth=0.3)
    # Format tick labels to match main plot
    axins.tick_params(labelsize=13, colors='black')

    fig.tight_layout()
    fig.canvas.draw()
    fig.canvas.flush_events()
    
    return fig, ax1