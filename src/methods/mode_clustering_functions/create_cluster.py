from typing import Any, Dict
import numpy as np
from functions.calculate_mac import calculate_mac
# pylint: disable=C0103, R0912, R0914, R0915

def cluster_creation(IP: Dict[str,Any],params: Dict[str,Any]) -> Dict[str,Any]: #Algorithm 2
    """
        Create cluster

        Args:
            IP (Dict[str,Any]): Dictionary of data on inital points
            params (Dict[str,Any]): Dictionary of algorithm parameters
        Returns:
            cluster (Dict[str,Any]): Cluster

    """ #Algorithm 2
    #Extract data:
    frequencies = IP['f']
    cov_f = IP['cov_f']
    damping_ratios = IP['d']
    cov_d = IP['cov_d']
    mode_shapes = IP['ms']
    row = IP['row']
    col = IP['col']

    IPu = {}
    #line 5 in algorithm #If there are multiple points at the same model order
    if len(row) != len(set(row)):
        for ii, idx in enumerate(row): #Go through all rows/model orders
            pos = np.argwhere(row==idx) #Locate the indices of one or more poles
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
                else:
                    IPu['f'] = np.append(IPu['f'],frequencies[ii])
                    IPu['cov_f'] = np.append(IPu['cov_f'],cov_f[ii])
                    IPu['d'] = np.append(IPu['d'],damping_ratios[ii])
                    IPu['cov_d'] = np.append(IPu['cov_d'],cov_d[ii])
                    IPu['ms'] = np.vstack((IPu['ms'],mode_shapes[ii,:]))
                    IPu['row'] = np.append(IPu['row'],row[ii])
                    IPu['col'] = np.append(IPu['col'],col[ii])

        non_clustered_IPu = {'row':[]}
        if len(IPu) > 0: #If there exist model orders with unique poles
            if isinstance(IPu['f'],float):
                cluster = {'f':np.array([IPu['f']]),
                    'cov_f':np.array([IPu['cov_f']]),
                    'd':np.array([IPu['d']]),
                    'cov_d':np.array([IPu['cov_d']]),
                    'mode_shapes':np.array([IPu['ms']]),
                    'model_order':np.array([params['model_order']-IPu['row']]),
                    'row':np.array([IPu['row']]),
                    'col':np.array([IPu['col']]),
                    'MAC':np.array([1])}

            else: #If more unique poles exist
                cluster = {'f':np.array([IPu['f'][0]]),
                        'cov_f':np.array([IPu['cov_f'][0]]),
                        'd':np.array([IPu['d'][0]]),
                        'cov_d':np.array([IPu['cov_d'][0]]),
                        'mode_shapes':np.array([IPu['ms'][0,:]]),
                        'model_order':np.array([params['model_order']-IPu['row'][0]]),
                        'row':np.array([IPu['row'][0]]),
                        'col':np.array([IPu['col'][0]]),
                        'MAC':np.array([1])}

                #cluster the unique poles
                cluster, non_clustered_IPu = cluster_from_mac(cluster,IPu,params)

        else: #if no unique poles exist then go forth with the initial point, ip.
            #Only the initial point is clustered
            cluster = {'f':np.array([frequencies[0]]),
                'cov_f':np.array([cov_f[0]]),
                'd':np.array([damping_ratios[0]]),
                'cov_d':np.array([cov_d[0]]),
                'mode_shapes':np.array([mode_shapes[0,:]]),
                'model_order':np.array([params['model_order']-row[0]]),
                'row':np.array([row[0]]),
                'col':np.array([col[0]]),
                'MAC':np.array([1])}

            #Check if there are multiple points with same model order as ip
            ip_ids = np.argwhere(row==row[0])
            if len(ip_ids[:,0]) > 1: # Remove all the other points at the same model order
                for ii in np.flip(ip_ids[:,0]):
                    try:
                        frequencies = np.delete(frequencies,ii)
                        cov_f = np.delete(cov_f,ii)
                        damping_ratios = np.delete(damping_ratios,ii)
                        cov_d = np.delete(cov_d,ii)
                        mode_shapes = np.delete(mode_shapes,ii,axis=0)
                        row = np.delete(row,ii)
                        col = np.delete(col,ii)
                    except Exception as exc:
                        raise ValueError("Multiple rows exist") from exc
        if len(row) != len(set(row)): #If there still are points at the same model order in IP
            IPm = {}
            for ii, idx in enumerate(row): #Go through all rows/model orders
                pos = np.argwhere(row==idx) #Locate the indices of one or more poles
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
            cluster, non_clustered_IPm = cluster_from_mac_IPm(cluster,IPm,params)

            #Start while loop
            cluster_len_before = 0
            while len(cluster['row']) != cluster_len_before:
                cluster_len_before = len(cluster['row'])
                if len(non_clustered_IPu['row']) > 0:
                    #cluster the unique poles again
                    cluster, non_clustered_IPu = cluster_from_mac(cluster,non_clustered_IPu,
                                                                  params)
                if len(non_clustered_IPm['row']) > 0:
                    #cluster the non-unique poles again
                    cluster, non_clustered_IPm = cluster_from_mac_IPm(cluster,non_clustered_IPm,
                                                                      params)

    else: #line 1 in algorithm: only unique poles
        cluster = {'f':np.array([frequencies[0]]),
                'cov_f':np.array([cov_f[0]]),
                'd':np.array([damping_ratios[0]]),
                'cov_d':np.array([cov_d[0]]),
                'mode_shapes':np.array([mode_shapes[0,:]]),
                'model_order':np.array([params['model_order']-row[0]]),
                'row':np.array([row[0]]),
                'col':np.array([col[0]]),
                'MAC':np.array([1])}
        if IP['f'].shape[0] > 1:
            cluster, _ = cluster_from_mac(cluster,IP,params)

    return cluster

def cluster_from_mac(cluster: Dict[str,Any], IP: Dict[str,Any],
                     params: Dict[str,Any]) -> Dict[str,Any]:
    """
        Add points to cluster based on MAC

        Args:
            cluster (dict): Intermediate cluster
            IP (dict): Dictionary of data on inital points
            params (dict): Dictionary of algorithm parameters
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

    skip_id = []
    for jj, ms in enumerate(i_ms): #Go through all mode shapes in cluster
        idx = jj+1
        MAC = calculate_mac(ip_ms,ms) #Does the mode shape match with the first pole
        if MAC > params['tMAC']: #line 2 in algorithm
            #Add to cluster
            cluster['f'] = np.append(cluster['f'],frequencies[idx])
            cluster['cov_f'] = np.append(cluster['cov_f'],cov_f[idx])
            cluster['d'] = np.append(cluster['d'],damping_ratios[idx])
            cluster['cov_d'] = np.append(cluster['cov_d'],cov_d[idx])
            cluster['mode_shapes'] = np.vstack((cluster['mode_shapes'],
                                                np.array(mode_shapes[idx,:])))
            cluster['MAC'] = np.append(cluster['MAC'],MAC)
            cluster['model_order'] = np.append(cluster['model_order'],
                                               params['model_order']-row[idx])
            cluster['row'] = np.append(cluster['row'],row[idx])
            cluster['col'] = np.append(cluster['col'],col[idx])
            skip_id.append(idx)

    # Compare remaining points with newly added cluster points,
    # i.e. points are compared with the full cluster, not just ip
    if cluster['f'].shape[0] > 1: #Proceed if points have been added to cluster
        if IP['ms'].shape[0] > len(skip_id): #If there are more points to compare left, then proceed
            cluster_length = len(cluster['row'])
            new_cluster_length = 0
            while cluster_length != new_cluster_length: #Run until no points are clustered anymore
                cluster_length = len(cluster['row'])

                i_ms = IP['ms'][1:]
                for jj, ms in enumerate(i_ms):
                    idx = jj+1
                    if idx in skip_id: #Skip indecies of points that have already been added
                        continue

                    MAC_list = []
                    for c_ms in cluster['mode_shapes']:
                        MAC_list.append(calculate_mac(c_ms,ms))

                    if max(MAC_list) > params['tMAC']: #line 2 in algorithm
                        MAC = calculate_mac(ip_ms,ms)
                        #Add to cluster
                        cluster['f'] = np.append(cluster['f'],frequencies[idx])
                        cluster['cov_f'] = np.append(cluster['cov_f'],cov_f[idx])
                        cluster['d'] = np.append(cluster['d'],damping_ratios[idx])
                        cluster['cov_d'] = np.append(cluster['cov_d'],cov_d[idx])
                        cluster['mode_shapes'] = np.vstack((cluster['mode_shapes'],
                                                            np.array(mode_shapes[idx,:])))
                        cluster['MAC'] = np.append(cluster['MAC'],MAC)
                        cluster['model_order'] = np.append(cluster['model_order'],
                                                           params['model_order']-row[idx])
                        cluster['row'] = np.append(cluster['row'],row[idx])
                        cluster['col'] = np.append(cluster['col'],col[idx])

                        skip_id.append(idx)

                new_cluster_length = len(cluster['row'])


    clustered_id = []
    for row_c in cluster['row']: #For every entry in row cluster
        for ii, row_IP in enumerate(IP['row']): #For every entry in row IPu
            if row_IP == row_c: #If row_IP is a entry of "row" in the cluster,
                                # then save that row for later.
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

def cluster_from_mac_IPm(cluster: Dict[str,Any], IPm: Dict[str,Any],
                         params: Dict[str,Any]) -> Dict[str,Any]:
    """
        Cluster based on MAC if multiple poles exist for the model order

        Args:
            cluster (dict): Intermediate cluster
            IP (dict): Dictionary of data on inital points
            params (dict): Dictionary of algorithm parameters
        Returns:
            cluster (dict): Intermediate cluster

    """
    #Cluster based on MAC if multiple poles exist for the model order
    #Extract data
    frequencies = IPm['f']
    cov_f = IPm['cov_f']
    damping_ratios = IPm['d']
    cov_d = IPm['cov_d']
    mode_shapes = IPm['ms']
    row = IPm['row']
    col = IPm['col']

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
        #Go through all the model orders
        for oo, pos_i in enumerate(pos):
            MAC = np.zeros(pos_i.shape[0])

            if oo in skip_id: #Skip these model orders, since they have already been added.
                continue

            pos_i = pos_i[:,0]
            for ii, id_row in enumerate(pos_i):
                #Calculate MAC between first pole of cluster and a pole in IPm
                MAC[ii] = calculate_mac(ip_ms_0,i_ms[id_row])
                #If MAC is not satisfied
                if MAC[ii] < params['tMAC']:
                    #Search for max across all mode shapes in cluster:
                    #line 3 in algorithm
                    MAC_list = []
                    for ms in ip_ms:
                        MAC_list.append(calculate_mac(ms,i_ms[id_row]))
                    MAC[ii] = max(MAC_list)

            #Find the mask for the poles that meets the MAC criteria
            mask = MAC > params['tMAC']
            pos_MAC = np.argwhere(mask == True) #Get indicies

            #Formatting of the indicies
            if pos_MAC.shape[0] > 1: #more than one indice
                pos_MAC = pos_MAC[:,0]
            else: #Only one or zero indice (No MAC match)
                if pos_MAC.shape[0] == 1:
                    pos_MAC = pos_MAC[0]

            if pos_MAC.shape[0] > 1: #If multiple poles comply with MAC criteria
                #ids formatting
                ids = pos_i[pos_MAC]

                #Get frequencies of poles
                freq = np.zeros(ids.shape[0])
                for jj, idid in enumerate(ids):
                    freq[jj] = frequencies[idid]
                median_f = np.median(cluster['f'])

                #Locate the index of the closest pole
                idx = (np.abs(freq - median_f)).argmin()
                ll = pos_i[pos_MAC[idx]]

                #Add this pole to the cluster
                cluster['f'] = np.append(cluster['f'],frequencies[ll])
                cluster['cov_f'] = np.append(cluster['cov_f'],cov_f[ll])
                cluster['d'] = np.append(cluster['d'],damping_ratios[ll])
                cluster['cov_d'] = np.append(cluster['cov_d'],cov_d[ll])
                cluster['mode_shapes'] = np.vstack((cluster['mode_shapes'],
                                                    np.array(mode_shapes[ll,:])))
                cluster['MAC'] = np.append(cluster['MAC'],MAC[pos_MAC[idx]])
                cluster['model_order'] = np.append(cluster['model_order'],
                                                   params['model_order']-row[ll])
                cluster['row'] = np.append(cluster['row'],row[ll])
                cluster['col'] = np.append(cluster['col'],col[ll])

                skip_id.append(oo)

            elif pos_MAC.shape[0] == 1: #If only one pole complies with MAC
                ll = pos_i[pos_MAC[0]]

                #Add this pole to the cluster
                cluster['f'] = np.append(cluster['f'],frequencies[ll])
                cluster['cov_f'] = np.append(cluster['cov_f'],cov_f[ll])
                cluster['d'] = np.append(cluster['d'],damping_ratios[ll])
                cluster['cov_d'] = np.append(cluster['cov_d'],cov_d[ll])
                cluster['mode_shapes'] = np.vstack((cluster['mode_shapes'],
                                                    np.array(mode_shapes[ll,:])))
                cluster['MAC'] = np.append(cluster['MAC'],MAC[pos_MAC[0]])
                cluster['model_order'] = np.append(cluster['model_order'],
                                                   params['model_order']-row[ll])
                cluster['row'] = np.append(cluster['row'],row[ll])
                cluster['col'] = np.append(cluster['col'],col[ll])

                skip_id.append(oo)

    clustered_id = []
    for row_c in cluster['row']: #For every entry in row cluster
        for ii, row_IPm in enumerate(IPm['row']): #For every entry in row IPm
            #If row_IPm is a entry of "row" in the cluster, then save that row for later.
            if row_IPm == row_c:
                clustered_id.append(ii)

    all_id = np.array(list(range(len(IPm['row']))))

    clustered_id = np.array(clustered_id)
    if clustered_id.shape[0] > 0:
        unclustered_id = np.delete(all_id,clustered_id)
    else:
        unclustered_id = all_id

    unclustered_IPm = {}
    unclustered_IPm['f'] = IPm['f'][unclustered_id]
    unclustered_IPm['cov_f'] = IPm['cov_f'][unclustered_id]
    unclustered_IPm['d'] = IPm['d'][unclustered_id]
    unclustered_IPm['cov_d'] = IPm['cov_d'][unclustered_id]
    unclustered_IPm['ms'] = IPm['ms'][unclustered_id]
    unclustered_IPm['row'] = IPm['row'][unclustered_id]
    unclustered_IPm['col'] = IPm['col'][unclustered_id]

    return cluster, unclustered_IPm
