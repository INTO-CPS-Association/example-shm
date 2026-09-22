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
    print("Modal expansion")
    
    #Find DOF that are measured, and not validation DOF
    measure_loc, measure_id_data, validation_id = find_unique_dofs(params['sensor_loc'],params['validation_sensor_loc'])

    model_pars['modes'] = np.arange(measure_loc.shape[0])+1 #Number of model modes g must be <= to n_m
    print("modes",model_pars['modes'])
    _, _, _, myModel, _ = beam_new.eval_yafem_model(model_pars) #Fetch myModel

    model_pars['dofs_sel'] = myModel.dofs
    omega, Phi_all, Phi_selected, myModel, _ = beam_new.eval_yafem_model(model_pars)
    
    #Find DOF that are estimated, and not validation DOF
    estimate_loc, estimate_id, non_validation_sensor_id = find_unique_dofs(model_pars['dofs_sel'],measure_loc)

    #Find the location id of the validation sensor for the whole model/globally
    _, _, id_validation_sensor = find_unique_dofs(model_pars['dofs_sel'],params['validation_sensor_loc'])

    # Find non-measured DOF
    non_measured_loc, id_no_sensors, id_sensors = find_unique_dofs(myModel.dofs,params['sensor_loc'])
    print(id_sensors,id_no_sensors)
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
    sos = signal.butter(4, [90], 'low', analog=False, fs = params['Fs'], output='sos')
    y = signal.sosfilt(sos, y)

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


    #Integration:
    Disp = frequency_based_integration(y,params,order=2)

    model_pars['modes'] = [1,2,3]
    model_pars['dofs_sel'] = myModel.dofs
    _, _, Phi_selected, _, _ = beam_new.eval_yafem_model(model_pars)
    non_measured_loc, id_no_sensors, id_sensors = find_unique_dofs(myModel.dofs,params['sensor_loc'])
    
    #Estimate displacements based on all sensors, even the validation sensor
    Phi_alpha_S = Phi_selected[id_sensors,:] #Mode shapes of the measuremed locations
    Phi_beta_S = Phi_selected[id_no_sensors,:] #Mode shapes of the unmeasuremed locations

    # Estimate displacements
    d_alpha = Disp[:,:]
    print(d_alpha.shape)
    q_hat_disp = np.linalg.pinv(Phi_alpha_S) @ d_alpha #Find modal coordinates of measured points
    d_beta = Phi_beta_S @ q_hat_disp
    d_hat = np.zeros((myModel.ndof,N)) # np.zeros((unconstrained_model_loc.shape[0],y.shape[1]))
    for id, loc in enumerate(id_sensors):
            d_hat[loc,:] = d_alpha[id,:]
    for id, loc in enumerate(id_no_sensors):
            d_hat[loc,:] = d_beta[id,:]

    h = 1e-3
    b = 29e-3
    y_height = h/2
    I = b * h**3/12 

    model_pars['modes'] = [1,2,3]
    print("modes",model_pars['modes'])
    model_pars['dofs_sel'] = params['sensor_loc']
    _, _, Phi_selected, myModel, _ = beam_new.eval_yafem_model(model_pars)
    s = myModel.my_elements[5].s_phi.shape[0]
    N = Disp.shape[1]
    stress_beam = np.zeros((7,s,N)) # s x m
    strain_beam = np.zeros((7,s,N)) # s x m
    moment_beam = np.zeros((7,s,N)) # s x m
    for beam_element in [0,1,2,3,4,5,6]:
        moment_beam[beam_element,:] = (myModel.my_elements[beam_element+3].s_phi @ Disp) # [Nm]
        stress_beam[beam_element,:] = (myModel.my_elements[beam_element+3].s_phi @ Disp) * - y_height / I / 10**6 # [MPa]
        strain_beam[beam_element,:] = (myModel.my_elements[beam_element+3].e_phi @ Disp)


    # Find non-measured DOF
    model_pars['modes'] = [1,2,3]
    print("modes",model_pars['modes'])
    model_pars['dofs_sel'] = myModel.dofs
    _, _, Phi_selected, myModel, _ = beam_new.eval_yafem_model(model_pars)
    stress_beam2 = np.zeros((7,s,N)) # s x m
    strain_beam2 = np.zeros((7,s,N)) # s x m
    moment_beam2 = np.zeros((7,s,N)) # s x m
    for beam_element in [0,1,2,3,4,5,6]:
        moment_beam2[beam_element,:] = (myModel.my_elements[beam_element+3].s_phi @ d_hat) # [Nm]
        stress_beam2[beam_element,:] = (myModel.my_elements[beam_element+3].s_phi @ d_hat) * - y_height / I / 10**6 # [MPa]
        strain_beam2[beam_element,:] = (myModel.my_elements[beam_element+3].e_phi @ d_hat)

    # Find non-measured DOF
    model_pars['modes'] = [1,2,3]
    print("modes",model_pars['modes'])
    model_pars['dofs_sel'] = myModel.dofs
    _, _, Phi_selected, myModel, _ = beam_new.eval_yafem_model(model_pars)
    # Find non-measured DOF
    non_measured_loc, id_no_sensors, id_sensors = find_unique_dofs(myModel.dofs,params['sensor_loc'])
    #Estimate displacements based on all sensors, even the validation sensor
    Phi_alpha_S = Phi_selected[id_sensors,:] #Mode shapes of the measuremed locations
    Phi_beta_S = Phi_selected[id_no_sensors,:] #Mode shapes of the unmeasuremed locations
    # Validation
    acc_alpha = y
    q_acc = np.linalg.pinv(Phi_alpha_S) @ acc_alpha #Find modal coordinates of measured points
    acc_beta = Phi_beta_S @ q_acc #Find accelerations as modal coordinates that is non-measured (expansion)
    acc_hat = np.zeros((myModel.ndof,N)) #q for both measured and non-measured poins
    for id, loc in enumerate(id_sensors):
            acc_hat[loc,:] = acc_alpha[id,:]
    for id, loc in enumerate(id_no_sensors):
            acc_hat[loc,:] = acc_beta[id,:]
    Disp = frequency_based_integration(acc_hat,params,order=2)

    stress_beam3 = np.zeros((7,s,N)) # s x m
    strain_beam3 = np.zeros((7,s,N)) # s x m
    moment_beam3 = np.zeros((7,s,N)) # s x m
    for beam_element in [0,1,2,3,4,5,6]:
        moment_beam3[beam_element,:] = (myModel.my_elements[beam_element+3].s_phi @ Disp) # [Nm]
        stress_beam3[beam_element,:] = (myModel.my_elements[beam_element+3].s_phi @ Disp) * - y_height / I / 10**6 # [MPa]
        strain_beam3[beam_element,:] = (myModel.my_elements[beam_element+3].e_phi @ Disp)



    fig1, (ax1,ax2,ax3) = plt.subplots(1,3,figsize=(12, 4), tight_layout=True)
    ax1.plot(np.transpose(moment_beam[2,1,:]))
    ax2.plot(np.transpose(moment_beam2[2,1,:]))
    ax3.plot(np.transpose(moment_beam3[2,1,:]))
    plt.show(block=False)



    translation = [0,5,8,11,14,17]
    #translation = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19]
    fig1, (ax1,ax2,ax3) = plt.subplots(1,3,figsize=(12, 4), tight_layout=True)
    ax1.plot(np.transpose(d_hat[translation,:]))
    ax2.plot(np.transpose(Disp[translation,:]))

    ax3.plot(np.transpose(d_hat[translation,:]))
    ax3.plot(np.transpose(Disp[translation,:]),'--',linewidth=3)
    ax1.legend(["N1","N4","N5","N6","N7","N8"])
    plt.show(block=False)

    breakpoint()
    return d_hat, Disp, stress_beam, strain_beam, moment_beam, expansion_validation


def find_unique_dofs(a,b):
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

def trapezoidal_integration(y,params):
    print("\nNumerical integration")
    if params['output_type'] == 0:
        Disp = y
    elif params['output_type'] == 2:
        bias = np.mean(y,axis=1)
        bias = np.vstack([bias] * y.shape[1])

        y2 = y-np.transpose(bias)
        dt = 0.004
        v = np.zeros((y2.shape[0],y2.shape[1]))
        for ii in range(y2.shape[0]):
            for kk, y_ in enumerate(y2[ii,:]):
                b = kk*dt
                if kk != 0:
                    v[ii,kk] = (b-a)*((y2[ii,kk]+y2[ii,kk-1])/2) + v[ii,kk-1]
                else:
                    v[ii,kk] = (b-0)*((y2[ii,kk]+0)/2)
                a = kk*dt

        import scipy
        v = scipy.signal.detrend(v,axis=1,type="linear")
        vel = v
        u = np.zeros((v.shape[0],v.shape[1]))
        for ii in range(v.shape[0]):
            for kk, v_ in enumerate(v[ii,:]):
                b = kk*dt
                if kk != 0:
                    u[ii,kk] = (b-a)*((v[ii,kk]+v[ii,kk-1])/2) + u[ii,kk-1]
                else:
                    u[ii,kk] = (b-0)*((v[ii,kk]+0)/2)
                a = kk*dt
        #u = scipy.signal.detrend(u,axis=1,type="linear")
        Disp = u
    
    return Disp

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