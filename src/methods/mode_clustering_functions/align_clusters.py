from typing import Any, Dict
import numpy as np
from functions.calculate_mac import calculate_mac
# pylint: disable=C0103

def alignment(cluster_dict: Dict[str,dict], params: Dict[str,Any]) -> Dict[str,dict]:
    """
        Alignment/merging of clusters

        Args:
            cluster_dict (dict): Dictionary of multiple clusters
            params (dict): Dictionary of algorithm parameters
        Returns:
            cluster_dict (dict): Dictionary of aligned clusters

    """
    median_f = []
    for key in cluster_dict.keys(): #Find the median of each cluster
        cluster = cluster_dict[key]
        median_f.append(np.median(cluster['f']))
    median_f = np.array(median_f)

    deleted_cluster_id = []
    for ii, m_f in enumerate(median_f): #Go through all medians
        if ii in deleted_cluster_id: #If cluster is deleted pass on
            continue
        # Calculate absolute difference of selected median and all medians
        diff = abs(median_f-m_f)
        # If this difference is above 0 (not itself) and inside the bounds:
        # Bounds are the minimum of either median_f * allignment_factor_0
        # or Sampling frequency / 2 * allignment_factor_1
        # For lower median frequencies the bound is determined by the size of median frequency.
        # For higher median frequencies the bound is determined by the sampling frequency

        mask = (diff > 0) & (diff < min(m_f*params['allignment_factor'][0],
                                        params['Fs']/2*params['allignment_factor'][1]))
        #Indicies of clusters that are closely located in frequency
        indices = np.argwhere(mask == True)

        if indices.shape[0] > 0:# If one or more clusters are found
            ids = indices[:,0]
            for idx in ids: #Go through all clusters that is closely located
                if idx in deleted_cluster_id:
                    continue

                cluster1 = cluster_dict[str(ii)] #Parent cluster
                cluster2 = cluster_dict[str(idx)] #Co-located cluster

                # Check mode shape for the first pole in each cluster
                MAC = calculate_mac(cluster1['mode_shapes'][0],cluster2['mode_shapes'][0])
                if MAC >= params['tMAC']: #If MAC complies with the criteria, then add the two clusters
                    cluster, cluster_remaining = join_clusters(cluster_dict[str(ii)],
                                                               cluster_dict[str(idx)],
                                                               params)
                    cluster_dict[str(ii)] = cluster #Save the new larger cluster
                    if len(cluster_remaining) == 0: #If the remaining cluster is emmpty
                        cluster_dict.pop(str(idx), None) #Remove the co-located cluster
                        deleted_cluster_id.append(int(idx)) #The delete cluster idx
                    else:
                        cluster_dict[str(idx)] = cluster_remaining #Save the remaining cluster

                else: #Check if the mode shapes across any of the poles complies with the MAC criteria
                    MAC = np.zeros((cluster1['mode_shapes'].shape[0],
                                    cluster2['mode_shapes'].shape[0]))
                    for jj,  ms1 in enumerate(cluster1['mode_shapes']):
                        for kk, ms2 in enumerate(cluster2['mode_shapes']):
                            MAC[jj,kk] = calculate_mac(ms1,ms2)
                    if MAC.max() >= params['tMAC']: #If MAC criteria is meet add clusters together
                        cluster, cluster_remaining = join_clusters(cluster_dict[str(ii)],
                                                                   cluster_dict[str(idx)],params)
                        cluster_dict[str(ii)] = cluster #Save the new larger cluster
                        if len(cluster_remaining) == 0: #If the remaining cluster is emmpty
                            cluster_dict.pop(str(idx), None) #Remove the co-located cluster
                            deleted_cluster_id.append(int(idx)) #The delete cluster idx
                        else:
                            cluster_dict[str(idx)] = cluster_remaining #Save the remaining cluster

    cluster_dict_alligned = cluster_dict
    return cluster_dict_alligned

def join_clusters(cluster_1: Dict[str,Any], cluster_2: Dict[str,Any],
                  params: Dict[str,Any]) -> Dict[str,Any]:
    """
        Add two clusters together

        Args:
            cluster_1 (dict): Cluster
            cluster_2 (dict): Cluster
            params (dict): Dictionary of algorithm parameters
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

    for MO in range(params['model_order']): #Go through all poles in a cluster
        jj = np.argwhere(row1 == MO)
        idx = np.argwhere(row2 == MO)
        if MO in row1: #If a pole in the largest cluster exist for the this model order
            if MO in row2: #If a pole exist in the same model order
                #Get frequencies of the poles
                f1 = cluster1['f'][jj[:,0]]
                f2 = cluster2['f'][idx[:,0]]
                if abs(median_f1-f2) >= abs(median_f1-f1):
                    #If pole in cluster 1 is closer to median of cluster 1
                    cluster = append_cluster_data(cluster,cluster1,jj[:,0])
                    cluster_remaining = append_cluster_data(cluster_remaining,cluster2,idx[:,0])
                else: #If pole in cluster 2 is closer to median of cluster 1
                    cluster = append_cluster_data(cluster,cluster2,idx[:,0])
                    cluster_remaining = append_cluster_data(cluster_remaining,cluster1,jj[:,0])
            else: #If only one pole exist in the largest cluster
                cluster = append_cluster_data(cluster,cluster1,jj[:,0])
        elif MO in row2: #If a pole in the smallest cluster exist for the model order
            cluster = append_cluster_data(cluster,cluster2,idx[:,0])

    return cluster, cluster_remaining

def append_cluster_data(cluster: Dict[str,Any], cluster2: Dict[str,Any], idx: int) -> Dict[str,Any]:
    """
        Add cluster data to an existing cluster

        Args:
            cluster (dict): Existing cluster
            cluster2 (dict): Cluster
            idx (int): id of data to append
        Returns:
            cluster (dict): Cluster

    """
    if len(cluster) == 0: #If it is the first pole
        cluster['f'] = cluster2['f'][idx]
        cluster['cov_f'] = cluster2['cov_f'][idx]
        cluster['d'] = cluster2['d'][idx]
        cluster['cov_d'] = cluster2['cov_d'][idx]
        cluster['mode_shapes'] = cluster2['mode_shapes'][idx,:]
        cluster['MAC'] = cluster2['MAC'][idx]
        cluster['model_order'] = cluster2['model_order'][idx]
        cluster['row'] = cluster2['row'][idx]
        cluster['col'] = cluster2['col'][idx]
    else:
        cluster['f'] = np.append(cluster['f'],cluster2['f'][idx])
        cluster['cov_f'] = np.append(cluster['cov_f'],cluster2['cov_f'][idx])
        cluster['d'] = np.append(cluster['d'],cluster2['d'][idx])
        cluster['cov_d'] = np.append(cluster['cov_d'],cluster2['cov_d'][idx])
        cluster['mode_shapes'] = np.vstack((cluster['mode_shapes'],cluster2['mode_shapes'][idx,:]))
        cluster['MAC'] = np.append(cluster['MAC'],cluster2['MAC'][idx])
        cluster['model_order'] = np.append(cluster['model_order'],cluster2['model_order'][idx])
        cluster['row'] = np.append(cluster['row'],cluster2['row'][idx])
        cluster['col'] = np.append(cluster['col'],cluster2['col'][idx])
    return cluster
