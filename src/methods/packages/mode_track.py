"This file is taken from the DTaaS-platform"
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import numpy as np
import numpy.ma as ma
import copy

# plt.close('all')
# Clustering function
def cluster_frequencies(frequencies, damping_ratios, mode_shapes, 
                        frequencies_max_MO, cov_freq_max_MO, 
                        damping_ratios_max_MO, cov_damping_max_MO,
                        mode_shapes_max_MO, tMAC, bound_multiplier=2):
    """
    

    Parameters
    ----------
    frequencies : TYPE
        DESCRIPTION.
    damping_ratios : TYPE
        DESCRIPTION.
    mode_shapes : TYPE
        DESCRIPTION.
    frequencies_max_MO : TYPE
        DESCRIPTION.
    cov_freq_max_MO : TYPE
        DESCRIPTION.
    damping_ratios_max_MO : TYPE
        DESCRIPTION.
    cov_damping_max_MO : TYPE
        DESCRIPTION.
    mode_shapes_max_MO : TYPE
        DESCRIPTION.
    tMAC : TYPE
        DESCRIPTION.
    bound_multiplier : TYPE, optional
        DESCRIPTION. The default is 2.

    Returns
    -------
    None.

    """
    
    # Modify the index of frequency to sorting
    
    sorted_indices = np.argsort(frequencies_max_MO)   
    fn_sorted = frequencies_max_MO[sorted_indices]
    damping_ratios_sorted = damping_ratios_max_MO[sorted_indices]
    cov_fn_sorted = cov_freq_max_MO[sorted_indices]
    cov_damping_sorted = cov_damping_max_MO[sorted_indices]
    mode_shape_sorted = mode_shapes_max_MO[sorted_indices]
    
    fn_unique, unique_indices = np.unique(fn_sorted, return_index=True)
    cov_fn_unique = cov_fn_sorted[unique_indices]
    damping_ratios_unique = damping_ratios_sorted[unique_indices]
    cov_damping_unique = cov_damping_sorted[unique_indices] 
    mode_shape_unique = mode_shape_sorted[unique_indices]
    
    # print(f'unsorted frequencies: {frequencies_max_MO}')
    # print(f'unique frequencies: {fn_unique}')
    # print(f'unsorted covariance: {cov_freq_max_MO}')
    # print(f'unique covariance: {cov_fn_unique}')
    
    # frequencies = frequencies[::2]              # This is 'S' as per algorithm
    # mode_shapes = mode_shapes[::2, :, :]
    
    # print(f'Shape of frequencies: {frequencies.shape}')
        
    C_cluster = [] 
    Ip        = []
    
    # Mask to track ungrouped elements (initially all elements are ungrouped)
    ungrouped_mask = np.ones_like(frequencies, dtype=bool)
    
    # Check each limit and save indices
    for ip, (f_MxMO, fcov_MxMO, z_MxMO, zcov_MxMO) in enumerate(zip(fn_unique, 
                    cov_fn_unique, damping_ratios_unique, cov_damping_unique)):
        if np.isnan(f_MxMO):
                continue
        
        # Confidence interval using the mean±2*standard_deviation 
        f_lower_bound = f_MxMO - bound_multiplier * np.sqrt(fcov_MxMO)
        f_upper_bound = f_MxMO + bound_multiplier * np.sqrt(fcov_MxMO)
        z_lower_bound = z_MxMO - bound_multiplier * np.sqrt(zcov_MxMO)
        z_upper_bound = z_MxMO + bound_multiplier * np.sqrt(zcov_MxMO)
        
        # Find elements within the current limit that are still ungrouped
        condition_mask = (frequencies >= f_lower_bound) & (frequencies <= f_upper_bound) & (damping_ratios >= z_lower_bound) & (damping_ratios <= z_upper_bound) & ungrouped_mask
        indices = np.argwhere(condition_mask)  # Get indices satisfying the condition
        
        # Initialization of Ip
        Ip.append({
            "ip_index": ip,
            "confidence_interval": (f_lower_bound, f_upper_bound, z_lower_bound, z_upper_bound),
            "indices": indices,
            "f_values": frequencies[tuple(indices.T)],
            "z_values": damping_ratios[tuple(indices.T)]            
            })
        
        # for Ip_item in Ip:
        #     print(f'Ip values: {Ip_item["f_values"]}')
        
        
        # declared for appending
        updated_indices = np.empty((0, 2), dtype=int)
        f_updated_values = []
        z_updated_values = []
        # print(f'ip : {ip}')
        
        
        # Find duplicates and their indices
        # print(f'Indices : {Ip[ip]["indices"]}')
        model_order_id = Ip[ip]["indices"][:,1]
        # print(f'model order id: {model_order_id}')
        unique, counts = np.unique(model_order_id, return_counts=True)
        duplicates = unique[counts > 1]                                           # model order number with duplicate modes    
        # print(f'Duplicate : {duplicates}')
        # Create a boolean mask for duplicate rows
        is_duplicate_row = np.isin(model_order_id, duplicates)
        # Filter indices with duplicate values
        indices_Ipm = Ip[ip]["indices"][is_duplicate_row]  # Rows with duplicates
        # print(f'Ipm indices: {indices_Ipm}')
        indices_Ipu = Ip[ip]["indices"][~is_duplicate_row]
        # print(f'Ipu indices: {indices_Ipu}')
        # Check if indices_Ipu is empty
        if indices_Ipu.size > 0:
            ip_for_Ipu = indices_Ipu[np.argmax(indices_Ipu[:, 1])]
            # print(f'ip for Ipu : {ip_for_Ipu}')
        else:
            print("No unique mode issue in this step.")
        
        
        if duplicates.size == 0:
            print("All values are unique.")
            if len(indices)>1:
                
                for ii in indices:
                    target_mode_shape = mode_shapes[ii[0], ii[1], :]  # Extract mode shape from the 3D array
                    reference_mode_shape = mode_shape_unique[ip]
                    
                    # print(f'print target_mode_shape: {target_mode_shape}')
                    # print(f'print reference_mode_shape: {reference_mode_shape}')  
                    
                    # Calculate MAC with the reference mode shape
                    mac_value = calculate_mac(reference_mode_shape, target_mode_shape)
                    # print(f'MAC value: {mac_value}')
                    # print(f'ip : {ip}')
                    # print(f'MAC : {mac_value}')
                    # Check the MAC value to include in C. Algorithm 2: step 2
                    if mac_value > tMAC:
                        # print(f'updated indices: {updated_indices}')
                        # print(f'new indices to be added: {ii}')
                        updated_indices = np.vstack([updated_indices,ii])
                        f_updated_values = np.append(f_updated_values, frequencies[tuple(ii.T)])
                        z_updated_values = np.append(z_updated_values, damping_ratios[tuple(ii.T)])
                        # print(f'updated values: {updated_values}')
                        # Check if the cluster already exists
                        existing_cluster = next((c for c in C_cluster if c["ip_index"] == ip), None)
                        if existing_cluster:
                            # Update existing cluster
                            existing_cluster["indices"] = np.vstack([existing_cluster["indices"], ii])
                            existing_cluster["f_values"] = np.append(existing_cluster["f_values"], frequencies[tuple(ii.T)])
                            existing_cluster["z_values"] = np.append(existing_cluster["z_values"], damping_ratios[tuple(ii.T)])
                        else:
                            # Create a new cluster
                            C_cluster.append({
                                "ip_index": ip,
                                "confidence_interval": (f_lower_bound, f_upper_bound, z_lower_bound, z_upper_bound),
                                "indices": np.copy(updated_indices),
                                "f_values": np.copy(f_updated_values),
                                "z_values":np.copy(z_updated_values)
                            })
                                        
            else:
                 C_cluster.append({
                     "ip_index": ip,
                     "confidence_interval": (f_lower_bound,f_upper_bound, z_lower_bound, z_upper_bound),
                     "indices": indices,
                     "f_values": frequencies[tuple(indices.T)],
                     "z_values": damping_ratios[tuple(indices.T)]
                     }) 
                    
        # Handle the duplicate model order for single mode
        else:
            if len(indices_Ipu)>1:                
                for ii in indices_Ipu:
                    target_mode_shape = mode_shapes[ii[0], ii[1], :]  # Extract mode shape from the 3D array
                    reference_mode_shape = mode_shapes[ip_for_Ipu[0], ip_for_Ipu[1], :]
                    
                    # print(f'print target_mode_shape: {target_mode_shape}')
                    # print(f'print reference_mode_shape: {reference_mode_shape}')  
                    
                    # Calculate MAC with the reference mode shape
                    mac_value = calculate_mac(reference_mode_shape, target_mode_shape)
                    # print(f'MAC value: {mac_value}')
                    # print(f'ip : {ip}')
                    # print(f'MAC : {mac_value}')
                    # Check the MAC value to include in C. Algorithm 2: step 2
                    if mac_value > tMAC:
                        # print(f'updated indices: {updated_indices}')
                        # print(f'new indices to be added: {ii}')
                        updated_indices = np.vstack([updated_indices,ii])
                        f_updated_values = np.append(f_updated_values, frequencies[tuple(ii.T)])
                        z_updated_values = np.append(z_updated_values, damping_ratios[tuple(ii.T)])
                        # print(f'updated values: {updated_values}')
                        # Check if the cluster already exists
                        existing_cluster = next((c for c in C_cluster if c["ip_index"] == ip), None)
                        if existing_cluster:
                            # Update existing cluster
                            existing_cluster["indices"] = np.vstack([existing_cluster["indices"], ii])
                            existing_cluster["f_values"] = np.append(existing_cluster["f_values"], frequencies[tuple(ii.T)])
                            existing_cluster["z_values"] = np.append(existing_cluster["z_values"], damping_ratios[tuple(ii.T)])
                        else:
                            # print(f'Ipu indices: {indices_Ipu} and frequencies: {f_updated_values}')
                            # Create a new cluster
                            C_cluster.append({
                                "ip_index": ip,
                                "confidence_interval": (f_lower_bound, f_upper_bound, z_lower_bound, z_upper_bound),
                                "indices": np.copy(updated_indices),
                                "f_values": np.copy(f_updated_values),
                                "z_values":np.copy(z_updated_values)
                            })
                                        
            else:
                 C_cluster.append({
                     "ip_index": ip,
                     "confidence_interval": (f_lower_bound,f_upper_bound, z_lower_bound, z_upper_bound),
                     "indices": indices,
                     "f_values": frequencies[tuple(indices.T)],
                     "z_values": damping_ratios[tuple(indices.T)]
                     }) 
            
            
         
                
                
             
    # for Ip_item in C_cluster:
    #     print(f'C_cluster values: {Ip_item["f_values"]}')
    
     
               
    Ip_C_cluster = []  
    # algorith 2: setp 3 [condition check]
    for item1 in C_cluster:
        # print(f'C_cluster item: {item1}')
        # print(f'C_cluster value: {item1["values"]}')
        
        for item2 in Ip:
            if item1['ip_index'] != item2['ip_index']:
                continue  # Skip the comparison if ip_index is not the same
            
            if len(item1['f_values']) == len(item2['f_values']):
                # print('For C and Ip - values have the same length. Proceeding to compare the values.')
                
                # Compare the values
                if np.all(item1['f_values'] != item2['f_values']):
                    # print(f'Values are different between C_cluster and Ip: {item1["values"]} vs {item2["values"]}')
                    continue
                else:
                    print('Values are the same between C_cluster and Ip')
            
            else:
                # print('Values have different lengths between C_cluster and Ip.')
                updated_indices2 = np.empty((0, 2), dtype=int)  # Reset to empty 2D array
                f_updated_values2  = []
                z_updated_values2  = []
                for pp in item1['indices']:
                    for kk in item2['indices']:
                        reference_mode_shape = mode_shapes[pp[0], pp[1], :]
                        target_mode_shape    = mode_shapes[kk[0], kk[1], :]
                        mac_value = calculate_mac(reference_mode_shape, target_mode_shape)
                        if mac_value > tMAC:
                            updated_indices2 = np.vstack([updated_indices2,kk])
                            f_updated_values2  = np.append(f_updated_values2, frequencies[tuple(kk.T)])
                            z_updated_values2  = np.append(z_updated_values2, damping_ratios[tuple(kk.T)])
                            # print(f'newly added indices: {kk}')
                            # print(f'newly added values: {frequencies[tuple(kk.T)]}')
                            Ip_C_cluster.append({ 
                                "ip_index": item1['ip_index'],
                                "indices" : updated_indices2,
                                "f_values"  : f_updated_values2,
                                "z_values" : z_updated_values2
                                })
                        
    # for Ip_item in Ip_C_cluster:
    #     print(f'Ip_C_cluster values: {Ip_item["f_values"]}')
    #     print(f'Ip_C_cluster indices: {Ip_item["indices"]}')
                                                  
    # Initialize C_cluster_finale as a deep copy of C_cluster
    C_cluster_finale = copy.deepcopy(C_cluster)
    
    # Add the points from Ip_C_cluster if they satisfy MAC conditions
    # algorith 2: setp 3 [addition of point]
    for item1 in C_cluster:
        for item2 in Ip_C_cluster:
            if item1['ip_index'] != item2['ip_index']:
                continue  # Skip the comparison if ip_index is not the same
            
            # Combine values from both clusters
            f_merged_values = np.concatenate((item1['f_values'], item2['f_values']))
            z_merged_values = np.concatenate((item1['z_values'], item2['z_values']))
            # Combine indices from both clusters
            merged_indices = np.concatenate((item1['indices'], item2['indices']))
            
            # Find the corresponding cluster in C_cluster_finale
            for finale_item in C_cluster_finale:
                if finale_item['ip_index'] == item1['ip_index']:
                    # Update values and indices
                    finale_item['f_values'] = f_merged_values
                    finale_item['z_values'] = z_merged_values
                    finale_item['indices'] = merged_indices
                    break  # Exit the loop once the match is found     

                               
    # for C_item in C_cluster_finale:
    #     print(f'C_cluster values end: {C_item["values"]}')
    
    # algorith 2: step 4
    Ip_indices = np.vstack([item['indices'] for item in C_cluster])
    # Make a copy of frequencies to represent unclustered frequencies
    unclustered_frequencies = frequencies.copy()
    unclustered_damping = damping_ratios.copy()
    # Update the copied matrix to NaN at collected indices
    for idx in Ip_indices:
        unclustered_frequencies[tuple(idx)] = np.nan  # Set to NaN
        unclustered_damping[tuple(idx)] = np.nan
         
    # print(f'Unclustred frequencies: {unclustered_frequencies}')  
    
    # Find all indices in the frequencies matrix
    all_indices = np.array(np.meshgrid(np.arange(frequencies.shape[0]), np.arange(frequencies.shape[1]))).T.reshape(-1, 2)
    
    # Identify unclustered indices: exclude NaN and indices in clustered_indices
    unclustered_indices = []
    for idx in all_indices:
        if not np.isnan(frequencies[tuple(idx)]) and not any((idx == Ip_indices).all(axis=1)):
            unclustered_indices.append(idx)
    
    unclustered_indices = np.array(unclustered_indices) 
    # print(f'Unclustred indices: {unclustered_indices}')    
        
    return C_cluster_finale, unclustered_frequencies, unclustered_damping, unclustered_indices

# MAC calculation function
def calculate_mac(reference_mode, mode_shape):
    """
    

    Parameters
    ----------
    reference_mode : TYPE
        DESCRIPTION.
    mode_shape : TYPE
        DESCRIPTION.

    Returns
    -------
    TYPE
        DESCRIPTION.

    """
    numerator = np.abs(np.dot(reference_mode.conj().T, mode_shape)) ** 2
    denominator = np.dot(reference_mode.conj().T, reference_mode) * np.dot(mode_shape.conj().T, mode_shape)
    return np.real(numerator / denominator)

def clusterexpansion(C_clusters, unClustered_frequencies, unClustered_damping, cov_freq, cov_damping, mode_shapes, unClustered_indices, tMAC, bound_multiplier=2):
    """
    

    Parameters
    ----------
    C_clusters : TYPE
        DESCRIPTION.
    unClustered_frequencies : TYPE
        DESCRIPTION.
    unClustered_damping : TYPE
        DESCRIPTION.
    cov_freq : TYPE
        DESCRIPTION.
    cov_damping : TYPE
        DESCRIPTION.
    mode_shapes : TYPE
        DESCRIPTION.
    unClustered_indices : TYPE
        DESCRIPTION.
    bound_multiplier : TYPE, optional
        DESCRIPTION. The default is 2.

    Raises
    ------
    a
        DESCRIPTION.

    Returns
    -------
    C_cluster_finale : TYPE
        DESCRIPTION.
    unclustered_frequencies_expanded : TYPE
        DESCRIPTION.
    unclustered_damping_expanded : TYPE
        DESCRIPTION.
    unclustered_indices_expnaded : TYPE
        DESCRIPTION.

    """
    
    # cov_freq = cov_freq[::2]              
    # mode_shapes = mode_shapes[::2, :, :]
    
    # import pprint
    # for cluster in C_clusters:
    #     pprint.pprint(cluster)
    
    Ip_plus = []
    
    for cluster in C_clusters:
        
        f_values = cluster['f_values']
        z_values = cluster['z_values']
        indices = cluster['indices']
                
        # **Skip if the cluster is empty**
        if len(f_values) == 0:  
            print("Skipping empty cluster...")
            continue  # Move to the next cluster
        
        # print("Covariance Array:", np.sqrt(cov_freq[tuple(indices.T)]))        
        # Calculate the lower and upper bounds for the current cluster
        # print(f'f_values: {f_values}')
        # print(f'cov_freq[tuple(indices.T): {cov_freq[tuple(indices.T)]}')
        f_lower_bound = np.min(f_values - bound_multiplier * np.sqrt(cov_freq[tuple(indices.T)]))  # Minimum of all points for frequencies
        f_upper_bound = np.max(f_values + bound_multiplier * np.sqrt(cov_freq[tuple(indices.T)]))  # Maximum of all points for frequencies
        z_lower_bound = np.min(z_values - bound_multiplier * np.sqrt(cov_damping[tuple(indices.T)]))  # Minimum of all points for damping
        z_upper_bound = np.max(z_values + bound_multiplier * np.sqrt(cov_damping[tuple(indices.T)]))  # Maximum of all points for damping

        # print(f'Print cluster lower bound: {lower_bound}')
        # print(f'Print cluster upper bound: {upper_bound}')
                
        # Find elements within the current limit that are still ungrouped
        condition_mask2 = (unClustered_frequencies >= f_lower_bound) & (unClustered_frequencies <= f_upper_bound) & (unClustered_damping >= z_lower_bound) & (unClustered_damping <= z_upper_bound)
        # Get indices satisfying the condition
        expanded_indices = np.argwhere(condition_mask2)
        
        # Initialize lists to store updated indices and values
        updated_indices3 = []
        f_updated_values3 = []
        z_updated_values3 = []
    
        # Loop through the unclustered indices and append matching values to the cluster
        for idx in expanded_indices:
            freq_value = unClustered_frequencies[tuple(idx)]  # Get the frequency value at this index
            damp_value = unClustered_damping[tuple(idx)]      # Get the damping value at this index
            updated_indices3.append(idx)  # Append the index
            f_updated_values3.append(freq_value)  # Append the frequency value
            z_updated_values3.append(damp_value)  # Append the damping value
        
        # Create a new cluster and append it to Ip_plus_cluster
        Ip_plus.append({
            "ip_index": cluster['ip_index'],  # Use the ip_index from the original cluster
            "indices": np.array(updated_indices3),  # Updated indices
            "f_values": np.array(f_updated_values3),  # Updated frequency values
            "z_values": np.array(z_updated_values3)  # Updated damping values
        })
        
        
    Ip_plus_C = []  
    # algorith 2: setp 3 [condition check]
    for item1 in C_clusters:
        # print(f'C_cluster item: {item1}')
        # print(f'C_cluster value: {item1["values"]}')
        
        for item2 in Ip_plus:
            if item1['ip_index'] != item2['ip_index']:
                continue  # Skip the comparison if ip_index is not the same
            
            if len(item1['f_values']) == len(item2['f_values']):
                # print('For C and Ip - values have the same length. Proceeding to compare the values.')
                
                # Compare the values
                if np.all(item1['f_values'] != item2['f_values']):
                    # print(f'Values are different between C_cluster and Ip: {item1["values"]} vs {item2["values"]}')
                    continue
                else:
                    print(f'Values are the same between C_cluster and Ip_plus: {item1["f_values"]}')
            
            else:
                # print('Values have different lengths between C_cluster and Ip.')
                updated_indices4 = np.empty((0, 2), dtype=int)  # Reset to empty 2D array
                f_updated_values4  = []
                z_updated_values4  = []
                for pp in item1['indices']:
                    for kk in item2['indices']:
                        reference_mode_shape = mode_shapes[pp[0], pp[1], :]
                        target_mode_shape    = mode_shapes[kk[0], kk[1], :]
                        mac_value = calculate_mac(reference_mode_shape, target_mode_shape)
                        if mac_value > tMAC:
                            updated_indices4 = np.vstack([updated_indices4,kk])
                            f_updated_values4  = np.append(f_updated_values4, unClustered_frequencies[tuple(kk.T)])
                            z_updated_values4  = np.append(z_updated_values4, unClustered_damping[tuple(kk.T)])
                            # print(f'newly added indices: {kk}')
                            # print(f'newly added values: {frequencies[tuple(kk.T)]}')
                            Ip_plus_C.append({ 
                                "ip_index": item1['ip_index'],
                                "indices" : updated_indices4,
                                "f_values"  : f_updated_values4,
                                "z_values" : z_updated_values4
                                })


        # Initialize C_cluster_finale as a deep copy of C_cluster
        C_cluster_finale = copy.deepcopy(C_clusters)
        
        # Add the points from Ip_C_cluster if they satisfy MAC conditions
        # algorith 2: setp 3 [addition of point]
        for item1 in C_clusters:
            for item2 in Ip_plus_C:
                if item1['ip_index'] != item2['ip_index']:
                    continue  # Skip the comparison if ip_index is not the same
                
                # Combine values from both clusters
                f_merged_values2 = np.concatenate((item1['f_values'], item2['f_values']))       # concatenate frequencies
                z_merged_values2 = np.concatenate((item1['z_values'], item2['z_values']))       # concatenate damping
                # Combine indices from both clusters
                merged_indices2 = np.concatenate((item1['indices'], item2['indices']))
                
                # Find the corresponding cluster in C_cluster_finale
                for finale_item in C_cluster_finale:
                    if finale_item['ip_index'] == item1['ip_index']:
                        # Update values and indices
                        finale_item['f_values'] = f_merged_values2
                        finale_item['z_values'] = z_merged_values2
                        finale_item['indices'] = merged_indices2
                        break  # Exit the loop once the match is found  


    # algorith 2: step 4
    # Filter out empty 'indices' arrays and check if there are any non-empty ones
    valid_indices = [item['indices'] for item in C_clusters if item['indices'].size > 0]
    
    if valid_indices:
        # If there are valid indices, proceed with stacking
        Ip_plus_indices = np.vstack(valid_indices)
    else:
        # If there are no valid indices, handle accordingly (e.g., set to empty or raise a warning)
        # print("No valid indices to stack.")
        Ip_plus_indices = np.array([])  # Or choose another fallback behavior    
    # Make a copy of frequencies to represent unclustered frequencies
    unclustered_frequencies_expanded = unClustered_frequencies.copy()
    unclustered_damping_expanded = unClustered_damping.copy()
    # Update the copied matrix to NaN at collected indices
    for idx in Ip_plus_indices:
        unclustered_frequencies_expanded[tuple(idx)] = np.nan  # Set to NaN
        unclustered_damping_expanded[tuple(idx)] = np.nan  # Set to NaN
         
    # print(f'Unclustred frequencies: {unclustered_frequencies}')  
    
    # Find all indices in the frequencies matrix
    all_indices = np.array(np.meshgrid(np.arange(unClustered_frequencies.shape[0]), np.arange(unClustered_frequencies.shape[1]))).T.reshape(-1, 2)
    
    # Identify unclustered indices: exclude NaN and indices in clustered_indices
    unclustered_indices_expnaded = []
    for idx in all_indices:
        # if not np.isnan(unClustered_frequencies[tuple(idx)]) and not any((idx == Ip_plus_indices).all(axis=1)):
        if Ip_plus_indices.size > 0 and not np.isnan(unClustered_frequencies[tuple(idx)]) and not any((idx == Ip_plus_indices).all(axis=1)):
            unclustered_indices_expnaded.append(idx)
    
    unclustered_indices_expnaded = np.array(unclustered_indices_expnaded) 
    # print(f'Unclustred indices expanded: {unclustered_indices_expnaded}')

    return C_cluster_finale, unclustered_frequencies_expanded, unclustered_damping_expanded, unclustered_indices_expnaded


def visualize_clusters(clusters, cov_freq, bounds):
    """
    

    Parameters
    ----------
    clusters : TYPE
        DESCRIPTION.
    cov_freq : TYPE
        DESCRIPTION.
    bounds : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    # Sort clusters by their median if available, otherwise keep original order
    clusters.sort(key=lambda cluster: np.median(cluster["values"]) if "values" in cluster and len(cluster["values"]) > 0 else float('inf'))

    # Create subplots (one for each cluster)
    num_clusters = len(clusters)
    fig, axs = plt.subplots(num_clusters, 1, figsize=(10, 5 * num_clusters), tight_layout=True)


    if num_clusters == 1:
        axs = [axs]  # Ensure axs is always iterable

    for idx, (cluster, ax) in enumerate(zip(clusters, axs)):
        cluster_values = cluster["f_values"]
        cluster_indices = cluster["indices"]
        cluster_cov = cov_freq[tuple(np.array(cluster_indices).T)]  # Covariance for original cluster

        # Extract the second part of the cluster indices for plotting
        model_orders = cluster_indices[:, 1]
        
        # Scatter plot the cluster values against model orders
        ax.scatter(cluster_values, model_orders, label="Cluster Data")

        # Plot the cluster values with covariance as error bars
        ax.errorbar(
            cluster_values,
            model_orders,  # Use the second index for the vertical axis
            xerr=(np.sqrt(cluster_cov)*bounds),  # Error bars for x-values based on covariance
            fmt='o', capsize=5, ecolor='red', label="± 2σ"
        )
        
        # Check if the 'median' key exists in the cluster dictionary
        if 'median' in cluster:
            median_value = cluster["median"]
            if not np.isnan(median_value):  # If median is not NaN, plot the vertical line
                ax.axvline(median_value, color='blue', linestyle='--', label='Median')
           
        ax.set_title(f"Cluster {idx + 1}")
        ax.set_xlabel("Frequency [Hz]")
        ax.set_ylabel("Model Order")
        ax.set_ylim(0, 21)
        ax.legend()
        ax.grid()

    plt.show()


def clean_clusters_by_median(clusters, cov_freq, bound_multiplier=2):
    """
    

    Parameters
    ----------
    clusters : TYPE
        DESCRIPTION.
    cov_freq : TYPE
        DESCRIPTION.
    bound_multiplier : TYPE, optional
        DESCRIPTION. The default is 2.

    Returns
    -------
    cleaned_clusters : TYPE
        DESCRIPTION.

    """
    cleaned_clusters = []

    for cluster_idx, cluster in enumerate(clusters):
        # Extract values and indices from the cluster
        f_cluster_values = np.array(cluster["f_values"])
        z_cluster_values = np.array(cluster["z_values"])
        cluster_indices = np.array(cluster["indices"])
        
        # Extract covariance for each cluster element
        f_cluster_cov = cov_freq[tuple(cluster_indices.T)]  # Extract covariance for the given indices

        # Remove duplicates by using unique values and their indices
        f_unique_values, unique_indices = np.unique(f_cluster_values, return_index=True)
        f_unique_cov = f_cluster_cov[unique_indices]
        z_unique = z_cluster_values[unique_indices]
        unique_indices_2D = cluster_indices[unique_indices]

        # Update the original cluster with unique values and indices
        cluster["f_values"] = f_unique_values
        cluster["z_values"] = z_unique
        cluster["indices"] = unique_indices_2D

        # Calculate the median of the unique values
        median_value = np.nanmedian(f_unique_values)

        # Define bounds for filtering based on the bound_multiplier and covariance
        lower_bound = f_unique_values - bound_multiplier * np.sqrt(f_unique_cov)
        upper_bound = f_unique_values + bound_multiplier * np.sqrt(f_unique_cov)

        # Keep elements where the median lies within the bounds
        mask = (median_value >= lower_bound) & (median_value <= upper_bound)
        f_cleaned_values = f_unique_values[mask]
        z_cleaned_values = z_unique[mask]
        cleaned_indices = unique_indices_2D[mask]

        # Append the cleaned cluster to the result if there are enough values
        if len(f_cleaned_values) > 1:  # Keep clusters with more than one cleaned value
            cleaned_clusters.append({
                "original_cluster": cluster,  # Store the original cluster (now updated with unique values)
                "f_values": f_cleaned_values,
                "z_values": z_cleaned_values,
                "indices": cleaned_indices,
                "median": median_value,
                "bound_multiplier": bound_multiplier,  # Store the bound multiplier used
            })

    return cleaned_clusters

    
def mode_allingment(ssi_mode_track_res, mstab, tMAC):
    print("DEBUG: oma_output inside mode_allingment:", type(ssi_mode_track_res), ssi_mode_track_res)
        
    # extract results
    frequencies = ssi_mode_track_res['Fn_poles']
    cov_freq    = ssi_mode_track_res['Fn_poles_cov']
    damping_ratios = ssi_mode_track_res['Xi_poles']
    cov_damping    = ssi_mode_track_res['Xi_poles_cov']
    mode_shapes    = ssi_mode_track_res['Phi_poles']
    bounds = 2                  # standard deviation multiplier
    
    frequencies_max_MO = frequencies[:,-1]
    cov_freq_max_MO = cov_freq[:,-1]
    damping_ratios_max_MO = damping_ratios[:,-1]
    cov_damping_max_MO = cov_damping[:,-1]
    mode_shapes_max_MO = mode_shapes[:,-1,:]
    
    frequencies_copy = frequencies.copy()
    
    # Remove the complex conjugate entries
    frequencies = frequencies[::2]              # This is 'S' as per algorithm
    damping_ratios = damping_ratios[::2]        # This is 'S' as per algorithm
    mode_shapes = mode_shapes[::2, :, :]
    cov_freq = cov_freq[::2]           
    cov_damping = cov_damping[::2]   
    
    frequency_coefficient_variation = np.sqrt(cov_freq)/frequencies
    damping_coefficient_variation = np.sqrt(cov_damping)/damping_ratios
    indices_frequency = frequency_coefficient_variation > 0.05
    indices_damping   = damping_coefficient_variation > 0.5
    combined_indices = indices_frequency & indices_damping
    frequencies[combined_indices] = np.nan
    damping_ratios[combined_indices] = np.nan
    cov_freq[combined_indices] = np.nan
    cov_damping[combined_indices] = np.nan 
    
    
    # Initial clustering
    C_clusters, unClustd_frequencies, unClustd_damping, unClustd_indices = cluster_frequencies(frequencies, damping_ratios,
                                    mode_shapes, frequencies_max_MO, cov_freq_max_MO,
                                    damping_ratios_max_MO, cov_damping_max_MO, 
                                    mode_shapes_max_MO, tMAC, bound_multiplier=bounds)   
    
    # Expansion step
    C_expanded, unClustd_frequencies_expanded, unClustd_damping_expanded, unClustd_indices_expanded = clusterexpansion(C_clusters, unClustd_frequencies, unClustd_damping, 
                                  cov_freq, cov_damping, mode_shapes, 
                                  unClustd_indices, tMAC, bound_multiplier=bounds)
    
    
    last_ip_index = max(cluster['ip_index'] for cluster in C_expanded)
    
    count = 0
      
    # Loop until unClustd_indices contains only one index
    while True:
        # print(f"unClustd indices expanded size before: {unClustd_indices_expanded.size}")
        # print(f'Loop counter: {count}')
        count += 1
        # Check the termination condition
        if unClustd_indices_expanded.size <= 2:  # Stop if there are fewer than 2 indices
            print("No more unclustered indices to process. Exiting ...")
            break
    
        # Get the highest column index from unClustd_indices
        highest_column = np.max(unClustd_indices_expanded[:, 1])  # Assuming column index is in the second column
    
        # Create a mask for the unclustered indices
        mask1 = np.full(frequencies.shape, False)  # Initialize a boolean mask
        mask1[tuple(unClustd_indices_expanded.T)] = True  # Set only unclustered indices to True
        unClustd_frequencies = frequencies.copy()
        unClustd_damping = damping_ratios.copy()
        unClustd_frequencies[~mask1] = np.nan
        unClustd_damping[~mask1] = np.nan
        unClustd_cov_freq = cov_freq.copy()
        unClustd_cov_damp = cov_damping.copy()
        unClustd_cov_freq[~mask1] = np.nan  # Unclustered frequency variance matrix
        unClustd_cov_damp[~mask1] = np.nan  # Unclustered damping variance matrix
        unClustd_mode_shapes = mode_shapes.copy()
    
        for ii in range(unClustd_mode_shapes.shape[2]):  
            slice_2d = unClustd_mode_shapes[:, :, ii]    
            slice_2d[~mask1] = np.nan
            unClustd_mode_shapes[:, :, ii] = slice_2d  # Unclustered mode shape matrix
        
        # Filter the data for the highest column
        frequencies_max_MO = unClustd_frequencies_expanded[:, highest_column]
        # print(f'Maximum model order: {highest_column}')
        # print(f'MO frequencies: {frequencies_max_MO}')
        damping_ratios_max_MO = unClustd_damping_expanded[:, highest_column]
        # print(f'frequencies initization: {frequencies_max_MO}')
        cov_freq_max_MO = unClustd_cov_freq[:, highest_column]
        cov_damp_max_MO = unClustd_cov_damp[:, highest_column]
        mode_shapes_max_MO = unClustd_mode_shapes[:, highest_column, :]
    
        # Call the cluster_frequencies function with updated parameters
        C_cluster_loop, unClustd_frequencies_loop, unClustd_damping_loop, unClustd_indices_loop = cluster_frequencies(
            unClustd_frequencies, 
            unClustd_damping,
            unClustd_mode_shapes, 
            frequencies_max_MO, 
            cov_freq_max_MO, 
            damping_ratios_max_MO, 
            cov_damping_max_MO,
            mode_shapes_max_MO, 
            tMAC, 
            bound_multiplier=bounds
        )
        print("Initial clustering done.")
        
        # import pprint
        # for cluster in C_clusters:
        #     pprint.pprint(cluster)
        
        if unClustd_indices_loop.size == 0:
            print("No unclustered indices left. Exiting ...")
            # Update the clusters with new 'ip_index' values
            for cluster in C_cluster_loop:
                # Update the ip_index for the new clusters (starting from last_ip_index + 1)
                new_ip_index = last_ip_index + 1
                cluster["ip_index"] = new_ip_index
    
                # Append the updated cluster to the final list
                C_expanded.append(cluster)
    
                # Update last_ip_index to the newly assigned ip_index for the next iteration
                last_ip_index = new_ip_index
        
            # print('before break')    
            break
            # print('after break')
    
        print("Expansion started in loop.")
        # Expansion step for each initial clusters
        C_expanded_loop, unClustd_frequencies_expanded_loop, unClustd_damping_expanded_loop, unClustd_indices_expanded_loop = clusterexpansion(
            C_cluster_loop, 
            unClustd_frequencies_loop, 
            unClustd_damping_loop,
            cov_freq, 
            cov_damping,
            mode_shapes, 
            unClustd_indices_loop, 
            tMAC,
            bound_multiplier=bounds
        )
        print("Expansion clustering done.")
    
        # Update the clusters with new 'ip_index' values
        for cluster in C_expanded_loop:
            # Update the ip_index for the new clusters (starting from last_ip_index + 1)
            new_ip_index = last_ip_index + 1
            cluster["ip_index"] = new_ip_index
    
            # Append the updated cluster to the final list
            C_expanded.append(cluster)
    
            # Update last_ip_index to the newly assigned ip_index for the next iteration
            last_ip_index = new_ip_index
    
        # print("Expansion added to clustering.")
    
        if unClustd_indices_expanded_loop.size == 0:
            print("No unclustered indices left. Exiting ...")
            break
        # Update the unClustd_indices for the next iteration
        unClustd_indices_expanded = unClustd_indices_expanded_loop[
            unClustd_indices_expanded_loop[:, 1] != highest_column
        ]
           
        # Check if the size of unClustd_indices_expanded has become less than or equal to 2
        if unClustd_indices_expanded.size <= 2:
            print("Unclustered indices size <= 2. Stopping ...")
            break
    
    # Removing repeatation during merge
    for cluster in C_expanded:
        # Get the current values
        f_values = cluster['f_values']
        indices = cluster['indices']
        z_values = cluster['z_values']  
        # Find unique f_values and their indices
        unique_f_values, unique_indices = np.unique(f_values, return_index=True)    
        cluster['f_values'] = unique_f_values
        cluster['indices'] = indices[unique_indices]
        cluster['z_values'] = z_values[unique_indices]
    
    
    # # Visualize the initial clusters
    # visualize_clusters(C_expanded, cov_freq, bounds)
    
    # # import pprint
    # for cluster in C_expanded:
    #     print(f"ip_index: {cluster['ip_index']}, f_values length: {len(cluster['f_values'])}")
    #     print(f"Cluster confidence interval: {cluster['confidence_interval'][0:2]}")
    #     print(f"Cluster shape: {len(cluster['f_values'])}")
    #     # pprint.pprint(cluster)
    #     # print(f"ip_index: {cluster['ip_index']}")
    #     # print(f"indices shape: {cluster['indices'].shape}")
    #     # print(f"f_values shape: {len(cluster['f_values'])}")
    
    
    print('Cluster filter started')
    # Filter clusters with less than 'mstab' elements
    C_expanded_filtered = [cluster for cluster in C_expanded if cluster['indices'].shape[0] > mstab]
    # Sort clusters by the lower bound of their confidence_interval (the first value in the tuple)
    C_expanded_filtered.sort(key=lambda cluster: cluster['confidence_interval'][0])
    print('Cluster filter finished')
    
    # # Visualize the cluster filter by element numbers
    # visualize_clusters(C_expanded_filtered, cov_freq, bounds)
    
    # Cluster cleaning based on median
    cleaned_clusters = clean_clusters_by_median(C_expanded_filtered, cov_freq, bound_multiplier=bounds)
    
    # remove repeatative clusters
    seen = set()
    uq_clusters = []
    for d in cleaned_clusters:
        f_values_tuple = tuple(d['f_values'])
        if f_values_tuple not in seen:
            seen.add(f_values_tuple)
            uq_clusters.append(d)
            
    for cluster in uq_clusters:
        indices = cluster['indices']
        mode_shapes_list = []

        for idx in indices:
            # Extract mode shapes using indices
            mode_shape = mode_shapes[idx[0], idx[1], :]
            mode_shapes_list.append(mode_shape)

        # Add mode shapes to the dictionary
        cluster['mode_shapes'] = np.array(mode_shapes_list)
    
    uq_clusters_sorted = sorted(uq_clusters, key=lambda cluster: cluster["median"])    
    
    return uq_clusters_sorted
