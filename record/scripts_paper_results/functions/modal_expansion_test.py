import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, AutoMinorLocator
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from scipy.fft import fft, ifft
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
    non_measured_loc, id_no_sensors, id_sensors = find_unique_dofs(model_pars['dofs_sel'],params['sensor_loc'])
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
        # fig_ax = plot_validation(q_hat[8,:],y[2,:],params)
        # plt.show(block=True)
        # sys.stdout.flush()
        fig_ax = plot_validation(q_hat[id_validation_sensor,:][0],y[validation_id,:][0],params)
        plt.show(block=True)
        sys.stdout.flush()

    expansion_validation = {}
    expansion_validation['y_expanded'] = q_hat[id_validation_sensor,:][0]
    expansion_validation['data_compare'] = y[validation_id,:][0]


    # Stress-strain estimation
    model_pars['dofs_sel'] = params['sensor_loc']
    model_pars['dofs_sel'] = np.array([[1, 1],[1, 2],[1, 3],[2, 3],[3, 3],[4, 1],[4, 2],[4, 3],[5, 1],[5, 2],[5, 3],[6, 1],[6, 2],[6, 3],[7, 1],[7, 2],[7, 3],[8, 1],[8, 2],[8, 3]])
    model_pars['modes'] = [1,2,3]
    omegaM, phi, PhiM, myModel, mySimulation = beam_new.eval_yafem_model(model_pars)

    # [u, v, acc, r] = mySimulation.dynamic_analysis(output=False)

    # np.save("C:/project_cp-sens/demo_cantilever_beam/beam_paper/data/simulated_acc",acc)
    # np.save("C:/project_cp-sens/demo_cantilever_beam/beam_paper/data/simulated_dis",u)

    acc = np.load("C:/project_cp-sens/demo_cantilever_beam/beam_paper/data/simulated_acc.npy")
    u = np.load("C:/project_cp-sens/demo_cantilever_beam/beam_paper/data/simulated_dis.npy")

    fig1, (ax1) = plt.subplots(1,1,figsize=(8, 6), tight_layout=True)
    ax1.plot(np.transpose(u))
    ax1.set_title("Discplacements simualted")
    

    # params['output_type'] = 0
    # if params['output_type'] == 2:
    #     y = acc[[14,11,8,5],:]
    # elif params['output_type'] == 1:
    #     y = v[[14,11,8,5],:]
    # else:
    #     y = u[[14,11,8,5],:]

    # params['output_type'] = 2
    # if params['output_type'] == 2:
    #     y = acc
    # elif params['output_type'] == 1:
    #     y = v
    # else:
    #     y = u
    # d_m = u[[5,8,11,14],:] #Does not match with order of 'dofs_sel', i.e. it does not work
    
    ms, N = y.shape #Reshape y if it is transposed
    if N < ms:
        y = y.T
        ms, N = y.shape
    if N % 2 == 0: # Needed because of frequency integration?
        N -= 1
        y = y[:, :N]

    y2 = y.copy()

    # #Add noise
    # np.random.seed(1)
    # NSR = 0.02
    # sigy = np.std(y2,axis=1)
    # v = np.multiply(NSR * sigy, np.random.randn(N,ms))
    # y = y2 + np.transpose(v)
    
    from scipy import signal

    b, a = signal.butter(4, [90], 'low', analog=False, fs = 250)
    sos = signal.butter(4, [90], 'low', analog=False, fs = 250, output='sos')

    #y = signal.sosfilt(sos, y)



    # # Harmonic acceleration
    # t = np.linspace(0,40,9999)
    # y = np.zeros((1,9999))
    # omega = 1
    # omega2 = 30
    # omega3 = 5
    # for i in range(y.shape[0]):
    #     y[i,:] = np.sin(t*np.pi*2*omega) #+ np.sin(t*np.pi*2*omega2) + np.sin(t*np.pi*2*omega3)

    # Linear acceleration
    # t = np.linspace(0,40,9999)
    # y = np.ones((1,9999))


    t = np.linspace(0,40,9999)
    test = np.linspace(-10,10,9999)+np.sin(t*2*np.pi*1)
    import scipy
    test_detrended = scipy.signal.detrend(test,type="linear")
    fig1, (ax1,ax2) = plt.subplots(1,2,figsize=(8, 6), tight_layout=True)
    ax1.plot(t,test)
    ax2.plot(t,test_detrended)
    ax2.set_ylim([-1,1])
    plt.show(block=False)
    

    # ms, N = y.shape
    # np.random.seed(1)
    # NSR = 0.05
    # sigy = np.std(y,axis=1)
    # v = np.multiply(NSR * sigy, np.random.randn(N,ms))
    # y = y + np.transpose(v)

    # zero_padding = np.zeros((y.shape[0],15001))
    # zero_padding[:,0:9999] = y
    # y = zero_padding

    ms, N = y.shape #Reshape y if it is transposed
    if N < ms:
        y = y.T
        ms, N = y.shape
    if N % 2 == 0: # Needed because of frequency integration?
        N -= 1
        y = y[:, :N]

    # #Spectrum test
    # # Generating a sample musical note signal
    # fig1, (ax1) = plt.subplots(1,1,figsize=(8, 6), tight_layout=True)
    # fs = 256  # Sampling frequency (Hz)
    # duration = 2*60
    # t = np.linspace(0, duration, int(fs * duration), endpoint=False)
    # # Applying FFT
    # for ii, y_data in enumerate(y[:,0]):
    #     fft_result = np.fft.fft(y[ii,:])
    #     freq = np.fft.fftfreq(t.shape[-1], d=1/fs)

    #     # Plotting the spectrum
    #     ax1.plot(freq[:-1], np.abs(fft_result))
    #     ax1.set_xlabel('Frequency (Hz)')
    #     ax1.set_ylabel('Amplitude')
    #     ax1.set_xlim(0,fs/2)
    # ax1.legend(["acc1,node7","acc2,node6","acc3,node5","acc4,node4"])
    # ax1.set_title("Filtered FFT")
    # plt.show(block=False)

    # # Spectrum test
    # # Generating a sample musical note signal
    # fig2, (ax2) = plt.subplots(1,1,figsize=(8, 6), tight_layout=True)
    # fs = 256  # Sampling frequency (Hz)
    # duration = 2*60
    # t = np.linspace(0, duration, int(fs * duration), endpoint=False)
    # # Applying FFT
    # for ii, y_data in enumerate(y2[:,0]):
    #     fft_result = np.fft.fft(y2[ii,:])
    #     freq = np.fft.fftfreq(t.shape[-1], d=1/fs)

    #     # Plotting the spectrum
    #     ax2.plot(freq[:-1], np.abs(fft_result))
    #     ax2.set_xlabel('Frequency (Hz)')
    #     ax2.set_ylabel('Amplitude')
    #     ax2.set_xlim(0,fs/2)
    # ax2.legend(["acc1,node7","acc2,node6","acc3,node5","acc4,node4"])
    # ax2.set_title("No filter FFT")
    # plt.show(block=False)´

    # Spectrum test
    # Generating a sample musical note signal
    fig1, (ax1) = plt.subplots(1,1,figsize=(8, 6), tight_layout=True)
    fs = 250  # Sampling frequency (Hz)
    duration = 40
    tt = np.linspace(0, duration, int(fs * duration), endpoint=False)
    # Applying FFT
    for ii, y_data in enumerate(y[:,0]):
        fft_result = np.fft.fft(y[ii,:])
        freq = np.fft.fftfreq(tt.shape[-1], d=1/fs)

        # Plotting the spectrum
        ax1.plot(freq[:4999], np.abs(fft_result[:4999]))
        ax1.set_xlabel('Frequency (Hz)')
        ax1.set_ylabel('Amplitude')
        ax1.set_xlim(0,fs/2)
    ax1.legend(["acc1,node7","acc2,node6","acc3,node5","acc4,node4"])
    ax1.set_title("Filtered FFT")
    plt.show(block=False)

    # # Spectrum test
    # # Generating a sample musical note signal
    # fig2, (ax2) = plt.subplots(1,1,figsize=(8, 6), tight_layout=True)
    # fs = 250  # Sampling frequency (Hz)
    # duration = 40
    # tt = np.linspace(0, duration, int(fs * duration), endpoint=False)
    # # Applying FFT
    # for ii, y_data in enumerate(y2[:,0]):
    #     fft_result = np.fft.fft(y2[ii,:])
    #     freq = np.fft.fftfreq(tt.shape[-1], d=1/fs)

    #     # Plotting the spectrum
    #     ax2.plot(freq[:4999], np.abs(fft_result[:4999]))
    #     ax2.set_xlabel('Frequency (Hz)')
    #     ax2.set_ylabel('Amplitude')
    #     ax2.set_xlim(0,fs/2)
    # ax2.legend(["acc1,node7","acc2,node6","acc3,node5","acc4,node4"])
    # ax2.set_title("No filter FFT")
    # plt.show(block=False)

    # fig3, (ax3) = plt.subplots(1,1,figsize=(8, 6), tight_layout=True)
    # ax3.plot(y[0,:])
    # ax3.plot(y2[0,:])
    # ax3.legend(["Filtered","Nofilter"])
    # plt.show(block=False)





    fs = 255
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
        omj = 1j * 2 * np.pi * cK * fs / N
        
        if params['output_type'] == 1: #Velocity outputs
            D[:, 1:Nh] = Y[:, 1:Nh] / omj
            D[:, Nh:] = np.conj(np.flip(D[:, 1:Nh], axis=1))
        elif params['output_type'] == 2: #Acceleration outputs
            D[:, 1:Nh] = Y[:, 1:Nh] / (omj ** 2)
            D[:, Nh:] = np.conj(np.flip(D[:, 1:Nh], axis=1))
        else:
            raise ValueError('Unknown measurement type - please fix.')

        #Convert from frequency to physical domain
        D1 = D[:,0:9999]
        Disp2 = ifft(D1.T, axis=0)
        #print(f"Disp2: {Disp2.shape}")
        x = np.arange(Disp2.shape[0])  # Time indices or sample points
        Disp1 = np.zeros_like(Disp2)  # Initialize the detrended array with the same shape

        fig1, (ax1,ax2,ax3) = plt.subplots(1,3,figsize=(12, 4), tight_layout=True)    
        for i in range(Disp2.shape[1]):  # Loop over each column (sensor)
            # Fit a second-order polynomial to the data (column-wise)
            poly_coeffs = Polynomial.fit(x, Disp2[:, i], 2)
            # Calculate the trend (second-order polynomial evaluated at x)
            trend = poly_coeffs(x)
            # Subtract the trend from the data
            Disp1[:, i] = Disp2[:, i] - trend

            ax1.plot(x,Disp2[:, i])
            ax1.set_title("Disp. before detrend")
            ax2.plot(x,Disp1[:, i])
            ax2.set_title("Disp. after detrend")
            ax3.plot(x,trend)
            ax3.set_title("Detrend")
        # trend = scipy.signal.detrend(Disp2,axis=1,type="linear")
        # Disp1 = Disp2 - trend

        Disp = Disp1.T
        # Disp = Disp2.T
    # if np.linalg.norm(np.imag(Disp)) > np.linalg.norm(np.real(Disp)) * 1e-8:
    #     raise ValueError('The displacements are complex-valued - please fix.')
    # else:
    Disp = np.real(Disp)

    import scipy
    #Disp = scipy.signal.detrend(Disp,axis=1,type="linear")
    freq_Disp = Disp

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
        
        fig1, (ax1,ax2,ax3) = plt.subplots(1,3,figsize=(12, 4), tight_layout=True)
        ax1.plot(np.transpose(y))
        ax1.set_title("Acceleration")
        ax2.plot(np.transpose(v))
        ax2.set_title("Velocity")
        ax3.plot(np.transpose(u))
        ax3.set_title("Displacesments trapezoidal")



    print("\nNumerical integration mid-point-rule")
    if params['output_type'] == 0:
        Disp = y
    elif params['output_type'] == 2:
        bias = np.mean(y,axis=1)
        bias = np.vstack([bias] * y.shape[1])

        y2 = y-np.transpose(bias)


        dx = 0.004
        v = np.zeros((y2.shape[0],y2.shape[1]))
        for ii in range(y2.shape[0]):
            for kk, y_ in enumerate(y2[ii,:]):
                if kk != 0:
                    v[ii,kk] = y2[ii,kk]*dx + v[ii,kk-1]
                else:
                    v[ii,kk] = y2[ii,kk]*dx
        import scipy
        v = scipy.signal.detrend(v,axis=1,type="linear")
        vel_mp = v
        u = np.zeros((v.shape[0],v.shape[1]))
        for ii in range(v.shape[0]):
            for kk, v_ in enumerate(v[ii,:]):
                if kk != 0:
                    u[ii,kk] = v[ii,kk]*dx + u[ii,kk-1]
                else:
                    u[ii,kk] = v[ii,kk]*dx
        #u = scipy.signal.detrend(u,axis=1,type="linear")
        Disp_mid = u
        
        fig1, (ax1,ax2,ax3) = plt.subplots(1,3,figsize=(12, 4), tight_layout=True)
        ax1.plot(np.transpose(y))
        ax1.set_title("Acceleration")
        ax2.plot(np.transpose(v))
        ax2.set_title("Velocity")
        ax3.plot(np.transpose(u))
        ax3.set_title("Displacesments mid-point")




    fig1, (ax1,ax2,ax3) = plt.subplots(1,3,figsize=(12, 4), tight_layout=True)    
    ax1.plot(np.transpose(Disp[0,:]),color="k",linewidth=3,label="Integrated")
    ax1.set_title("Displacement trapezoid-rule")
    ax2.plot(np.transpose(Disp_mid[0,:]),color="k",linewidth=3,label="Integrated")
    ax2.set_title("Displacement midpoint-rule")
    ax3.plot(np.transpose(freq_Disp[0,:]),color="k",linewidth=3,label="Integrated")
    ax3.set_title("Displacement frequency-based")

    # analytical_harmonic = -(1/(np.pi*2*omega)**2)*np.sin(t*np.pi*2*omega)
    # # analytical_harmonic = -(1/(np.pi*2*omega)**2)*np.sin(t*np.pi*2*omega) + (-(1/(np.pi*2*omega2)**2)*np.sin(t*np.pi*2*omega2)) + (-(1/(np.pi*2*omega3)**2)*np.sin(t*np.pi*2*omega3))
    # ax1.plot(analytical_harmonic,'--r',label="Analytical")
    # ax2.plot(analytical_harmonic,'--r',label="Analytical")
    # ax3.plot(analytical_harmonic,'--r',label="Analytical")
    # ax1.legend()

    # print(analytical_harmonic.shape)
    # print(Disp[0,:].shape)
    # print(np.hstack((analytical_harmonic,Disp[0,:])))
    # norm_f = np.linalg.norm(np.hstack((analytical_harmonic,freq_Disp[0,:])),ord=2)
    # norm = np.linalg.norm(np.hstack((analytical_harmonic,Disp[0,:])),ord=2)
    # norm_mp = np.linalg.norm(np.hstack((analytical_harmonic,Disp_mid[0,:])),ord=2)
    # print(norm_f,norm,norm_mp)
    

    fig1, (ax1,ax2,ax3) = plt.subplots(1,3,figsize=(12, 4), tight_layout=True)    
    ax1.plot(np.transpose(scipy.signal.detrend(Disp[0,:],type="linear")),color="k",linewidth=3,label="Integrated")
    ax1.set_title("Displacement trapezoid-rule")
    ax2.plot(np.transpose(scipy.signal.detrend(Disp_mid[0,:],type="linear")),color="k",linewidth=3,label="Integrated")
    ax2.set_title("Displacement midpoint-rule")
    ax3.plot(np.transpose(freq_Disp[0,:]-np.flip(np.linspace(-0.000605,0.000605,9999)-0.00001)),color="k",linewidth=3,label="Integrated")
    ax3.set_title("Displacement frequency-based")

    # analytical_harmonic = -(1/(np.pi*2*omega)**2)*np.sin(t*np.pi*2*omega)
    # # analytical_harmonic = -(1/(np.pi*2*omega)**2)*np.sin(t*np.pi*2*omega) + (-(1/(np.pi*2*omega2)**2)*np.sin(t*np.pi*2*omega2)) + (-(1/(np.pi*2*omega3)**2)*np.sin(t*np.pi*2*omega3))
    # ax1.plot(analytical_harmonic,'--r',label="Analytical")
    # ax2.plot(analytical_harmonic,'--r',label="Analytical")
    # ax3.plot(analytical_harmonic,'--r',label="Analytical")
    # ax1.legend()

    # print(analytical_harmonic.shape)
    # print(Disp[0,:].shape)
    # print(np.hstack((analytical_harmonic,Disp[0,:])))
    # norm_f = np.linalg.norm(np.hstack((analytical_harmonic,freq_Disp[0,:])),ord=2)
    # norm = np.linalg.norm(np.hstack((analytical_harmonic,Disp[0,:])),ord=2)
    # norm_mp = np.linalg.norm(np.hstack((analytical_harmonic,Disp_mid[0,:])),ord=2)
    # print(norm_f,norm,norm_mp)


    fig1, (ax1,ax2) = plt.subplots(1,2,figsize=(8, 4), tight_layout=True)    
    ax1.plot(np.transpose(vel[0,:]),color="k",linewidth=3,label="Integrated")
    ax1.set_title("Velocity trapezoid-rule")
    ax2.plot(np.transpose(vel_mp[0,:]),color="k",linewidth=3,label="Integrated")
    ax2.set_title("Velocity midpoint-rule")

    plt.show(block=True)
    quit()










    d_m = Disp

    modes = [0,1,2,3,4,5,6,7,8,9,10,11,12,15]
    #modes = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18]
    converged_moment = []
    for mode in modes:
        # Find non-measured DOF
        model_pars['modes'] = np.array(list(range(mode+1)))+1
        print("modes",model_pars['modes'])
        omega, _, Phi_selected, myModel, _ = beam_new.eval_yafem_model(model_pars)
        # if mode == 18:
        #     breakpoint()

        h = 1e-3
        b = 29e-3
        y_height = h/2
        I = b * h**3/12 

        L   = 0.530  # [m] ruler length
        l1  = 0.030  # [m] distance from the beam top to the top accelerometer
        l2  = 0.0675 # [m] distance between the tip and the middle accelerometers
        l3  = 0.070 # [m] distance between the supports
        l4 = 0.128925

        nodes = np.array([[8,0.0,L        ,0.0], # tip mass
                        [7,0.0,L-l1     ,0.0], # acc 1
                        [6,0.0,L-l1-1*l2,0.0], # acc 3
                        [5,0.0,L-l1-2*l2,0.0], # acc 2
                        [4,0.0,L-l1-3*l2,0.0], # acc 4
                        [3,0.0,l4        ,0.0], # support 2
                        [2,0.0,l4-l3     ,0.0], # support 1
                        [1,0.0,0.0      ,0.0],
                        ])

        s = myModel.my_elements[5].s_phi.shape[0]
        N = d_m.shape[1]
        stress_beam = np.zeros((7,s,N)) # s x m
        strain_beam = np.zeros((7,s,N)) # s x m
        moment_beam = np.zeros((7,s,N)) # s x m
        for beam_element in [0,1,2,3,4,5,6]:
            moment_beam[beam_element,:] = (myModel.my_elements[beam_element+3].s_phi @ d_m) # [Nm]
            stress_beam[beam_element,:] = (myModel.my_elements[beam_element+3].s_phi @ d_m) * -y_height / I / 10**6 # [MPa]
            strain_beam[beam_element,:] = (myModel.my_elements[beam_element+3].e_phi @ d_m)
    
        #converged_moment.append(np.mean(moment_beam[2,1,:]))
        converged_moment.append(moment_beam[2,1,4998])
    
    fig, (ax1) = plt.subplots(1,1,figsize=(8, 6), tight_layout=True)
    ax1.plot(np.array(modes)+1,converged_moment,"-o")
    ax1.set_ylabel("Moment [Nm]")
    ax1.set_xlabel("Modes")
    ax1.set_title("Converged moment, trapezoidal rule")
    ax1.set_xlim([0,20])
    ax1.set_xticks(list(range(21)))
    ax1.grid()
    print("Omega 17 modes",omega)
    
    d_m = freq_Disp
    modes = [0,1,2,3,4,5,6,7,8,9,10,11,12,15]
    #modes = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18]
    converged_moment = []
    for mode in modes:
        # Find non-measured DOF
        model_pars['modes'] = np.array(list(range(mode+1)))+1
        print("modes",model_pars['modes'])
        omega, _, Phi_selected, myModel, _ = beam_new.eval_yafem_model(model_pars)
        # if mode == 18:
        #     breakpoint()

        h = 1e-3
        b = 29e-3
        y_height = h/2
        I = b * h**3/12 

        L   = 0.530  # [m] ruler length
        l1  = 0.030  # [m] distance from the beam top to the top accelerometer
        l2  = 0.0675 # [m] distance between the tip and the middle accelerometers
        l3  = 0.070 # [m] distance between the supports
        l4 = 0.128925

        nodes = np.array([[8,0.0,L        ,0.0], # tip mass
                        [7,0.0,L-l1     ,0.0], # acc 1
                        [6,0.0,L-l1-1*l2,0.0], # acc 3
                        [5,0.0,L-l1-2*l2,0.0], # acc 2
                        [4,0.0,L-l1-3*l2,0.0], # acc 4
                        [3,0.0,l4        ,0.0], # support 2
                        [2,0.0,l4-l3     ,0.0], # support 1
                        [1,0.0,0.0      ,0.0],
                        ])

        s = myModel.my_elements[5].s_phi.shape[0]
        N = d_m.shape[1]
        stress_beam = np.zeros((7,s,N)) # s x m
        strain_beam = np.zeros((7,s,N)) # s x m
        moment_beam = np.zeros((7,s,N)) # s x m
        for beam_element in [0,1,2,3,4,5,6]:
            moment_beam[beam_element,:] = (myModel.my_elements[beam_element+3].s_phi @ d_m) # [Nm]
            stress_beam[beam_element,:] = (myModel.my_elements[beam_element+3].s_phi @ d_m) * -y_height / I / 10**6 # [MPa]
            strain_beam[beam_element,:] = (myModel.my_elements[beam_element+3].e_phi @ d_m)
    
        #converged_moment.append(np.mean(moment_beam[2,1,:]))
        converged_moment.append(moment_beam[2,1,4998])
    
    fig, (ax1) = plt.subplots(1,1,figsize=(8, 6), tight_layout=True)
    ax1.plot(np.array(modes)+1,converged_moment,"-o")
    ax1.set_ylabel("Moment [Nm]")
    ax1.set_xlabel("Modes")
    ax1.set_title("Converged moment, freq-based integration")
    ax1.set_xlim([0,20])
    ax1.set_xticks(list(range(21)))
    ax1.grid()
    print("Omega 17 modes",omega)













    # # Find non-measured DOF
    # model_pars['modes'] = [1]
    # print("modes",model_pars['modes'])
    # _, _, Phi_selected, myModel, _ = beam_new.eval_yafem_model(model_pars)
    # # non_measured_loc, id_no_sensors, id_sensors = find_unique_dofs(model_pars['dofs_sel'],params['sensor_loc'])
    
    
    # # Phi_alpha_S = Phi_selected[id_sensors,:] #Mode shapes of the measuremed locations
    # # Phi_beta_S = Phi_selected[id_no_sensors,:] #Mode shapes of the unmeasuremed locations

    # # # Estimate displacements
    # # d_alpha = Disp[:,:]
    # # q_hat = np.linalg.pinv(Phi_alpha_S) @ d_alpha #Find modal coordinates of measured points
    # # d_beta = Phi_beta_S @ q_hat
    # # d_hat = np.zeros((myModel.ndof,N)) # np.zeros((unconstrained_model_loc.shape[0],y.shape[1]))
    # # for id, loc in enumerate([id_sensors]):
    # #         d_hat[loc,:] = d_alpha[id,:]
    # # for id, loc in enumerate(id_no_sensors):
    # #         d_hat[loc,:] = d_beta[id,:]


    

    # h = 1e-3
    # b = 29e-3
    # y_height = h/2
    # I = b * h**3/12 

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

    # s = myModel.my_elements[5].s_phi.shape[0]
    # N = d_m.shape[1]
    # stress_beam = np.zeros((7,s,N)) # s x m
    # strain_beam = np.zeros((7,s,N)) # s x m
    # moment_beam = np.zeros((7,s,N)) # s x m
    # for beam_element in [0,1,2,3,4,5,6]:
    #     moment_beam[beam_element,:] = (myModel.my_elements[beam_element+3].s_phi @ d_m) # [Nm]
    #     stress_beam[beam_element,:] = (myModel.my_elements[beam_element+3].s_phi @ d_m) * -y_height / I / 10**6 # [MPa]
    #     strain_beam[beam_element,:] = (myModel.my_elements[beam_element+3].e_phi @ d_m)

    # print("Moment [Nm] and Stress [MPa]")
    # print(moment_beam[6,1,-1],moment_beam[6,2,-1],stress_beam[6,1,-1],stress_beam[6,2,-1])
    # print(moment_beam[5,1,-1],moment_beam[5,2,-1],stress_beam[5,1,-1],stress_beam[5,2,-1])
    # print(moment_beam[4,1,-1],moment_beam[4,2,-1],stress_beam[4,1,-1],stress_beam[4,2,-1])
    # print(moment_beam[3,1,-1],moment_beam[3,2,-1],stress_beam[3,1,-1],stress_beam[3,2,-1])
    # print(moment_beam[2,1,-1],moment_beam[2,2,-1],stress_beam[2,1,-1],stress_beam[2,2,-1])
    # print(moment_beam[1,1,-1],moment_beam[1,2,-1],stress_beam[1,1,-1],stress_beam[1,2,-1])
    # print(moment_beam[0,1,-1],moment_beam[0,2,-1],stress_beam[0,1,-1],stress_beam[0,2,-1])

    # P = 1
    # nodes_height = np.flip(nodes[:,2])
    # #Analytical
    # L2 = L-nodes_height
    # print("L",L2)
    # M = []
    # S = []
    # for l in L2:
    #     M.append(-P*l)
    #     S.append(P*l*y_height/I / 10**6)

    # plot_list = stress_beam[:,1,-1]
    # plot_list = np.append(plot_list,stress_beam[6,2,-1])
    # fig, (ax1, ax2) = plt.subplots(1,2,figsize=(16, 6), tight_layout=True)
    # ax1.plot(np.zeros(8),nodes[:,2]*1000,'-o',color="k")
    # ax1.plot(np.flip(plot_list),nodes[:,2]*1000,'o',label="Estimate")
    # ax1.fill_betweenx(nodes[:,2]*1000,np.flip(plot_list),alpha=0.4)
    # #ax1.plot(np.flip(S),nodes[:,2]*1000,'o-',label="Analytical")
    # ax1.set_xlabel("Stress [MPa]")
    # ax1.grid()
    # ax1.legend()
    # for i, txt in enumerate([1,2,3,4,5,6,7,8]):
    #     ax1.annotate("Node "+str(txt), (0, nodes_height[i]*1000))

    # plot_list = moment_beam[:,1,-1]
    # plot_list = np.append(plot_list,moment_beam[6,2,-1])
    # ax2.plot(np.zeros(8),nodes[:,2]*1000,'-o',color="k")
    # ax2.plot(np.flip(plot_list),nodes[:,2]*1000,'o',label="Estimate")
    # ax2.fill_betweenx(nodes[:,2]*1000,np.flip(plot_list),alpha=0.4)
    # #ax2.plot(np.flip(M),nodes[:,2]*1000,'o-',label="Analytical")
    # ax2.set_xlabel("Bending [Nm]")
    # ax2.grid()
    # ax2.legend()
    # ax1.set_title("Mode 1")
    # for i, txt in enumerate([1,2,3,4,5,6,7,8]):
    #     ax2.annotate("Node "+str(txt), (0, nodes_height[i]*1000))

    # plt.show(block=False)


    # # Find non-measured DOF
    # model_pars['modes'] = [1,2]
    # print("modes",model_pars['modes'])
    # _, _, Phi_selected, myModel, _ = beam_new.eval_yafem_model(model_pars)



    

    # h = 1e-3
    # b = 29e-3
    # y_height = h/2
    # I = b * h**3/12 

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

    # s = myModel.my_elements[5].s_phi.shape[0]
    # N = d_m.shape[1]
    # stress_beam = np.zeros((7,s,N)) # s x m
    # strain_beam = np.zeros((7,s,N)) # s x m
    # moment_beam = np.zeros((7,s,N)) # s x m
    # for beam_element in [0,1,2,3,4,5,6]:
    #     moment_beam[beam_element,:] = (myModel.my_elements[beam_element+3].s_phi @ d_m) # [Nm]
    #     stress_beam[beam_element,:] = (myModel.my_elements[beam_element+3].s_phi @ d_m) * -y_height / I / 10**6 # [MPa]
    #     strain_beam[beam_element,:] = (myModel.my_elements[beam_element+3].e_phi @ d_m)

    # print("Moment [Nm] and Stress [MPa]")
    # print(moment_beam[6,1,-1],moment_beam[6,2,-1],stress_beam[6,1,-1],stress_beam[6,2,-1])
    # print(moment_beam[5,1,-1],moment_beam[5,2,-1],stress_beam[5,1,-1],stress_beam[5,2,-1])
    # print(moment_beam[4,1,-1],moment_beam[4,2,-1],stress_beam[4,1,-1],stress_beam[4,2,-1])
    # print(moment_beam[3,1,-1],moment_beam[3,2,-1],stress_beam[3,1,-1],stress_beam[3,2,-1])
    # print(moment_beam[2,1,-1],moment_beam[2,2,-1],stress_beam[2,1,-1],stress_beam[2,2,-1])
    # print(moment_beam[1,1,-1],moment_beam[1,2,-1],stress_beam[1,1,-1],stress_beam[1,2,-1])
    # print(moment_beam[0,1,-1],moment_beam[0,2,-1],stress_beam[0,1,-1],stress_beam[0,2,-1])

    # P = 1
    # nodes_height = np.flip(nodes[:,2])
    # #Analytical
    # L2 = L-nodes_height
    # print("L",L2)
    # M = []
    # S = []
    # for l in L2:
    #     M.append(-P*l)
    #     S.append(P*l*y_height/I / 10**6)

    # plot_list = stress_beam[:,1,-1]
    # plot_list = np.append(plot_list,stress_beam[6,2,-1])
    # fig, (ax1, ax2) = plt.subplots(1,2,figsize=(16, 6), tight_layout=True)
    # ax1.plot(np.zeros(8),nodes[:,2]*1000,'-o',color="k")
    # ax1.plot(np.flip(plot_list),nodes[:,2]*1000,'o',label="Estimate")
    # ax1.fill_betweenx(nodes[:,2]*1000,np.flip(plot_list),alpha=0.4)
    # #ax1.plot(np.flip(S),nodes[:,2]*1000,'o-',label="Analytical")
    # ax1.set_xlabel("Stress [MPa]")
    # ax1.grid()
    # ax1.legend()
    # ax1.set_title("Mode 1+2")
    # for i, txt in enumerate([1,2,3,4,5,6,7,8]):
    #     ax1.annotate("Node "+str(txt), (0, nodes_height[i]*1000))

    # plot_list = moment_beam[:,1,-1]
    # plot_list = np.append(plot_list,moment_beam[6,2,-1])
    # ax2.plot(np.zeros(8),nodes[:,2]*1000,'-o',color="k")
    # ax2.plot(np.flip(plot_list),nodes[:,2]*1000,'o',label="Estimate")
    # ax2.fill_betweenx(nodes[:,2]*1000,np.flip(plot_list),alpha=0.4)
    # #ax2.plot(np.flip(M),nodes[:,2]*1000,'o-',label="Analytical")
    # ax2.set_xlabel("Bending [Nm]")
    # ax2.grid()
    # ax2.legend()
    # for i, txt in enumerate([1,2,3,4,5,6,7,8]):
    #     ax2.annotate("Node "+str(txt), (0, nodes_height[i]*1000))

    # plt.show(block=False)


    # # Find non-measured DOF
    # model_pars['modes'] = [1,2,3]
    # print("modes",model_pars['modes'])
    # _, _, Phi_selected, myModel, _ = beam_new.eval_yafem_model(model_pars)
    

    # h = 1e-3
    # b = 29e-3
    # y_height = h/2
    # I = b * h**3/12 

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

    # s = myModel.my_elements[5].s_phi.shape[0]
    # N = d_m.shape[1]
    # stress_beam = np.zeros((7,s,N)) # s x m
    # strain_beam = np.zeros((7,s,N)) # s x m
    # moment_beam = np.zeros((7,s,N)) # s x m
    # for beam_element in [0,1,2,3,4,5,6]:
    #     moment_beam[beam_element,:] = (myModel.my_elements[beam_element+3].s_phi @ d_m) # [Nm]
    #     stress_beam[beam_element,:] = (myModel.my_elements[beam_element+3].s_phi @ d_m) * -y_height / I / 10**6 # [MPa]
    #     strain_beam[beam_element,:] = (myModel.my_elements[beam_element+3].e_phi @ d_m)

    # print("Moment [Nm] and Stress [MPa]")
    # print(moment_beam[6,1,-1],moment_beam[6,2,-1],stress_beam[6,1,-1],stress_beam[6,2,-1])
    # print(moment_beam[5,1,-1],moment_beam[5,2,-1],stress_beam[5,1,-1],stress_beam[5,2,-1])
    # print(moment_beam[4,1,-1],moment_beam[4,2,-1],stress_beam[4,1,-1],stress_beam[4,2,-1])
    # print(moment_beam[3,1,-1],moment_beam[3,2,-1],stress_beam[3,1,-1],stress_beam[3,2,-1])
    # print(moment_beam[2,1,-1],moment_beam[2,2,-1],stress_beam[2,1,-1],stress_beam[2,2,-1])
    # print(moment_beam[1,1,-1],moment_beam[1,2,-1],stress_beam[1,1,-1],stress_beam[1,2,-1])
    # print(moment_beam[0,1,-1],moment_beam[0,2,-1],stress_beam[0,1,-1],stress_beam[0,2,-1])

    # P = 1
    # nodes_height = np.flip(nodes[:,2])
    # #Analytical
    # L2 = L-nodes_height
    # print("L",L2)
    # M = []
    # S = []
    # for l in L2:
    #     M.append(-P*l)
    #     S.append(P*l*y_height/I / 10**6)

    # plot_list = stress_beam[:,1,-1]
    # plot_list = np.append(plot_list,stress_beam[6,2,-1])
    # fig, (ax1, ax2) = plt.subplots(1,2,figsize=(16, 6), tight_layout=True)
    # ax1.plot(np.zeros(8),nodes[:,2]*1000,'-o',color="k")
    # ax1.plot(np.flip(plot_list),nodes[:,2]*1000,'o',label="Estimate")
    # ax1.fill_betweenx(nodes[:,2]*1000,np.flip(plot_list),alpha=0.4)
    # #ax1.plot(np.flip(S),nodes[:,2]*1000,'o-',label="Analytical")
    # ax1.set_xlabel("Stress [MPa]")
    # ax1.grid()
    # ax1.legend()
    # ax1.set_title("Mode 1+2+3")
    # for i, txt in enumerate([1,2,3,4,5,6,7,8]):
    #     ax1.annotate("Node "+str(txt), (0, nodes_height[i]*1000))

    # plot_list = moment_beam[:,1,-1]
    # plot_list = np.append(plot_list,moment_beam[6,2,-1])
    # ax2.plot(np.zeros(8),nodes[:,2]*1000,'-o',color="k")
    # ax2.plot(np.flip(plot_list),nodes[:,2]*1000,'o',label="Estimate")
    # ax2.fill_betweenx(nodes[:,2]*1000,np.flip(plot_list),alpha=0.4)
    # #ax2.plot(np.flip(M),nodes[:,2]*1000,'o-',label="Analytical")
    # ax2.set_xlabel("Bending [Nm]")
    # ax2.grid()
    # ax2.legend()
    # for i, txt in enumerate([1,2,3,4,5,6,7,8]):
    #     ax2.annotate("Node "+str(txt), (0, nodes_height[i]*1000))

    plt.show(block=True)

    quit()


    # if plot == True:
    #     nodes_height = np.flip(nodes[:,2])
    #     t = np.linspace(0, N / params['Fs'], N)
    #     for beam_element, _ in enumerate(stress_beam[:,0]):
    #         label_str1 = "Ele." + str(beam_element+1) + "node:" + str(beam_element+1)
    #         label_str2 = "Ele." + str(beam_element+1) + "node:" + str(beam_element+2)
    #         plt.plot(t,stress_beam[beam_element,1]+nodes_height[beam_element]*1000,label=label_str1)
    #         plt.plot(t,stress_beam[beam_element,2]+nodes_height[beam_element+1]*1000,label=label_str2)
    #     for i, txt in enumerate([1,2,3,4,5,6,7,8]):
    #         plt.annotate("Node "+str(txt), (0, nodes_height[i]*1000))
    #     plt.legend()
    #     plt.show(block=True)
    #     sys.stdout.flush()

    # nodes_height = np.flip(nodes[:,2])
    # plt.plot(stress_beam[:,1,-1],nodes[1:,2]*1000)
    # for i, txt in enumerate([1,2,3,4,5,6,7,8]):
    #     plt.annotate("Node "+str(txt), (0, nodes_height[i]*1000))
    # plt.show(block=True)

    #print("moment",moment_beam[2,1,-1],moment_beam[2,2,-1],moment_beam[3,1,-1],moment_beam[3,2,-1],moment_beam[4,1,-1],moment_beam[4,2,-1],moment_beam[5,1,-1],moment_beam[5,2,-1],moment_beam[6,1,-1],moment_beam[6,2,-1])
    return d_hat, stress_beam, strain_beam, moment_beam, expansion_validation


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