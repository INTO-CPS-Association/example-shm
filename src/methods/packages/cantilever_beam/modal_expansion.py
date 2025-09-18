import sys
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from scipy.fft import fft, ifft
from numpy.polynomial import Polynomial
from methods.packages.cantilever_beam import eval_yafem_model as beam_new

# Function placeholders for modal expansion, mode pairing, and model eigenvalue calculations.

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
    ax1.tick_params(axis='both', labelsize=17, labelcolor='black')
    ax1.set_ylim(-10, 10)
    ax1.set_xlim(25, 28)
    ax1.set_xlim(0, 120)

    # Create inset axes
    axins = inset_axes(ax1, width="40%", height="50%", loc=('lower right'))  # inside upper right
    axins.plot(t, data_compare*9.81, linestyle='--', color='tab:red',zorder=3)
    axins.plot(t, d_hat*9.81, color='tab:blue',zorder=0)
    axins.set_xlim(25, 28)      # Adjust zoom range for x
    axins.set_ylim(-6, 6)      # Adjust zoom range for y
    # Set inset ticks based on the same logic as main axis
    axins.set_xticks(np.arange(25, 28, 1))   # Tick every 5 units
    axins.set_yticks(np.arange(-6, 6, 2))   # Tick every 1 unit
    axins.grid(which='major', color='gray', linestyle='-', linewidth=0.5)
    axins.grid(which='minor', color='lightgray', linestyle='--', linewidth=0.3)
    # Format tick labels to match main plot
    axins.tick_params(labelsize=10, colors='black')

    fig.tight_layout()
    fig.canvas.draw()
    fig.canvas.flush_events()
    
    return fig, ax1


def modal_expansion_run(data,params,model_pars,plot=False):
    print("Modal expansion")
    #Fint DOF that are measured, and not validation DOF
    measure_loc, measure_id, validation_id = find_unique_dofs(params['sensor_loc'],params['validation_sensor_loc'])

    model_pars['modes'] = np.arange(measure_loc.shape[0])+1 #Number of model modes g must be <= to n_m
    _, _, _, myModel = beam_new.eval_yafem_model(model_pars)

    if type(params['model_sel_DOF']) is str:
         if params['model_sel_DOF'] == "all":
              model_pars['dofs_sel'] = myModel.dofs
    else:
        model_pars['dofs_sel'] = params['model_sel_DOF'] #7,1 and 6,1 are locked, so they won't result in a mode shape
    omega, Phi_all, Phi_selected, myModel = beam_new.eval_yafem_model(model_pars)

    model_pars['dofs_c'] = np.array([[3,1],[2,1]])
    # Find DOF that are unconstrained
    unconstrained_model_loc, free_dof, constrained_dof = find_unique_dofs(model_pars['dofs_sel'],model_pars['dofs_c'])
    # Find non-measured DOF
    non_measured_loc, id_no_sensors, id_sensors = find_unique_dofs(unconstrained_model_loc,measure_loc)
    #Construct mode shape matrix for measured and non-measured points
    Phi_alpha_S = Phi_selected[id_sensors,:] #Mode shapes of the measuremed locations
    Phi_beta_S = Phi_selected[id_no_sensors,:] #Mode shapes of the unmeasuremed locations
    
    # Experimental data transformation
    y = data
    ms, N = y.shape #Reshape y if it is transposed
    if N < ms:
        y = y.T
        ms, N = y.shape
    if N % 2 == 0: # Needed because of frequency integration?
        N -= 1
        y = y[:, :N]

    # Validation
    q_alpha = y[measure_id,:]
    q = np.linalg.solve(Phi_alpha_S.T, q_alpha) #Find modal coordinates of measured points
    q_beta = Phi_beta_S @ q #Find accelerations
    q_hat = np.zeros((unconstrained_model_loc.shape[0],N)) #q for both measured and non-measured poins
    for id, loc in enumerate(id_sensors):
            q_hat[loc,:] = q_alpha[id,:]
    for id, loc in enumerate(id_no_sensors):
            q_hat[loc,:] = q_beta[id,:]

    if plot == True:
        fig_ax = plot_validation(q_hat[validation_id,:][0],y[validation_id,:][0],params)
        plt.show(block=True)
        sys.stdout.flush()

    # Displacement estimation
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
            poly_coeffs = Polynomial.fit(x, Disp2[:, i], 2)
            # Calculate the trend (second-order polynomial evaluated at x)
            trend = poly_coeffs(x)
            # Subtract the trend from the data
            Disp1[:, i] = Disp2[:, i] - trend
        Disp = Disp1.T

    if np.linalg.norm(np.imag(Disp)) > np.linalg.norm(np.real(Disp)) * 1e-8:
        raise ValueError('The displacements are complex-valued - please fix.')
    else:
        Disp = np.real(Disp)


    # Estimate displacements
    d_alpha = Disp[measure_id,:]
    q_hat = np.linalg.solve(Phi_alpha_S.T, d_alpha) #Find modal coordinates of measured points
    d_beta = Phi_beta_S @ q_hat
    d_hat = np.zeros((myModel.ndof,N)) # np.zeros((unconstrained_model_loc.shape[0],y.shape[1]))
    for id, loc in enumerate(id_sensors):
            d_hat[loc,:] = d_alpha[id,:]
    for id, loc in enumerate(id_no_sensors):
            d_hat[loc,:] = d_beta[id,:]
    d = np.zeros((model_pars['dofs_sel'].shape[0],N))
    for ii, id in enumerate(free_dof):
        d[id,:] = d_hat[ii,:]

    # Stress-strain estimation
    model_pars['dofs_sel'] = params['sensor_loc']
    model_pars['modes'] = 1
    omegaM, phi, PhiM, myModel = beam_new.eval_yafem_model(model_pars)

    h = 1e-3
    b = 29e-3
    y_height = h/2
    I = b * h**3/12 

    L   = 0.530  # [m] ruler length
    l1  = 0.030  # [m] distance from the beam top to the top accelerometer
    l2  = 0.0675 # [m] distance between the tio and the middle accelerometers
    l3  = 0.070 # [m] distance between the supports
    l4 = 0.128

    nodes = np.array([[8,0.0,L        ,0.0], # tip mass
                    [7,0.0,L-l1     ,0.0], # acc 1
                    [6,0.0,L-l1-1*l2,0.0], # acc 3
                    [5,0.0,L-l1-2*l2,0.0], # acc 2
                    [4,0.0,L-l1-3*l2,0.0], # acc 4
                    [3,0.0,l4        ,0.0], # support 2
                    [2,0.0,l4-l3     ,0.0], # support 1
                    [1,0.0,0.0      ,0.0],
                    ])


    d_m = Disp
    s = myModel.my_elements[5].s_phi.shape[0]
    N = d_m.shape[1]
    stress_beam = np.zeros((7,s,N)) # s x m
    strain_beam = np.zeros((7,s,N)) # s x m
    moment_beam = np.zeros((7,s,N)) # s x m
    for beam_element in [0,1,2,3,4,5,6]:
        print(myModel.my_elements[beam_element+3].s_phi.shape)
        moment_beam[beam_element,:] = (myModel.my_elements[beam_element+3].s_phi @ d_m) # [Nm]
        stress_beam[beam_element,:] = (myModel.my_elements[beam_element+3].s_phi @ d_m) * y_height / I / 10**6 # [MPa]
        strain_beam[beam_element,:] = (myModel.my_elements[beam_element+3].e_phi @ d_m)


    if plot == True:
        nodes_height = np.flip(nodes[:,2])
        t = np.linspace(0, N / params['Fs'], N)
        for beam_element, _ in enumerate(stress_beam[:,0]):
            label_str1 = "Ele." + str(beam_element+1) + "node:" + str(beam_element+1)
            label_str2 = "Ele." + str(beam_element+1) + "node:" + str(beam_element+2)
            plt.plot(t,stress_beam[beam_element,1]+nodes_height[beam_element]*1000,label=label_str1)
            plt.plot(t,stress_beam[beam_element,2]+nodes_height[beam_element+1]*1000,label=label_str2)
        for i, txt in enumerate([1,2,3,4,5,6,7,8]):
            plt.annotate("Node "+str(txt), (0, nodes_height[i]*1000))
        plt.legend()
        plt.show(block=True)
        sys.stdout.flush()

    # nodes_height = np.flip(nodes[:,2])
    # plt.plot(stress_beam[:,1,-1],nodes[1:,2]*1000)
    # for i, txt in enumerate([1,2,3,4,5,6,7,8]):
    #     plt.annotate("Node "+str(txt), (0, nodes_height[i]*1000))
    # plt.show(block=True)

    print("moment",moment_beam[2,1,-1],moment_beam[2,2,-1],moment_beam[3,1,-1],moment_beam[3,2,-1],moment_beam[4,1,-1],moment_beam[4,2,-1],moment_beam[5,1,-1],moment_beam[5,2,-1],moment_beam[6,1,-1],moment_beam[6,2,-1])
    return d_hat, stress_beam, strain_beam, moment_beam
    

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
    

