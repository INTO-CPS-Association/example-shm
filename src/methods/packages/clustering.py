from typing import Any
import numpy as np

# Following the algorithm proposed here: https://doi.org/10.1007/978-3-031-61421-7_56
# JVM 10/10/2025

def cluster_func(oma_results: dict[str,Any], Params : dict[str,Any]) -> tuple[dict[str,Any], dict[str,Any], dict[str,Any]]:
    """
        Clustering of OMA results

        Args:
            oma_results (dict): PyOMA results
            Params (dict): Algorihm parameters
        Returns:
            cluster_dict_1 (dict): Dictionary of clusters after clustering
            cluster_dict_2 (dict): Dictionary of clusters after alignment
            cluster_dict_3 (dict): Dictionary of clusters after cardinailty check

    """

    #Preeliminary cleaning
    frequencies_, cov_freq_, damping_ratios_, cov_damping_, mode_shapes_ = remove_complex_conjugates(oma_results)
    frequencies, cov_freq, damping_ratios, cov_damping, mode_shapes = remove_highly_uncertain_points(oma_results,Params) 

    # Transpose, flip and sort arrays, such that arrays maps directly to the stabilization diagram.
    # This means the the frequency array maps directly to the plot:
    # MO.
    # 5.| x    x     
    # 4.| x          
    # 3.| x          
    # 2.|      x
    # 1.|
    # 0.|
    #    -1----4------- Frequency
    # The frequency array will then have the shape (6,3). Initially (6,6) but the complex conjugates have been removed. So 6 is halved to 3.
    # 6 for each model order, including 0 and 3 for maximum poles in a modelorder
    # The frequency array will then become:
    #   _0_1_
    # 0| 1 4
    # 1| 1 Nan
    # 0| 1 Nan
    # 0| Nan 4
    # 0| Nan Nan
    # 0| Nan Nan 

    frequencies, cov_freq, damping_ratios, cov_damping, mode_shapes2, model_orders = transform_oma_features(frequencies, cov_freq, damping_ratios, cov_damping, mode_shapes)
    
    row, col = np.indices(model_orders.shape)
    row = row.flatten(order="C")
    col = col.flatten(order="C")

    #Initiate data
    data1 = {'frequencies':frequencies,
            'damping_ratios':damping_ratios,
            'cov_f':cov_freq,
            'cov_d':cov_damping,
            'mode_shapes':mode_shapes2,
            'row':row,
            'col':col}
    
    cluster_dict = {}
    cluster_counter = 0
    for count, f in enumerate(frequencies.flatten(order="f")): #np.count_nonzero(~np.isnan(frequencies))

        #print("\nIteration",count,"Unclustered poles:",np.count_nonzero(~np.isnan(frequencies)))

        #Extract data
        frequencies = data1['frequencies']
        damping_ratios = data1['damping_ratios']
        cov_freq = data1['cov_f']
        cov_damping = data1['cov_d']

        #Inital point
        r = row[count]
        c = col[count]
        ip = [frequencies[r,c],cov_freq[r,c],damping_ratios[r,c],cov_damping[r,c]]

        if np.isnan(ip[0]) == True: #Pass if the pole does not exist.
            pass
        else:
            initial_points = cluster_initial(ip,data1) #Algorithm. 1 step 3 - Initialization

            #Creating clusters
            cluster1 = cluster_creation(initial_points,Params)

            data2 = data1.copy()

            # Cluster expansion
            expansion = True
            kk = 0
            while expansion:
                kk += 1
                if kk > 10:
                    print("Expansion never ends, something is wrong.")
                    breakpoint()
                pre_cluster = cluster1
                cluster2 = cluster_expansion(cluster1,data2,Params,oma_results)
                if cluster2['f'].shape == pre_cluster['f'].shape:
                    if (cluster2['f'] == pre_cluster['f']).all():
                        expansion = False
                    else:
                        cluster1 = cluster2
                else:
                    cluster1 = cluster2
            
            #Sort if more than one pole exist in the cluster
            if isinstance(cluster2['f'],np.ndarray):
                cluster2 = sort_cluster(cluster2)
            
            #Save cluster
            if isinstance(cluster2['f'],np.ndarray): #Must atleast have two poles
                #print("Cluster saved", np.median(cluster2['f']))
                cluster_dict[str(cluster_counter)] = cluster2
                cluster_counter += 1
                data1 = remove_data_from_S(data2,cluster2) #Remove clustered poles from data
            else:
                print("cluster2 too short:",1,"But must be:",Params['mstab'])
            
    
    #Allignment or merging of stacked clusters
    cluster_dict2 = alignment(cluster_dict.copy(),Params)
    #Median filter
    #cluster_dict3 = median_filter(cluster_dict2.copy())

    #Custom cardinality check
    cluster_dict3 = {}
    cluster_counter = 0
    for ii, key in enumerate(cluster_dict2.keys()):
        cluster = cluster_dict2[key]
        if isinstance(cluster['f'],np.ndarray):
            if cluster['f'].shape[0] < Params['mstab']:
                print("cluster", np.median(cluster['f']),"too short:",cluster['f'].shape[0],"But must be:",Params['mstab'])
            else:
                print("Cluster saved", np.median(cluster['f']))
                cluster_dict3[str(ii)] = cluster
                cluster_counter += 1
                data1 = remove_data_from_S(data2,cluster) #Remove clustered poles from data
        else:
            print("cluster too short:",1,"But must be:",Params['mstab'])
            cluster_dict2.pop(key)
    
    #Add median and confidence intervals (one sided) to cluster data
    for key in cluster_dict3.keys():
        cluster = cluster_dict3[key]
        cluster['median_f'] = np.median(cluster['f'])
        # ci_f_upper = []
        # ci_f_lower = []
        # ci_d_upper = []
        # ci_d_lower = []
        # for ii, cov_f in enumerate(cluster['cov_f']):
        #     ci_f_upper.append(np.sqrt(cov_f) * Params['bound_multiplier'])
        #     ci_f_lower.append(np.sqrt(cov_f) * Params['bound_multiplier'])
        #     ci_d_upper.append(np.sqrt(cluster['cov_d'][ii]) * Params['bound_multiplier'])
        #     ci_d_lower.append(np.sqrt(cluster['cov_d'][ii]) * Params['bound_multiplier'])
        ci_f = np.sqrt(cluster['cov_f']) * Params['bound_multiplier']
        ci_d = np.sqrt(cluster['cov_d']) * Params['bound_multiplier']
        cluster['ci_f'] = ci_f
        cluster['ci_d'] = ci_d

    #Sort the clusters into accending order of median frequency
    median_frequencies = np.zeros(len(cluster_dict3))
    for ii, key in enumerate(cluster_dict3.keys()): 
        cluster = cluster_dict3[key]
        median_frequencies[ii] = cluster['median_f']
    
    indices = np.argsort(median_frequencies)
    cluster_dict4 = {}
    for ii, id in enumerate(np.array(list(cluster_dict3.keys()))[indices]): #Rename all cluster dict from 0 to len(cluster_dict2)
        cluster_dict4[ii] = cluster_dict3[id] #Insert a cluster into a key

    return cluster_dict4

def calculate_mac(reference_mode: np.array, mode_shape: np.array) -> float:
    """
        Calculate Modal Assurance Criterion (MAC)

        Args:
            reference_mode (np.array): Mode shape to compare to
            mode_shape (np.array): Mode shape to compare
        Returns:
            MAC (float): Modal Assurance Criterion 

    """
    numerator = np.abs(np.dot(reference_mode.conj().T, mode_shape)) ** 2
    denominator = np.dot(reference_mode.conj().T, reference_mode) * np.dot(mode_shape.conj().T, mode_shape)
    return np.real(numerator / denominator)

def cluster_initial(ip: list[float], data: dict[str,Any], bound: float = 2) -> dict[str,Any]:
    """
        Find the initial cluster points

        Args:
            ip (list): Frequency, damping and covariance for the inital point (ip)
            data (dict): OMA points data
            bound (float): Multiplier on standard deviation
        Returns:
            initial_points (float): Initial points to create cluster from

    """
    #Extract data of initial point
    ip_f = ip[0]
    ip_cov_f = ip[1]
    ip_d = ip[2]
    ip_cov_d = ip[3]

    # Confidence interval using the ±2*standard_deviation 
    f_lower_bound = ip_f - bound * np.sqrt(ip_cov_f)
    f_upper_bound = ip_f + bound * np.sqrt(ip_cov_f)
    z_lower_bound = ip_d - bound * np.sqrt(ip_cov_d)
    z_upper_bound = ip_d + bound * np.sqrt(ip_cov_d)

    
    frequencies = data['frequencies']
    damping_ratios = data['damping_ratios']

    # Find elements within the current limit that are still ungrouped
    condition_mask = (frequencies >= f_lower_bound) & (frequencies <= f_upper_bound) & (damping_ratios >= z_lower_bound) & (damping_ratios <= z_upper_bound)# & ungrouped_mask
    indices = np.argwhere(condition_mask)  # Get indices satisfying the condition

    #Generate the data for inital points
    initial_points = {}
    initial_points['f'] = data['frequencies'][condition_mask]
    initial_points['cov_f'] = data['cov_f'][condition_mask]
    initial_points['d'] = data['damping_ratios'][condition_mask]
    initial_points['cov_d'] = data['cov_d'][condition_mask]
    initial_points['ms'] = data['mode_shapes'][condition_mask,:]
    initial_points['row'] = indices[:,0]
    initial_points['col'] = indices[:,1]

    return initial_points

def cluster_creation(IP: dict[str,Any],Params: dict[str,Any]) -> dict[str,Any]: #Algorithm 2
    """
        Create cluster

        Args:
            IP (dict): Dictionary of data on inital points
            Params (dict): Dictionary of algorithm parameters
        Returns:
            cluster (dict): Cluster

    """ #Algorithm 2
    #print("\nCluster creation")
    #Extract data:
    frequencies = IP['f']
    cov_f = IP['cov_f']
    damping_ratios = IP['d']
    cov_d = IP['cov_d']
    mode_shapes = IP['ms']
    row = IP['row']
    col = IP['col']

    IPu = {}
    if len(row) != len(set(row)): #line 5 in algorithm #If there are multiple points at the same model order
        for ii, id in enumerate(row): #Go through all rows/model orders
            pos = np.argwhere(row==id) #Locate the indices of one or more poles
            #line 6 in algorithm
            if len(pos) == 1: #If only 1 pole exist at the model order
                if len(IPu) == 0: #First pole
                    IPu['f'] = frequencies[ii]
                    IPu['cov_f'] = cov_f[ii]
                    IPu['d'] = damping_ratios[ii]
                    IPu['cov_d'] = cov_d[ii]
                    IPu['ms'] = np.array((mode_shapes[ii,:]))
                    IPu['row'] = row[ii]
                    IPu['col'] = col[ii]
                    unique = 1 #To determine if the unique poles are more than one, for later use. if 1 then only one unique pole exist
                else: 
                    IPu['f'] = np.append(IPu['f'],frequencies[ii])
                    IPu['cov_f'] = np.append(IPu['cov_f'],cov_f[ii])
                    IPu['d'] = np.append(IPu['d'],damping_ratios[ii])
                    IPu['cov_d'] = np.append(IPu['cov_d'],cov_d[ii])
                    IPu['ms'] = np.vstack((IPu['ms'],mode_shapes[ii,:]))
                    IPu['row'] = np.append(IPu['row'],row[ii])
                    IPu['col'] = np.append(IPu['col'],col[ii])
                    unique = 2 #To determine if the unique poles are more than one, for later use. if 2 more than one uniqe pole exist
        
        if len(IPu) > 0: #If there exist model orders with unique poles
            if unique == 1: #If there only exist one unique pole
                cluster = {'f':np.array([IPu['f']]),
                    'cov_f':np.array([IPu['cov_f']]),
                    'd':np.array([IPu['d']]),
                    'cov_d':np.array([IPu['cov_d']]),
                    'mode_shapes':np.array([IPu['ms']]),
                    'model_order':np.array([Params['model_order']-IPu['row']]),
                    'row':np.array([IPu['row']]),
                    'col':np.array([IPu['col']]),
                    'MAC':np.array([1])}
                # print("371, IPu",cluster['f'],cluster['row'])
            else: #If more unique poles exist
                cluster = {'f':np.array([IPu['f'][0]]),
                        'cov_f':np.array([IPu['cov_f'][0]]),
                        'd':np.array([IPu['d'][0]]),
                        'cov_d':np.array([IPu['cov_d'][0]]),
                        'mode_shapes':np.array([IPu['ms'][0,:]]),
                        'model_order':np.array([Params['model_order']-IPu['row'][0]]),
                        'row':np.array([IPu['row'][0]]),
                        'col':np.array([IPu['col'][0]]),
                        'MAC':np.array([1])}
                # print("381, IPu",cluster['f'],cluster['row'])
                # print("IPu",IPu['row'])
                # if cluster['f'][0] > 300:
                #     breakpoint()
                cluster, non_clustered_IPu = cluster_from_mac(cluster,IPu,Params) #cluster the unique poles

        else: #if no unique poles exist then go forth with the initial point, ip.
            #Only the initial point is clustered
            cluster = {'f':np.array([frequencies[0]]),
                'cov_f':np.array([cov_f[0]]),
                'd':np.array([damping_ratios[0]]),
                'cov_d':np.array([cov_d[0]]),
                'mode_shapes':np.array([mode_shapes[0,:]]),
                'model_order':np.array([Params['model_order']-row[0]]),
                'row':np.array([row[0]]),
                'col':np.array([col[0]]),
                'MAC':np.array([1])}
            
            #Check if there are multiple points with same model order as ip
            ip_ids = np.argwhere(row==row[0])
            if len(ip_ids[:,0]) > 1: # Remove all the other points at the same model order
                for ii in ip_ids[1:,0]:
                    try:
                        frequencies = np.delete(frequencies,ii)
                        cov_f = np.delete(cov_f,ii)
                        damping_ratios = np.delete(damping_ratios,ii)
                        cov_d = np.delete(cov_d,ii)
                        mode_shapes = np.delete(mode_shapes,ii,axis=0)
                        row = np.delete(row,ii)
                        col = np.delete(col,ii)
                    except:
                        breakpoint()
            # print("379,ip is alone",cluster['row'],row)
        
        
        # try:
        #     print("Cluster after IPu",cluster['row'])
        # except:
        #     pass
        
        if len(row) != len(set(row)): #If there still are points at the same model order in IP
            IPm = {}
            for ii, id in enumerate(row): #Go through all rows/model orders
                pos = np.argwhere(row==id) #Locate the indices of one or more poles
                #line 6 in algorithm
                if len(pos) > 1: #If more than one pole exist for the model order
                    if len(IPm) == 0: #First pole
                        IPm['f'] = frequencies[ii]
                        IPm['cov_f'] = cov_f[ii]
                        IPm['d'] = damping_ratios[ii]
                        IPm['cov_d'] = cov_d[ii]
                        IPm['ms'] = np.array((mode_shapes[ii,:]))
                        IPm['row'] = row[ii]
                        IPm['col'] = col[ii]
                    else: 
                        IPm['f'] = np.append(IPm['f'],frequencies[ii])
                        IPm['cov_f'] = np.append(IPm['cov_f'],cov_f[ii])
                        IPm['d'] = np.append(IPm['d'],damping_ratios[ii])
                        IPm['cov_d'] = np.append(IPm['cov_d'],cov_d[ii])
                        IPm['ms'] = np.vstack((IPm['ms'],np.array(mode_shapes[ii,:])))
                        IPm['row'] = np.append(IPm['row'],row[ii])
                        IPm['col'] = np.append(IPm['col'],col[ii])
            # After the unique poles are clustered, the multiple poles are clusterd
            # try:
            #     print("IPu",IPu['f'],IPu['row'])
            # except:
            #     print("No IPu")
            # try:
            #     print("IPm",IPm['f'],IPm['row'])
            # except:
            #     print("No IPm")
            # print("to compare",cluster['f'][0],cluster['row'][0])
            cluster, non_clustered_IPm = cluster_from_mac_IPm(cluster,IPm,Params)



            #Start while loop
            cluster_len_before = 0
            while len(cluster['row']) != cluster_len_before:
                # print(len(cluster['row']),cluster_len_before)
                # print("c", cluster['row'])
                # try:
                #     print("u", non_clustered_IPu['row'])
                # except:
                #     pass
                # try:
                #     print("m", non_clustered_IPm['row'])
                # except:
                #     pass
                
                cluster_len_before = len(cluster['row'])
                try:
                    if len(non_clustered_IPu['row']) > 0:
                        cluster, non_clustered_IPu = cluster_from_mac(cluster,non_clustered_IPu,Params) #cluster the unique poles again
                except:
                    pass
                if len(non_clustered_IPm['row']) > 0:
                    cluster, non_clustered_IPm = cluster_from_mac_IPm(cluster,non_clustered_IPm,Params) #cluster the non-unique poles again

    else: #line 1 in algorithm: only unique poles
        cluster = {'f':np.array([frequencies[0]]),
                'cov_f':np.array([cov_f[0]]),
                'd':np.array([damping_ratios[0]]),
                'cov_d':np.array([cov_d[0]]),
                'mode_shapes':np.array([mode_shapes[0,:]]),
                'model_order':np.array([Params['model_order']-row[0]]),
                'row':np.array([row[0]]),
                'col':np.array([col[0]]),
                'MAC':np.array([1])}
        if IP['f'].shape[0] > 1:
            cluster, _ = cluster_from_mac(cluster,IP,Params)

    #Here lies the algorithms cardinality check
    # print(cluster)
    # if cluster['f'].shape[0] < Params['mstab']:
    #     print("cluster too short:",cluster['f'].shape[0],"But must be:",Params['mstab'])
    #     cluster = {}

    return cluster

def cluster_from_mac(cluster: dict[str,Any], IP: dict[str,Any], Params: dict[str,Any]) -> dict[str,Any]:
    """
        Add points to cluster based on MAC

        Args:
            cluster (dict): Intermediate cluster
            IP (dict): Dictionary of data on inital points
            Params (dict): Dictionary of algorithm parameters
        Returns:
            cluster (dict): Intermediate cluster

    """

    #Extract data
    frequencies = IP['f']
    cov_f = IP['cov_f']
    damping_ratios = IP['d']
    cov_d = IP['cov_d']
    mode_shapes = IP['ms']
    row = IP['row']
    col = IP['col']

    ip_ms = IP['ms'][0]
    i_ms = IP['ms'][1:]
    f_ip = frequencies[0]
    f_i = frequencies[1:]
    row_i = row[1:]
    # print(cluster['row'])
    # print(IP['ms'].shape)

    skip_id = []
    
    for jj, ms in enumerate(i_ms): #Go through all mode shapes in cluster
        idx = jj+1
        MAC = calculate_mac(ip_ms,ms) #Does the mode shape match with the first pole
        # print(row_i[jj],MAC)
        if MAC > Params['tMAC']: #line 2 in algorithm
            #Add to cluster
            cluster['f'] = np.append(cluster['f'],frequencies[idx])
            cluster['cov_f'] = np.append(cluster['cov_f'],cov_f[idx])
            cluster['d'] = np.append(cluster['d'],damping_ratios[idx])
            cluster['cov_d'] = np.append(cluster['cov_d'],cov_d[idx])
            cluster['mode_shapes'] = np.vstack((cluster['mode_shapes'],np.array(mode_shapes[idx,:])))
            cluster['MAC'] = np.append(cluster['MAC'],MAC)
            cluster['model_order'] = np.append(cluster['model_order'],Params['model_order']-row[idx])
            cluster['row'] = np.append(cluster['row'],row[idx])
            cluster['col'] = np.append(cluster['col'],col[idx])
            
            skip_id.append(idx)


    #IP['ms'] = np.delete(IP['ms'],skip_id,axis=0)

    # print(cluster['row'])
    # print(IP['ms'].shape)
    # print("skip_id",skip_id)
    #Compare remaining points with newly added cluster points, i.e. points are compared with the full cluster, not just ip
    if cluster['f'].shape[0] > 1: #If points have been added to cluster proceed
        if IP['ms'].shape[0] > len(skip_id): #If there are more points to compare left, then proceed
            unclustered_points = 1
            while IP['ms'].shape[0] != unclustered_points: #Run until no points are clustered anymore
                unclustered_points = IP['ms'].shape[0]

                i_ms = IP['ms'][1:]
                for jj, ms in enumerate(i_ms):
                    idx = jj+1
                    if idx in skip_id:
                        # print(idx)
                        continue

                    MAC_list = []
                    for c_ms in cluster['mode_shapes']:
                        MAC_list.append(calculate_mac(c_ms,ms))

                    # print("MAC_list",MAC_list)
                    if max(MAC_list) > Params['tMAC']: #line 2 in algorithm
                        #Add to cluster
                        cluster['f'] = np.append(cluster['f'],frequencies[idx])
                        cluster['cov_f'] = np.append(cluster['cov_f'],cov_f[idx])
                        cluster['d'] = np.append(cluster['d'],damping_ratios[idx])
                        cluster['cov_d'] = np.append(cluster['cov_d'],cov_d[idx])
                        cluster['mode_shapes'] = np.vstack((cluster['mode_shapes'],np.array(mode_shapes[idx,:])))
                        cluster['MAC'] = np.append(cluster['MAC'],MAC)   
                        cluster['model_order'] = np.append(cluster['model_order'],Params['model_order']-row[idx])
                        cluster['row'] = np.append(cluster['row'],row[idx])
                        cluster['col'] = np.append(cluster['col'],col[idx])

                        skip_id.append(idx)

                #IP['ms'] = np.delete(IP['ms'],skip_id,axis=0)
    
    # skip_id.insert(0,0)
    # skip_id_array = np.array(skip_id)

    # all_id = np.array(list(range(len(row))))
    # unclustered_id = np.delete(all_id,skip_id_array)

    clustered_id = []
    for r2 in cluster['row']: #For every entry in row cluster
        unclustered_point = False
        for ii, r1 in enumerate(IP['row']): #For every entry in row IPu
            if r1 == r2: #If r1 is a entry of "row" in the cluster, then save that row for later.
                clustered_id.append(ii)

    all_id = np.array(list(range(len(IP['row']))))

    clustered_id = np.array(clustered_id)
    if clustered_id.shape[0] > 0:
        unclustered_id = np.delete(all_id,clustered_id)
        unclustered_id = np.insert(unclustered_id,0,0)
    else:
        unclustered_id = all_id

    unclustered_IPu = {}
    unclustered_IPu['f'] = IP['f'][unclustered_id]
    unclustered_IPu['cov_f'] = IP['cov_f'][unclustered_id]
    unclustered_IPu['d'] = IP['d'][unclustered_id]
    unclustered_IPu['cov_d'] = IP['cov_d'][unclustered_id]
    unclustered_IPu['ms'] = IP['ms'][unclustered_id]
    unclustered_IPu['row'] = IP['row'][unclustered_id]
    unclustered_IPu['col'] = IP['col'][unclustered_id]

    return cluster, unclustered_IPu

def cluster_from_mac_IPm(cluster: dict[str,Any], IPm: dict[str,Any], Params: dict[str,Any]) -> dict[str,Any]:
    """
        Cluster based on MAC if multiple poles exist for the model order

        Args:
            cluster (dict): Intermediate cluster
            IP (dict): Dictionary of data on inital points
            Params (dict): Dictionary of algorithm parameters
        Returns:
            cluster (dict): Intermediate cluster

    """
    #Cluster based on MAC if multiple poles exist for the model order
    # print("cluster_IPm")
    #Extract data
    frequencies = IPm['f']
    cov_f = IPm['cov_f']
    damping_ratios = IPm['d']
    cov_d = IPm['cov_d']
    mode_shapes = IPm['ms']
    row = IPm['row']
    col = IPm['col']

    # if isinstance(cluster['f'],np.ndarray):
    #     ip_ms = cluster['mode_shapes'][0,:] #Mode shape of the first pole
    # else:
    #     ip_ms = cluster['mode_shapes'] #Mode shape of the first pole

    # Find the model orders with multiple poles
    pos = []
    for ii, idd in enumerate(set(row)): 
        pos.append(np.argwhere(row==idd))

    skip_id = []
    skip_id_before = None
    while skip_id != skip_id_before:
        ip_ms = cluster['mode_shapes']
        if isinstance(cluster['f'],np.ndarray):
            ip_ms_0 = ip_ms[0,:] #Mode shape of the first pole
        else:
            ip_ms_0 = ip_ms #Mode shape of the first pole
        
        i_ms = IPm['ms'][:] #Mode shape of the model orders with mutiple poles


        skip_id_before = skip_id.copy()
        # print("Cluster in IPm",cluster['row'])
 

        #Go through all the model orders
        for oo, pos_i in enumerate(pos):
            MAC = np.zeros(pos_i.shape[0])
            # print("IPm model order",list(set(row))[oo])
            
            if oo in skip_id: #Skip these model orders, since they have already been added.
                continue
            
            pos_i = pos_i[:,0]
            for ii, id_row in enumerate(pos_i):
                #print(IPm['row'][id_row],id_row)
                #print(ip_ms.shape,i_ms[id_row].shape)
                MAC[ii] = calculate_mac(ip_ms_0,i_ms[id_row]) #Calculate MAC between first pole of cluster and a pole in IPm

                #If MAC is not satisfied
                if MAC[ii] < Params['tMAC']: #Search for max across all mode shapes in cluster:
                    #line 3 in algorithm
                    MAC_list = []
                    for ms in ip_ms:
                        MAC_list.append(calculate_mac(ms,i_ms[id_row]))
                    MAC[ii] = max(MAC_list)

            #Find the mask for the poles that meets the MAC criteria
            mask = MAC > Params['tMAC']
            pos_MAC = np.argwhere(mask==True) #Get indicies

            #Formatting of the indicies
            if pos_MAC.shape[0] > 1: #more than one indice
                pos_MAC = pos_MAC[:,0]
            else: #Only one or zero indice (No MAC match)
                if pos_MAC.shape[0] == 1:
                    pos_MAC = pos_MAC[0]

            # print("MAC",MAC)
            # print("MACpos",pos_MAC)
            if pos_MAC.shape[0] > 1: #If multiple poles comply with MAC criteria
                #ids formatting
                ids = pos_i[pos_MAC]
                #ids = ids[:,0]

                #Get frequencies of poles
                freq = np.zeros(ids.shape[0])
                for jj, idid in enumerate(ids):
                    freq[jj] = frequencies[idid]
                median_f = np.median(cluster['f'])
                
                #Locate the index of the closest pole
                idx = (np.abs(freq - median_f)).argmin()
                ll = pos_i[pos_MAC[idx]]

                # print("IPm point mac approved",row[ll],frequencies[ll],MAC)

                #Add this pole to the cluster
                cluster['f'] = np.append(cluster['f'],frequencies[ll])
                cluster['cov_f'] = np.append(cluster['cov_f'],cov_f[ll])
                cluster['d'] = np.append(cluster['d'],damping_ratios[ll])
                cluster['cov_d'] = np.append(cluster['cov_d'],cov_d[ll])
                cluster['mode_shapes'] = np.vstack((cluster['mode_shapes'],np.array(mode_shapes[ll,:])))
                cluster['MAC'] = np.append(cluster['MAC'],MAC[pos_MAC[idx]])
                cluster['model_order'] = np.append(cluster['model_order'],Params['model_order']-row[ll])
                cluster['row'] = np.append(cluster['row'],row[ll])
                cluster['col'] = np.append(cluster['col'],col[ll])

                skip_id.append(oo)

            elif pos_MAC.shape[0] == 1: #If only one pole complies with MAC
                ll = pos_i[pos_MAC[0]]


                # print("IPm point mac approved",row[ll],frequencies[ll],MAC)
                

                #Add this pole to the cluster
                cluster['f'] = np.append(cluster['f'],frequencies[ll])
                cluster['cov_f'] = np.append(cluster['cov_f'],cov_f[ll])
                cluster['d'] = np.append(cluster['d'],damping_ratios[ll])
                cluster['cov_d'] = np.append(cluster['cov_d'],cov_d[ll])
                cluster['mode_shapes'] = np.vstack((cluster['mode_shapes'],np.array(mode_shapes[ll,:])))
                cluster['MAC'] = np.append(cluster['MAC'],MAC[pos_MAC[0]])
                cluster['model_order'] = np.append(cluster['model_order'],Params['model_order']-row[ll])
                cluster['row'] = np.append(cluster['row'],row[ll])
                cluster['col'] = np.append(cluster['col'],col[ll])

                skip_id.append(oo)
            # else:
            #     print("Not clustered. MAC not satisfied")
        # print("skip",skip_id)

    clustered_id = []
    for r2 in cluster['row']: #For every entry in row cluster
        unclustered_point = False
        for ii, r1 in enumerate(IPm['row']): #For every entry in row IPm
            if r1 == r2: #If r1 is a entry of "row" in the cluster, then save that row for later.
                clustered_id.append(ii)

    all_id = np.array(list(range(len(IPm['row']))))

    clustered_id = np.array(clustered_id)
    if clustered_id.shape[0] > 0:
        unclustered_id = np.delete(all_id,clustered_id)
    else:
        unclustered_id = all_id
    # print("709,unclustered_id",unclustered_id)

    unclustered_IPm = {}
    unclustered_IPm['f'] = IPm['f'][unclustered_id]
    unclustered_IPm['cov_f'] = IPm['cov_f'][unclustered_id]
    unclustered_IPm['d'] = IPm['d'][unclustered_id]
    unclustered_IPm['cov_d'] = IPm['cov_d'][unclustered_id]
    unclustered_IPm['ms'] = IPm['ms'][unclustered_id]
    unclustered_IPm['row'] = IPm['row'][unclustered_id]
    unclustered_IPm['col'] = IPm['col'][unclustered_id]

    # print("unclustered_IPm['row']",unclustered_IPm['row'])
    

    return cluster, unclustered_IPm

def remove_data_from_S(data: dict[str,Any],cluster: dict[str,Any]) -> dict[str,Any]:
    """
        Remove cluster from data or S

        Args:
            data (dict): OMA points data
            cluster (dict): cluster
        Returns:
            data2 (dict): Filtered OMA points data

    """
    #Copy data
    frequencies = data['frequencies'].copy()
    damping_ratios = data['damping_ratios'].copy()
    cov_freq = data['cov_f'].copy()
    cov_damping = data['cov_d'].copy()
    mode_shapes = data['mode_shapes'].copy()
    row = data['row'].copy()
    col = data['col'].copy()
    #Make new data dictionary
    data2 = {'frequencies':frequencies,
            'damping_ratios':damping_ratios,
            'cov_f':cov_freq,
            'cov_d':cov_damping,
            'mode_shapes':mode_shapes,
            'row':row,
            'col':col}
    #Remove data
    row = cluster['row']
    col = cluster['col']
    for ii, r in enumerate(row):
        c = col[ii]
        data2['frequencies'][r,c] = np.nan
        data2['damping_ratios'][r,c] = np.nan
        data2['cov_f'][r,c] = np.nan
        data2['cov_d'][r,c] = np.nan
        data2['mode_shapes'][r,c,:] = np.nan
    
    return data2

def cluster_expansion(cluster: dict[str,Any], data: dict[str,Any], Params: dict[str,Any], oma_results) -> dict[str,Any]:
    """
        Expand cluster based on minima and maxima bound

        Args:
            cluster (dict): Intermediate cluster
            data (dict): OMA points data
            Params (dict): Dictionary of algorithm parameters
        Returns:
            cluster (dict): Expanded cluster

    """
    #print("\nExpansion")
    unClustered_frequencies = data['frequencies']
    unClustered_damping = data['damping_ratios']
    
    freq_c = cluster['f']
    cov_f = cluster['cov_f']
    damp_c = cluster['d']
    cov_d = cluster['cov_d']
    row = cluster['row']

    bound_multiplier = Params['bound_multiplier']
    
    #Find min-max bounds of cluster
    f_lower_bound = np.min(freq_c - bound_multiplier * np.sqrt(cov_f))  # Minimum of all points for frequencies
    f_upper_bound = np.max(freq_c + bound_multiplier * np.sqrt(cov_f))  # Maximum of all points for frequencies
    d_lower_bound = np.min(damp_c - bound_multiplier * np.sqrt(cov_d))  # Minimum of all points for damping
    d_upper_bound = np.max(damp_c + bound_multiplier * np.sqrt(cov_d))  # Maximum of all points for damping

    #Mask of possible expanded poles
    condition_mask = (unClustered_frequencies >= f_lower_bound) & (unClustered_frequencies <= f_upper_bound) & (unClustered_damping >= d_lower_bound) & (unClustered_damping <= d_upper_bound)
    # Get indices satisfying the condition
    expanded_indices = np.argwhere(condition_mask)

    #Initiate cluster_points for cluster creation
    cluster_points = {}
    cluster_points['f'] = data['frequencies'][condition_mask]
    cluster_points['cov_f'] = data['cov_f'][condition_mask]
    cluster_points['d'] = data['damping_ratios'][condition_mask]
    cluster_points['cov_d'] = data['cov_d'][condition_mask]
    cluster_points['ms'] = data['mode_shapes'][condition_mask,:]
    cluster_points['row'] = expanded_indices[:,0]
    cluster_points['col'] = expanded_indices[:,1]

    #print(cluster_points['f'])
    #print(cluster_points['row'])

    #Make the first ip from cluster be the previous first point in cluster_points
    if isinstance(cluster['f'],np.ndarray):
        index_f = np.argwhere(cluster_points['f'] == cluster['f'][0])
    else:
        index_f = np.argwhere(cluster_points['f'] == cluster['f'])
    if len(index_f[:,0]) > 1:
        index_row = np.argwhere(cluster_points['row'][index_f[:,0]] == cluster['row'][0])
        ip_id = int(index_f[index_row[:,0]][:,0])
    else:
        ip_id = int(index_f[:,0])
    indecies = list(range(len(cluster_points['f'])))
    poped_id = indecies.pop(ip_id)
    indecies.insert(0,poped_id)
    indecies = np.array(indecies)

    cluster_points['f'] = cluster_points['f'][indecies]
    cluster_points['cov_f'] = cluster_points['cov_f'][indecies]
    cluster_points['d'] = cluster_points['d'][indecies]
    cluster_points['cov_d'] = cluster_points['cov_d'][indecies]
    cluster_points['ms'] = cluster_points['ms'][indecies,:]
    cluster_points['row'] = cluster_points['row'][indecies]
    cluster_points['col'] = cluster_points['col'][indecies]

    # print("row_before",cluster_points['row'])
    #print("exp1",cluster_points['f'])

    #Check if these values can be clustered
    cluster = cluster_creation(cluster_points,Params)
    if isinstance(cluster['f'],np.ndarray):
        if len(cluster['row']) != len(set(cluster['row'])):
            print("row_before",cluster_points['row'])
            print("row_after",cluster['row'])
            print("exp2",cluster['f'])
            print("double orders",cluster['row'])
            
            breakpoint()
    
    # print("row_before",cluster_points['row'])
    #print("exp1",cluster_points['f'])
    # print("row_after",cluster['row'])
    # print("exp2",cluster['f'])

    return cluster

def sort_cluster(cluster: dict[str,Any]) -> dict[str,Any]:
    """
        Sort cluster based on row/model order

        Args:
            cluster (dict): Cluster
        Returns:
            cluster (dict): Sorted cluster

    """
    sort_id = np.argsort(cluster['row'])

    cluster['f'] = cluster['f'][sort_id]
    cluster['cov_f'] = cluster['cov_f'][sort_id]
    cluster['d'] = cluster['d'][sort_id]
    cluster['cov_d'] = cluster['cov_d'][sort_id]
    cluster['mode_shapes'] = cluster['mode_shapes'][sort_id,:]
    cluster['MAC'] = cluster['MAC'][sort_id]
    cluster['model_order'] = cluster['model_order'][sort_id]
    cluster['row'] = cluster['row'][sort_id]
    cluster['col'] = cluster['col'][sort_id]
    
    return cluster

def alignment(cluster_dict: dict[str,dict], Params: dict[str,Any]) -> dict[str,dict]:
    """
        Alignment/merging of clusters

        Args:
            cluster_dict (dict): Dictionary of multiple clusters
            Params (dict): Dictionary of algorithm parameters
        Returns:
            cluster_dict (dict): Dictionary of aligned clusters

    """
    #print("\nCluster alignment")
    median_f = []
    for key in cluster_dict.keys(): #Find the median of each cluster
        cluster = cluster_dict[key]
        median_f.append(np.median(cluster['f']))
    median_f = np.array(median_f)

    deleted_cluster_id = []
    for ii, m_f in enumerate(median_f): #Go through all medians
        if ii in deleted_cluster_id: #If cluster is deleted pass on
            #print(deleted_cluster_id)
            continue
        # Calculate absolute difference of selected median and all medians
        diff = abs(median_f-m_f)
        # If this difference is above 0 (not itself) and inside the bounds:
        # Bounds are the minimum of either median_f * allignment_factor_0 or Sampling frequency / 2 * allignment_factor_1
        # For lower median frequencies the bound is determined by the size of median frequency.
        # For higher median frequencies the bound is determined by the sampling frequency

        mask = (diff > 0) & (diff < min(m_f*Params['allignment_factor'][0],Params['Fs']/2*Params['allignment_factor'][1]))
        indices = np.argwhere(mask == True) #Indicies of clusters that are closely located in frequency



        #print(cluster_dict.keys())
        if indices.shape[0] > 0:# If one or more clusters are found
            ids = indices[:,0]
            #print("ids",ids)
            for id in ids: #Go through all clusters that is closely located
                if id in deleted_cluster_id:
                    continue


                #print("id",id)
                break_loop = 0
                cluster1 = cluster_dict[str(ii)] #Parent cluster
                cluster2 = cluster_dict[str(id)] #Co-located cluster
                
                # Proposed method
                # for r in cluster2['model_order']:
                #     if r in cluster1['model_order']: #If the two clusters have poles with same model order, then skip the allignment
                #         print("Clusters have the same MO",cluster2['model_order'],cluster1['model_order'])
                #         break_loop = 1
                # if break_loop == 1:
                #     break

                MAC = calculate_mac(cluster1['mode_shapes'][0],cluster2['mode_shapes'][0]) # Check mode shape for the first pole in each cluster
                if MAC >= Params['tMAC']: #If MAC complies with the criteria, then add the two clusters
                    cluster, cluster_remaining = join_clusters(cluster_dict[str(ii)],cluster_dict[str(id)],Params)
                    cluster_dict[str(ii)] = cluster #Save the new larger cluster
                    if len(cluster_remaining) == 0: #If the remaining cluster is emmpty
                        cluster_dict.pop(str(id), None) #Remove the co-located cluster
                        deleted_cluster_id.append(int(id)) #The delete cluster id
                    else:
                        cluster_dict[str(id)] = cluster_remaining #Save the remaining cluster

                else: #Check if the mode shapes across any of the poles complies with the MAC criteria
                    
                    MAC = np.zeros((cluster1['mode_shapes'].shape[0],cluster2['mode_shapes'].shape[0]))
                    for jj,  ms1 in enumerate(cluster1['mode_shapes']):
                        for kk, ms2 in enumerate(cluster2['mode_shapes']):
                            MAC[jj,kk] = calculate_mac(ms1,ms2)
                    if MAC.max() >= Params['tMAC']: #If MAC criteria is meet add the clusters together
                        cluster, cluster_remaining = join_clusters(cluster_dict[str(ii)],cluster_dict[str(id)],Params)
                        cluster_dict[str(ii)] = cluster #Save the new larger cluster
                        if len(cluster_remaining) == 0: #If the remaining cluster is emmpty
                            cluster_dict.pop(str(id), None) #Remove the co-located cluster
                            deleted_cluster_id.append(int(id)) #The delete cluster id
                        else:
                            cluster_dict[str(id)] = cluster_remaining #Save the remaining cluster
                    # else:
                    #     if cluster1['f'][0] > 300:
                    #         breakpoint()
                    
    
    cluster_dict_alligned = cluster_dict
    return cluster_dict_alligned

def join_clusters(cluster_1: dict[str,Any], cluster_2: dict[str,Any], Params: dict[str,Any]) -> dict[str,Any]:
    """
        Add two clusters together

        Args:
            cluster_1 (dict): Cluster
            cluster_2 (dict): Cluster
            Params (dict): Dictionary of algorithm parameters
        Returns:
            cluster (dict): Joined cluster
            cluster_remaining (dict): The cluster that remains

    """
    #Adding two clusters together
    cluster = {}
    cluster_remaining = {}
    row1 = cluster_1['row']
    row2 = cluster_2['row']

    #Should the dominant cluster be the one that have the higest model orders?
    if row1.shape[0] >= row2.shape[0]: #Let be the largest cluster be the dominant one
        cluster1 = cluster_1
        cluster2 = cluster_2
        row1 = cluster_1['row']
        row2 = cluster_2['row']
    else:
        cluster1 = cluster_2
        cluster2 = cluster_1
        row1 = cluster_2['row']
        row2 = cluster_1['row']

    median_f1 = np.median(cluster1['f'])

    for MO in range(Params['model_order']): #Go through all poles in a cluster
        jj = np.argwhere(row1 == MO)
        id = np.argwhere(row2 == MO)
        if MO in row1: #If a pole in the largest cluster exist for the this model order
            r1 = MO
            if MO in row2: #If a pole exist in the same model order
                #Get frequencies of the poles
                f1 = cluster1['f'][jj[:,0]]
                f2 = cluster2['f'][id[:,0]]
                if abs(median_f1-f2) >= abs(median_f1-f1): #If pole in cluster 1 is closer to median of cluster 1
                    cluster = append_cluster_data(cluster,cluster1,jj[:,0])
                    cluster_remaining = append_cluster_data(cluster_remaining,cluster2,id[:,0])
                else: #If pole in cluster 2 is closer to median of cluster 1
                    cluster = append_cluster_data(cluster,cluster2,id[:,0])
                    cluster_remaining = append_cluster_data(cluster_remaining,cluster1,jj[:,0])
            else: #If only one pole exist in the largest cluster
                cluster = append_cluster_data(cluster,cluster1,jj[:,0])
        elif MO in row2: #If a pole in the smallest cluster exist for the model order
            cluster = append_cluster_data(cluster,cluster2,id[:,0])

    return cluster, cluster_remaining

def append_cluster_data(cluster: dict[str,Any], cluster2: dict[str,Any], id: int) -> dict[str,Any]:
    """
        Add cluster data to an existing cluster

        Args:
            cluster (dict): Existing cluster
            cluster2 (dict): Cluster
            id (int): id of data to append
        Returns:
            cluster (dict): Cluster

    """
    if len(cluster) == 0: #If it is the first pole
        cluster['f'] = cluster2['f'][id]
        cluster['cov_f'] = cluster2['cov_f'][id]
        cluster['d'] = cluster2['d'][id]
        cluster['cov_d'] = cluster2['cov_d'][id]
        cluster['mode_shapes'] = cluster2['mode_shapes'][id,:]
        cluster['MAC'] = cluster2['MAC'][id]
        cluster['model_order'] = cluster2['model_order'][id]
        cluster['row'] = cluster2['row'][id]
        cluster['col'] = cluster2['col'][id]
    else:
        cluster['f'] = np.append(cluster['f'],cluster2['f'][id])
        cluster['cov_f'] = np.append(cluster['cov_f'],cluster2['cov_f'][id])
        cluster['d'] = np.append(cluster['d'],cluster2['d'][id])
        cluster['cov_d'] = np.append(cluster['cov_d'],cluster2['cov_d'][id])
        cluster['mode_shapes'] = np.vstack((cluster['mode_shapes'],cluster2['mode_shapes'][id,:]))
        cluster['MAC'] = np.append(cluster['MAC'],cluster2['MAC'][id])
        cluster['model_order'] = np.append(cluster['model_order'],cluster2['model_order'][id])
        cluster['row'] = np.append(cluster['row'],cluster2['row'][id])
        cluster['col'] = np.append(cluster['col'],cluster2['col'][id])
    return cluster

def median_filter(cluster_dict: dict[str,dict]) -> dict[str,dict]:
    """
        Apply median filter to cluster

        Args:
            cluster_dict (dict): Dictionary of multiple clusters
        Returns:
            cluster_dict3 (dict): Median filtered multiple clusters

    """
    print("\nMedian filter")
    cluster_dict3 = {}
    for key in cluster_dict.keys():
        cluster = cluster_dict[key]
        #print(cluster['mode_shapes'])
        median_f = np.median(cluster['f']) #Calculate median

        cluster_new = {}
        for ii, f in enumerate(cluster['f']): #Go through all cluster poles
            lower_bound = f - np.sqrt(cluster['cov_f'][ii]) * 2
            upper_bound = f + np.sqrt(cluster['cov_f'][ii]) * 2
            if (median_f > lower_bound) & (median_f < upper_bound): #Check if a cluster confidence interval wraps the median
                cluster_new = append_cluster_data(cluster_new,cluster,ii)
            # else:
                # print("not",cluster['model_order'][ii])
        
        cluster_dict3[key] = cluster_new

    return cluster_dict3


def remove_complex_conjugates(oma_results):
    """
    Remove complex conjucates
    
    Args:
        oma_results (Dict[str, Any]): Results from PyOMA-2
    
    Returns:
        frequencies (np.ndarray): Frequencies (mean)
        cov_freq (np.ndarray): Covariance of frequency
        damping_ratios (np.ndarray): Damping ratios (mean)
        cov_damping (np.ndarray): Covariance of damping ratio
        mode_shapes (np.ndarray): Mode shapes
    """
    OMA = oma_results.copy()
    # OMA results as numpy array
    frequencies = OMA['Fn_poles'].copy()
    cov_freq    = OMA['Fn_poles_cov'].copy()
    damping_ratios = OMA['Xi_poles'].copy()
    cov_damping    = OMA['Xi_poles_cov'].copy()
    mode_shapes = OMA['Phi_poles'].copy()

    # Remove the complex conjugate entries
    frequencies = frequencies[::2]              # This is 'S' as per algorithm
    damping_ratios = damping_ratios[::2]        # This is 'S' as per algorithm
    mode_shapes = mode_shapes[::2, :, :]
    cov_freq = cov_freq[::2]           
    cov_damping = cov_damping[::2]

    return frequencies, cov_freq, damping_ratios, cov_damping, mode_shapes

def transform_oma_features(frequencies_,cov_freq_,damping_ratios_,cov_damping_,mode_shapes_):
    """
    Transform oma results
    
    Args:
        frequencies_ (np.ndarray): Frequencies (mean)
        cov_freq_ (np.ndarray): Covariance of frequency
        damping_ratios_ (np.ndarray): Damping ratios (mean)
        cov_damping_ (np.ndarray): Covariance of damping ratio
        mode_shapes_ (np.ndarray): Mode shapes
    
    Returns:
        frequencies (np.ndarray): Frequencies (mean)
        cov_freq (np.ndarray): Covariance of frequency
        damping_ratios (np.ndarray): Damping ratios (mean)
        cov_damping (np.ndarray): Covariance of damping ratio
        mode_shapes (np.ndarray): Mode shapes
    """
    # Transpose, flip and sort arrays, such that arrays maps directly to the stabilization diagram.
    # This means the the frequency array maps directly to the plot:
    # MO.
    # 5.| x    x     
    # 4.| x          
    # 3.| x          
    # 2.|      x
    # 1.|
    # 0.|
    #    -1----4------- Frequency
    # The frequency array will then have the shape (6,3). Initially (6,6) but the complex conjugates have been removed. So 6 is halved to 3.
    # 6 for each model order, including 0 and 3 for maximum poles in a modelorder
    # The frequency array will then become:
    #   _0_1_
    # 0| 1 4
    # 1| 1 Nan
    # 0| 1 Nan
    # 0| Nan 4
    # 0| Nan Nan
    # 0| Nan Nan 

    #Transformation of data
    frequencies = np.transpose(frequencies_)
    frequencies = np.flip(frequencies, 0)
    sort_indices = np.argsort(frequencies,axis=1)
    frequencies = np.take_along_axis(frequencies, sort_indices, axis=1)
    cov_freq = np.transpose(cov_freq_)
    cov_freq = np.flip(cov_freq, 0)
    cov_freq = np.take_along_axis(cov_freq, sort_indices, axis=1)
    damping_ratios = np.transpose(damping_ratios_)
    damping_ratios = np.flip(damping_ratios, 0)
    damping_ratios = np.take_along_axis(damping_ratios, sort_indices, axis=1)
    cov_damping = np.transpose(cov_damping_)
    cov_damping = np.flip(cov_damping, 0)
    cov_damping = np.take_along_axis(cov_damping, sort_indices, axis=1)
    mode_shapes = np.moveaxis(mode_shapes_, [0, 1, 2], [1, 0, 2])
    
    mode_shapes2 = np.zeros(mode_shapes.shape,dtype=np.complex128)
    for ii, indices in enumerate(sort_indices):
        mode_shapes2[ii,:,:] = mode_shapes[(sort_indices.shape[0]-ii-1),indices,:]

    # Array of model orders
    model_order = np.arange(sort_indices.shape[0])
    model_orders = np.stack((model_order,) * sort_indices.shape[1], axis=1)
    model_orders = np.flip(model_orders)

    return frequencies, cov_freq, damping_ratios, cov_damping, mode_shapes2, model_orders

def remove_highly_uncertain_points(oma_results,oma_params):
    """
    Remove highly uncertain points
    
    Args:
        oma_results (Dict[str, Any]): Results from PyOMA-2
        oma_params (Dict[str, Any]): Parameters
    
    Returns:
        frequencies (np.ndarray): Frequencies (mean)
        cov_freq (np.ndarray): Covariance of frequency
        damping_ratios (np.ndarray): Damping ratios (mean)
        cov_damping (np.ndarray): Covariance of damping ratio
        mode_shapes (np.ndarray): Mode shapes
    """
    frequencies, cov_freq, damping_ratios, cov_damping, mode_shapes = remove_complex_conjugates(oma_results)

    # # #=================== Removing high uncertain poles =======================
    freq_variance_treshold = oma_params.get('freq_variance_treshold', 0.1)
    damp_variance_treshold = oma_params.get('damp_variance_treshold', 10**6)
    frequency_coefficient_variation = np.sqrt(cov_freq)/frequencies
    damping_coefficient_variation = np.sqrt(cov_damping)/damping_ratios
    indices_frequency = frequency_coefficient_variation > freq_variance_treshold
    indices_damping   = damping_coefficient_variation > damp_variance_treshold
    above_nyquist = frequencies > oma_params['Fs']/2
    combined_indices = np.logical_or(np.logical_or(indices_frequency,indices_damping),above_nyquist)
    frequencies[combined_indices] = np.nan
    damping_ratios[combined_indices] = np.nan
    cov_freq[combined_indices] = np.nan
    cov_damping[combined_indices] = np.nan
    mask = np.broadcast_to(np.expand_dims(combined_indices, axis=2), mode_shapes.shape)
    mode_shapes[mask] = np.nan

    return frequencies, cov_freq, damping_ratios, cov_damping, mode_shapes