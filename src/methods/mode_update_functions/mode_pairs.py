"This file is taken from the DTaaS-platform"
import numpy as np

def MAC_calculate(mode1, mode2):
    """
    Parameters:
        mode1 (numpy array): Complex-valued mode shape vector.
        mode2 (numpy array): Complex-valued mode shape vector.

    Returns:
        float: MAC value (between 0 and 1).
     
    """
    numerator = np.abs(np.dot(mode1.conj().T, mode2)) ** 2  
    denominator = np.dot(mode1.conj().T, mode1) * np.dot(mode2.conj().T, mode2)
    
    return np.real(numerator / denominator)  

def pair_calculate(omegaM, PhiM, cleaned_clusters, median_frequencies):
    """
    Parameters
    ----------
    omegaM : numpy array
        Model frequencies in Hz
    PhiM : numpy array
        Model mode shape 
    cleaned_clusters : list of dictionaries
        Results obtained from mode tracking
    median_frequencies : numpy array
        Median frequencies of clusters obtained from mode track results

    Returns
    -------
    paired_frequencies : numpy array
        The SysID frequencies corresponding to paired modes
    paired_mode_shapes : numpy array
        The SysID mode shapes corresponding to paired modes
    omegaM : numpy array
        The model frequencies corresponding to paired modes
    PhiM : TYPE
        The model modes shapes corresponding to paired modes
        
    SM: 21/03/2025

    """

    # Mode pairing strategy for more than 3 sensors configuration
    # Calculate beta (highest MAC based pairing) and tau (average MAC based pairing)
    mode_count = PhiM.shape[1]  # Number of modes in PhiM
    # print(f'mode count: {mode_count}')
    # Initialize matrices to store MAC values
    highest_mac = np.zeros((mode_count, len(cleaned_clusters)))  # Highest MAC for each mode across all dictionaries
    average_mac = np.zeros((mode_count, len(cleaned_clusters)))  # Average MAC for each mode across all dictionaries
    
    highest_mac_dict_idx = np.zeros(mode_count, dtype=int)  # Dictionary index with highest MAC for each mode
    average_mac_dict_idx = np.zeros(mode_count, dtype=int)  # Dictionary index with best average MAC for each mode
    
    # Loop through each mode of PhiM
    for i in range(mode_count):
        best_avg_mac = -1  # Track the best average MAC
        best_avg_mac_idx = -1  # Track the dictionary index for best average MAC
    
        for j, cluster in enumerate(cleaned_clusters):
            mode_shape = cluster['mode_shapes']  # Mode shapes in current dictionary
    
           # Track the highest MAC for current mode of PhiM
            max_mac_for_mode = -1  # Track the highest MAC for this mode
            mac_per_mode = []
            
            for k in range(mode_shape.shape[0]):
                current_mac = MAC_calculate(mode_shape[k, :].T, PhiM[:,i])
                highest_mac[i, j] = max(highest_mac[i, j], current_mac)
                mac_per_mode.append(current_mac)
    
                if current_mac > max_mac_for_mode:
                    max_mac_for_mode = current_mac
    
            # Track the dictionary with the highest MAC for the current mode
            if highest_mac[i, j] == max_mac_for_mode:
                highest_mac_dict_idx[i] = j                     # paremeter beta
    
            # Calculate the average MAC for the current mode in the current dictionary
            avg_mac = np.mean(mac_per_mode)  # Calculate the average MAC inside the dictionary
            average_mac[i, j] = avg_mac  # Store the average MAC for the current mode in the current dictionary
    
            # Track the dictionary with the best average MAC for the current mode
            if avg_mac > best_avg_mac:
                best_avg_mac = avg_mac
                best_avg_mac_idx = j
    
        # Track the dictionary with the best average MAC for the current mode
        average_mac_dict_idx[i] = best_avg_mac_idx
    
    # # Display the results
    # print("Highest MAC for each mode of PhiM (across all dictionaries):")
    # print(highest_mac)
    
    # print("\nAverage MAC for each mode of PhiM (across all dictionaries):")
    # print(average_mac)
    
    # Mode pairing start for 2 sensors configuration
    MAC_THRESHOLD = 0.75
    
    # Initialize arrays to store final paired frequencies and mode shapes
    paired_frequencies = np.full(mode_count, np.nan)  # Use np.nan instead of zeros
    paired_mode_shapes = np.full((PhiM.shape[0], mode_count), np.nan, dtype=np.complex128)
    
    # Keep track of used clusters
    used_clusters = set()
    
    # Step 1: Frequency-based pairing (alfa)
    alfa = {np.argmin(np.abs(omegaM - a)): i for i, a in enumerate(median_frequencies)}
    # print(f'alfa pairing: {alfa}')
    
    # Step 2: Loop through each mode of PhiM
    for i in range(mode_count):
        # First try frequency-based pairing (alfa)
        if i in alfa:
            candidate_cluster_idx = alfa[i]
            # print(f'alfa : {alfa[i]}')
            if candidate_cluster_idx not in used_clusters:
                selected_cluster = cleaned_clusters[candidate_cluster_idx]
                mode_shapes = selected_cluster['mode_shapes']
                
                # Find the mode shape with the highest MAC for the current mode
                mac_values = np.array([MAC_calculate(mode_shapes[k, :].T, PhiM[:, i]) for k in range(mode_shapes.shape[0])])
                # print(f'PhiM for MAC: {PhiM[:,i]}')
                # print(f'Mode track mode shape: {[mode_shapes[k,:].T for k in range(mode_shapes.shape[0])]}')
                # print(f'MAC values alfa: {mac_values}')
                best_shape_idx = np.argmax(mac_values)
                # print(f'alfa: {alfa}')
                best_mac = mac_values[best_shape_idx]
                # print(f'best mac: {best_mac}')
    
                # Pair only if MAC exceeds the threshold
                if best_mac >= MAC_THRESHOLD:
                    paired_frequencies[i] = selected_cluster['median']
                    # print(f'MAC loop paired frequencies: {paired_frequencies}')
                    # print(f'MAC based mode shape: {mode_shape[best_shape_idx,:]}')
                    paired_mode_shapes[:, i] = mode_shapes[best_shape_idx, :]
                    # print(f'MAC based paired mode shape: {paired_mode_shapes[:,i]}')
                    used_clusters.add(candidate_cluster_idx)
                    # print(f'Used clusters: {used_clusters}')
    
        # Step 3: If frequency-based pairing fails, fallback to MAC-based pairing (beta)
        if np.isnan(paired_frequencies[i]):
            best_mac = -1
            best_dict_idx = -1
            best_shape_idx = -1
    
            for idx, cluster in enumerate(cleaned_clusters):
                if idx in used_clusters:
                    continue
    
                mode_shapes = cluster['mode_shapes']
                mac_values = np.array([MAC_calculate(mode_shapes[k, :].T, PhiM[:, i]) for k in range(mode_shapes.shape[0])])
                # print(f'MAC values beta: {mac_values}')
                max_mac_idx = np.argmax(mac_values)
                max_mac = mac_values[max_mac_idx]
    
                if max_mac > best_mac:
                    best_mac = max_mac
                    best_dict_idx = idx
                    best_shape_idx = max_mac_idx
    
            # Pair only if MAC exceeds the threshold
            if best_dict_idx != -1 and best_mac >= MAC_THRESHOLD:
                paired_frequencies[i] = cleaned_clusters[best_dict_idx]['median']
                paired_mode_shapes[:, i] = cleaned_clusters[best_dict_idx]['mode_shapes'][best_shape_idx, :]
                used_clusters.add(best_dict_idx)
    
    # Remove unpaired entries for further calculations
    valid_pairs = ~np.isnan(paired_frequencies)
    # print(f'valid pairs before: {valid_pairs}')
    
    # Ensure to number of paired modes are consistent
    min_length = min(len(paired_frequencies), len(valid_pairs))
    # print(f'min length: {min_length}')
    # Trim both arrays to the minimum length
    paired_frequencies = paired_frequencies[:min_length]
    # print(f'paired frequencies: {paired_frequencies}')
    omegaM = omegaM[:min_length]
    valid_pairs = valid_pairs[:min_length]
    # print(f'valid pairs after: {valid_pairs}')  
    PhiM = PhiM[:, :min_length]
    # print(f'PhiM shape: {np.shape(PhiM)}')
    
    # Apply valid pairs (filter paired_frequencies)
    paired_frequencies = paired_frequencies[valid_pairs]  
    paired_mode_shapes = paired_mode_shapes[:, valid_pairs]
    omegaM = omegaM[valid_pairs]
    PhiM = PhiM[:, valid_pairs]
    
    return paired_frequencies, paired_mode_shapes, omegaM, PhiM
