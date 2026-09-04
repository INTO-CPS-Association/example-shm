from typing import Any, Dict
import numpy as np
from functions.calculate_mac import calculate_mac
# pylint: disable=C0103, R1702, R0912, R0914

def alignment(cluster_dict: Dict[str,dict], params: Dict[str,Any]) -> Dict[str,dict]:
    """
        Alignment/merging of clusters

        Args:
            cluster_dict (Dict[str,dict]): Dictionary of multiple clusters
            params (Dict[str,dict]): Dictionary of algorithm parameters
        Returns:
            cluster_dict (Dict[str,dict]): Dictionary of aligned clusters

    """
    median_f = []
    upper_bound = []
    lower_bound = []
    for key in cluster_dict.keys(): #Find the median of each cluster
        cluster = cluster_dict[key]
        m_f = np.median(cluster['f'])
        median_f.append(m_f)
        upper_bound.append(np.max(cluster['f']+cluster['std_f']*params['bound_multiplier']))
        lower_bound.append(np.min(cluster['f']-cluster['std_f']*params['bound_multiplier']))
    median_f = np.array(median_f)

    deleted_cluster_id = []
    for ii, m_f in enumerate(median_f): #Go through all medians
        if ii in deleted_cluster_id: #If cluster is deleted pass on
            continue
        # Calculate absolute difference of selected median and all medians
        upper_mask = m_f-upper_bound < 0
        lower_mask = m_f-lower_bound > 0
        common_mask = np.logical_and(upper_mask,lower_mask)
        indices = np.argwhere(common_mask == True).reshape(-1)

        if indices.shape[0] > 0:# If one or more clusters are found
            ids = indices
            for idx in ids: #Go through all clusters that is closely located
                if idx in deleted_cluster_id:
                    continue

                main_cluster = cluster_dict[str(ii)] #Parent cluster
                co_located_cluster = cluster_dict[str(idx)] #Co-located cluster

                # Check mode shape for the first pole in each cluster
                MAC = calculate_mac(main_cluster['mode_shapes'][0],
                                    co_located_cluster['mode_shapes'][0])
                if m_f < 2:
                    print(m_f,np.median(co_located_cluster['f']),MAC)
                if MAC >= params['tMAC']: # If MAC complies with the criteria,
                                                    # then add the two clusters
                    cluster, cluster_remaining = join_clusters(main_cluster,
                                                                   co_located_cluster,params)
                    cluster_dict[str(ii)] = cluster #Save the new larger cluster
                    if len(cluster_remaining) == 0: #If the remaining cluster is emmpty
                        cluster_dict.pop(str(idx), None) #Remove the co-located cluster
                        deleted_cluster_id.append(int(idx)) #The delete cluster idx
                    else:
                        cluster_dict[str(idx)] = cluster_remaining #Save the remaining cluster

                else: # Check if the mode shapes across any of the poles
                                            # complies with the MAC criteria
                    MAC = np.zeros((main_cluster['mode_shapes'].shape[0],
                                    co_located_cluster['mode_shapes'].shape[0]))
                    for jj,  ms1 in enumerate(main_cluster['mode_shapes']):
                        for kk, ms2 in enumerate(co_located_cluster['mode_shapes']):
                            MAC[jj,kk] = calculate_mac(ms1,ms2)
                    if MAC.max() >= params['tMAC']: #If MAC criteria is meet add clusters together
                        cluster, cluster_remaining = join_clusters(main_cluster,
                                                                   co_located_cluster,params)
                        cluster_dict[str(ii)] = cluster #Save the new larger cluster
                        if len(cluster_remaining) == 0: #If the remaining cluster is empty
                            cluster_dict.pop(str(idx), None) #Remove the co-located cluster
                            deleted_cluster_id.append(int(idx)) #The delete cluster idx
                        else:
                            cluster_dict[str(idx)] = cluster_remaining #Save the remaining cluster
                    # else:
                    #     print(f"MAC criteria is not met. {MAC.max()} between: {np.median(main_cluster['f']),np.median(co_located_cluster['f'])}")

    cluster_dict_alligned = cluster_dict
    return cluster_dict_alligned

def join_clusters(cluster_1: Dict[str,Any], cluster_2: Dict[str,Any],
                  params: Dict[str,Any]) -> Dict[str,Any]:
    """
        Add two clusters together

        Args:
            cluster_1 (Dict[str,dict]): Cluster
            cluster_2 (Dict[str,dict]): Cluster
            params (Dict[str,dict]): Dictionary of algorithm parameters
        Returns:
            cluster (Dict[str,dict]): Joined cluster
            cluster_remaining (Dict[str,dict]): The cluster that remains

    """
    #Adding two clusters together
    cluster = {}
    cluster_remaining = {}
    row1 = cluster_1['row']
    row2 = cluster_2['row']

    #Should the dominant cluster be the one that have the higest model orders?
    if row1.shape[0] >= row2.shape[0]: #Let be the largest cluster be the dominant one
        main_cluster = cluster_1
        co_located_cluster = cluster_2
        row1 = cluster_1['row']
        row2 = cluster_2['row']
    else:
        main_cluster = cluster_2
        co_located_cluster = cluster_1
        row1 = cluster_2['row']
        row2 = cluster_1['row']

    median_f1 = np.median(main_cluster['f'])

    for MO in range(params['model_order']): #Go through all poles in a cluster
        jj = np.argwhere(row1 == MO)
        idx = np.argwhere(row2 == MO)
        if MO in row1: #If a pole in the largest cluster exist for the this model order
            if MO in row2: #If a pole exist in the same model order
                #Get frequencies of the poles
                f1 = main_cluster['f'][jj[:,0]]
                f2 = co_located_cluster['f'][idx[:,0]]
                if abs(median_f1-f2) >= abs(median_f1-f1):
                    #If pole in cluster 1 is closer to median of cluster 1
                    cluster = append_cluster_data(cluster,main_cluster,jj[:,0])
                    cluster_remaining = append_cluster_data(cluster_remaining,
                                                            co_located_cluster,idx[:,0])
                else: #If pole in cluster 2 is closer to median of cluster 1
                    cluster = append_cluster_data(cluster,co_located_cluster,idx[:,0])
                    cluster_remaining = append_cluster_data(cluster_remaining,main_cluster,jj[:,0])
            else: #If only one pole exist in the largest cluster
                cluster = append_cluster_data(cluster,main_cluster,jj[:,0])
        elif MO in row2: #If a pole in the smallest cluster exist for the model order
            cluster = append_cluster_data(cluster,co_located_cluster,idx[:,0])

    return cluster, cluster_remaining

def append_cluster_data(cluster: Dict[str,Any], co_located_cluster: Dict[str,Any],
                        idx: int) -> Dict[str,Any]:
    """
        Add cluster data to an existing cluster

        Args:
            cluster (Dict[str,dict]): Existing cluster
            co_located_cluster (Dict[str,dict]): Cluster
            idx (int): id of data to append
        Returns:
            cluster (Dict[str,dict]): Cluster

    """
    if len(cluster) == 0: #If it is the first pole
        cluster['f'] = co_located_cluster['f'][idx]
        cluster['std_f'] = co_located_cluster['std_f'][idx]
        cluster['d'] = co_located_cluster['d'][idx]
        cluster['std_d'] = co_located_cluster['std_d'][idx]
        cluster['mode_shapes'] = co_located_cluster['mode_shapes'][idx,:]
        cluster['MAC'] = co_located_cluster['MAC'][idx]
        cluster['model_order'] = co_located_cluster['model_order'][idx]
        cluster['row'] = co_located_cluster['row'][idx]
        cluster['col'] = co_located_cluster['col'][idx]
    else:
        cluster['f'] = np.append(cluster['f'],co_located_cluster['f'][idx])
        cluster['std_f'] = np.append(cluster['std_f'],co_located_cluster['std_f'][idx])
        cluster['d'] = np.append(cluster['d'],co_located_cluster['d'][idx])
        cluster['std_d'] = np.append(cluster['std_d'],co_located_cluster['std_d'][idx])
        cluster['mode_shapes'] = np.vstack((cluster['mode_shapes'],
                                            co_located_cluster['mode_shapes'][idx,:]))
        cluster['MAC'] = np.append(cluster['MAC'],co_located_cluster['MAC'][idx])
        cluster['model_order'] = np.append(cluster['model_order'],
                                           co_located_cluster['model_order'][idx])
        cluster['row'] = np.append(cluster['row'],co_located_cluster['row'][idx])
        cluster['col'] = np.append(cluster['col'],co_located_cluster['col'][idx])
    return cluster
