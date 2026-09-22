from typing import Any, Dict
import numpy as np
from functions import fun_cantilever_beam_new as beam_new

def MAC_calculate(mode1: np.ndarray[np.complex64], mode2: np.ndarray[np.complex64]) -> float:
    """
    Args:
        mode1 (np.ndarray[np.complex64]): Complex-valued mode shape vector.
        mode2 (np.ndarray[np.complex64]): Complex-valued mode shape vector.

    Returns:
        [float]: MAC value (between 0 and 1).
     
    """
    numerator = np.abs(np.dot(mode1.conj().T, mode2)) ** 2  
    denominator = np.dot(mode1.conj().T, mode1) * np.dot(mode2.conj().T, mode2)
    
    return np.real(numerator / denominator)  

def pair_calculate(model_freq: np.ndarray[float], model_mode_shapes: np.ndarray[float], cluster_dict: Dict[str,Any], Params):
    """
    Args:
    model_freq (np.ndarray[float]): Model frequencies in Hz
    model_mode_shapes (np.ndarray[float]): Model mode shape 
    cluster_dict (Dict[str,Any]): Dictionary of clusters
    Params: Update parameters

    Returns:
    paired_c_freq (): Paired cluster median frequencies
    paired_c_mode_shapes (): Paired cluster mode shapes
    paired_model_freq (): Paired model median frequencies
    paried_model_mode_shapes (): Paired model mode shapes
    
    JVM: 03/11/2025

    """

    sensors = model_mode_shapes.shape[0]
    
    # Calculate beta (highest MAC based pairing) and tau (average MAC based pairing)
    mode_count = model_mode_shapes.shape[1]  # Number of modes in PhiM

    # Initialize matrices to store MAC values
    highest_MAC = np.zeros((len(cluster_dict),mode_count))  # Highest MAC for each mode across all dictionaries
    average_MAC = np.zeros((len(cluster_dict),mode_count))  # Average MAC for each mode across all dictionaries
    
    highest_MAC_dict_idx = np.zeros(len(cluster_dict), dtype=int)  # Dictionary index with highest MAC for each mode
    average_MAC_dict_idx = np.zeros(len(cluster_dict), dtype=int)  # Dictionary index with best average MAC for each mode
    
    # Loop through each mode of PhiM
    median_frequencies = []
    closest_freq_id = []
    for i, key in enumerate(cluster_dict):
        best_avg_mac = -1

        cluster = cluster_dict[key]
        mode_shape = cluster['mode_shapes']  # Mode shapes in current dictionary
        m_f = cluster['median_f']
        median_frequencies.append(m_f)
        # Step 1: Frequency-based pairing (alfa)
        closest_freq_id.append(int(np.argmin(np.abs(model_freq - m_f))))

        for j in range(mode_count):
            if model_freq[j] < 2*m_f:
            # Track the highest MAC for current mode of PhiM
                max_mac_for_mode = -1  # Track the highest MAC for this mode
                mac_per_mode = []
                for k in range(mode_shape.shape[0]):
                    current_MAC = MAC_calculate(mode_shape[k, :].T, model_mode_shapes[:,j])
                    highest_MAC[i, j] = max(highest_MAC[i, j], current_MAC)
                    mac_per_mode.append(current_MAC)
        
                    if current_MAC > max_mac_for_mode:
                        max_mac_for_mode = current_MAC
        
                # Track the dictionary with the highest MAC for the current mode
                if highest_MAC[i, j] == max_mac_for_mode:
                    highest_MAC_dict_idx[i] = j                     # paremeter beta
        
                # Calculate the average MAC for the current mode in the current dictionary
                avg_mac = np.mean(mac_per_mode)  # Calculate the average MAC inside the dictionary
                average_MAC[i, j] = avg_mac  # Store the average MAC for the current mode in the current dictionary
                
                # Track the dictionary with the best average MAC for the current mode
                if avg_mac > best_avg_mac:
                    best_avg_mac = avg_mac
                    best_avg_mac_idx = j
    
        # Track the dictionary with the best average MAC for the current mode
        average_MAC_dict_idx[i] = best_avg_mac_idx

    MAC_THRESHOLD = Params['tMAC_MU']
    paired_c_freq = []
    paired_c_mode_shapes = np.zeros((sensors,1))
    paired_model_freq = []
    paried_model_mode_shapes = np.zeros((1,sensors))
    MAC_max_list = []
    Dm_f_list = []
    id_model_list = []
    for ii, key in enumerate(cluster_dict): #Iterate over all clusters
        cluster = cluster_dict[key]

        # Find the id in the MAC array with higest max and average.
        id_high_MAC = np.argmax(highest_MAC[ii,:])
        id_avg_MAC = np.argmax(average_MAC[ii,:])
        id_freq = closest_freq_id[ii] #The id of the best frequency match

        id_model = []
        if max(average_MAC[ii,:]) > MAC_THRESHOLD: #If the MAC value is above the threshold
            if (id_high_MAC == id_avg_MAC) or (id_avg_MAC == id_freq) or (id_high_MAC == id_freq): #At least two are similar id must be present across the three different parameters, max(MAC), avg(MAC) and min(D_freq)
                id_model = int(id_high_MAC) #What is the model id, what is a match/pair

                if id_high_MAC in id_model_list: #If a pairing is already made, then check what is best.
                    indices = int(np.argwhere(id_model_list == id_high_MAC))
                    
                    for id, ms in enumerate(cluster_dict[key]['mode_shapes']): #Iterate over all mode shapes
                        MAC = MAC_calculate(ms.T, model_mode_shapes[:,id_model]) #Calculate MAC
                        if MAC > MAC_max: #Find the max MAC for the possible other pairing
                            MAC_max = MAC
                            MAC_max_id = id
                    
                    MAC_previous = MAC_max_list[indices] #Previous MAC pairing
                    Dm_f_list_previous = Dm_f_list[indices] #Previous pairing difference in frequency 

                    Dm_f = model_freq[id_model] - cluster_dict[key]['median_f'] #The new frequency differences for the new possible pairing.
                    
                    if (MAC_max > MAC_previous) and (Dm_f_list_previous > Dm_f): #If the new pairing is better in terms of both MAC and frequency.
                        # print("Replace prevoius pairing")
                        replace_id = indices
                        id_model_list[replace_id] = id_model

                        paired_c_freq[replace_id] = cluster_dict[key]['median_f']
                        paired_model_freq[replace_id] = model_freq[id_model]

                        Dm_f_list[replace_id] = Dm_f
                        MAC_max_list[replace_id] = MAC_max
                        paried_model_mode_shapes[:,replace_id] = model_mode_shapes[:,id_model]
                        paired_c_mode_shapes[:,replace_id] = cluster_dict[key]['mode_shapes'][MAC_max_id,:]


                else: #If this is a new pairing
                    #Add information to paring
                    id_model_list.append(id_model)
                    paired_c_freq.append(cluster_dict[key]['median_f'])
                    paired_model_freq.append(model_freq[id_model])

                    Dm_f_list.append(model_freq[id_model]-cluster_dict[key]['median_f'])

                    #Mode shape of paried model mode
                    if np.sum(paried_model_mode_shapes) == 0: #If no paried mode shapes have been done before
                        paried_model_mode_shapes = model_mode_shapes[:,id_model].reshape(sensors,1)
                    else:
                        paried_model_mode_shapes = np.append(paried_model_mode_shapes,model_mode_shapes[:,id_model].reshape(sensors,1),axis=1)
                    
                    MAC_max = -1 #Insert the MAC value into the paring information
                    for id, ms in enumerate(cluster_dict[key]['mode_shapes']):
                        MAC = MAC_calculate(ms.T, model_mode_shapes[:,id_model])
                        if MAC > MAC_max:
                            MAC_max = MAC
                            MAC_max_id = id
                    MAC_max_list.append(MAC_max)
                    #Mode shape of paried cluster
                    if np.sum(paired_c_mode_shapes) == 0:#If no paried mode shapes have been done before
                        paired_c_mode_shapes = cluster_dict[key]['mode_shapes'][MAC_max_id,:].reshape(sensors,1)
                    else:
                        paired_c_mode_shapes = np.append(paired_c_mode_shapes,cluster_dict[key]['mode_shapes'][MAC_max_id,:].reshape(sensors,1),axis=1)

            else:
                print("Cluster",key,cluster['median_f'],"is not matched. Reason: similar match id criteria")
                pass
        else:
            print("Cluster",key,cluster['median_f'],"is not matched. Reason: MAC threshold")
            pass



    paired_c_freq = np.array(paired_c_freq)
    paired_model_freq = np.array(paired_model_freq)

    return paired_c_freq, paired_c_mode_shapes, paired_model_freq, paried_model_mode_shapes


def par_est(theta_star: np.ndarray[float], cluster_dict: Dict[str,Any], model_parameters: Dict[str,Any],parameters_to_update: np.ndarray[str],Params: Dict[str,Any]) -> float:
    """
    Estimate updated parameters adn return the objective function result

    Args:
        theta_star (np.ndarray[float]): The parameters to update
        cluster_dict (Dict[str,Any]): Dictionary of clustered modes
        model_parameters Dict[str,Any]: Model parameters (YaFEM)
        parameters_to_update np.ndarray[str]: String of keys to update in model_parameters
        Params Dict[str,Any]: Update parameters

    Returns:
        X (float): Resulting value from objective function

    Raises:
    ValueError:
        The number of updating parameters more than than the number of features. 
        One should re-try after reducing the number of updating parameters 

    """ 
    
    id = 0
    for key in model_parameters:
        if str(key) in parameters_to_update:
            model_parameters[key] = theta_star[id]
            id += 1
    # Call FE solver to get model frequencies and mode shapes
    omegaM, phi, PhiM, myModel, _ = beam_new.eval_yafem_model(model_parameters)
    
    # Mode Pairing Start
    paired_frequencies, paired_mode_shapes, omegaM, PhiM = pair_calculate(omegaM, PhiM, cluster_dict, Params)
    omegaM = omegaM.reshape(paired_frequencies.shape)

    
    # Error message if the number of updating parameters is more than double of the paired frequencies
    if len(theta_star) > 2 * len(paired_frequencies):
        raise ValueError("The problem becomes undetermined. The number of updated parameters should not be more than the number of features")
    
    # Compute MAC
    MACn = np.abs(np.diag(np.conj(paired_mode_shapes).T @ PhiM))**2
    MACd = np.diag(np.conj(paired_mode_shapes).T @ paired_mode_shapes) * np.diag(np.conj(PhiM).T @ PhiM)
    MAC = MACn / MACd
    
    # Objective function
    resOM = (omegaM - paired_frequencies)/omegaM
    resPhi = MAC
    X = np.dot(resOM.T, resOM) + 1 / np.dot(resPhi.T, resPhi)
    
    return np.real(X)


