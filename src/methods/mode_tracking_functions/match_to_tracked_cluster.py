from typing import Any, Dict, List
import numpy as np
from functions.calculate_mac import calculate_mac
# pylint:  disable=C0103, R0912, R0913, R0914, R0915, R0917, R1702

def match_cluster_to_tracked_cluster(cluster_dict: Dict[str,Any], tracked_clusters: Dict[str,Any],
                                     params: Dict[str,Any], result_pairs_prev: Dict[str,Any] = None,
                                     skip_cluster: List = None,
                                     skip_tracked_cluster: List = None) -> Dict[str,Any]:
    """
    Match clusters to tracked clusters

    The result dictionary consist of keys: cluster indecies,
    and values: indecies of tracked cluster to match with

    Example:
        Cluster 1 match with tracked cluster 2
        Cluster 2 match with tracked cluster 1
        Cluster 3 match with tracked cluster 1
        Cluster 4 match with "new", i.e. could not be matched with an existing tracked cluster

    Args:
        cluster_dict (dict): Dictionary of clusters
        tracked_clusters (dict): Previously tracked clusters
        params (dict): tracking parameters
        result_pairs_prev (dict): Dictionary of previous match result
        skip_cluster (list): List of clusters that are the optimal match with a tracked cluster
        skip_tracked_cluster (list): List of tracked clusters are an optimal match with a cluster

    Returns:
        result (dict): Dictionary of matches

    """
    result_pairs = {}
    for idx, key in enumerate(cluster_dict): #Go through all clusters
        if skip_cluster is not None:
            if result_pairs_prev is not None:
                if idx in skip_cluster: #If this cluster is already matched skip it
                    result_pairs[str(idx)] = result_pairs_prev[str(idx)]
                    continue

        #Get mode shapes
        cluster = cluster_dict[key]
        omega = cluster['median_f']
        phi_all = cluster['mode_shapes']

        MAC_list = []
        R_freq = []
        MAC_max_list = []
        for key_t in tracked_clusters: #Go through all tracked clusters.
            #They are identified with keys which are integers from 0 up to total number of clusters
            if key_t == 'iteration':
                pass
            elif skip_tracked_cluster is not None:
                if key_t in skip_tracked_cluster:
                    MAC_max_list.append(0)
                    R_freq.append(10**6)
            else:
                #Accessing all cluster in a tracked cluster group
                tracked_cluster_list = tracked_clusters[key_t]
                l = params.get('l_lastest_clusters',1) #Number of tracked clusters to compare with
                n_last_tracked_clusters = np.min((len(tracked_cluster_list),l))
                for ii in range(n_last_tracked_clusters):
                    tracked_cluster = tracked_cluster_list[-1*(ii+1)]

                    #phi of last cluster in tracked cluster group
                    phi_t_all = tracked_cluster['mode_shapes']

                    MAC_matrix = np.zeros((phi_all.shape[0],phi_t_all.shape[0]))
                    for kk, phi in enumerate(phi_all):
                        for jj, phi_t in enumerate(phi_t_all):
                            MAC = float(calculate_mac(phi_t, phi))
                            #array to compare the cluster with all tracked clusters
                            MAC_matrix[kk,jj] = MAC
                    if np.max(MAC_matrix) > params['phi_cri']:
                        break

                MAC_max = np.max(MAC_matrix) #Max MAC value between cluster and tracked cluster
                MAC_max_list.append(MAC_max)
                #median freq of last cluster in tracked cluster group
                tracked_cluster = tracked_cluster_list[-1]
                omega_t = tracked_cluster['median_f']
                #For cases where the tracked cluster has a frequency of 0
                omega_t = max(0.0001,omega_t)

                R_freq.append(abs(omega_t-omega)/omega_t) #Relative frequency difference

        #Find where the cluster matches the tracked cluster regarding the MAC criteria
        itemindex1 = np.argwhere(np.array(MAC_max_list) > params['phi_cri'])
        #Find where the cluster matches the tracked cluster regarding the MAC and frequency criteria
        itemindex = np.argwhere(np.array(R_freq)[itemindex1[:,0]] < params['freq_cri'])
        indicies = itemindex1[itemindex[:,0]]
        if len(indicies) > 1: #If two or more clusters combly with the criteria
            X_list = []
            R_f_list = []
            MAC_list = []
            for pos in indicies[:,0]:
                X = R_freq[pos]/MAC_max_list[pos] #Objective function
                X_list.append(X)
                R_f_list.append(R_freq[pos])
                MAC_list.append(MAC_max_list[pos])

            pos1 = X_list.index(min(X_list)) #Find the cluster that is most likely
            pos2 = MAC_list.index(max(MAC_list)) #Find the largest MAC
            pos3 = R_f_list.index(min(R_f_list)) #Find the smallest frequency difference
            #If one match on all three parameters:
            if pos2 == pos3:
                pos = int(indicies[pos1][0])
                result_pairs[str(idx)] = pos #group to a tracked cluster
            else:
                X_list_left = X_list.copy()
                del X_list_left[pos1]
                if isinstance(X_list_left,float):
                    X_list_left = [X_list_left]

                MAC_list_left = MAC_list.copy()
                del MAC_list_left[pos1]
                if isinstance(MAC_list_left,float):
                    MAC_list_left = [MAC_list_left]

                #Find the cluster that is most likely based on MAC
                pos2_2 = MAC_list_left.index(max(MAC_list_left))

                #Make different: abs(min(X_list_left)/min(X_list)) < params['obj_cri'] = 2
                #If the objective function results are close
                if abs(min(X_list_left)-min(X_list)) < params['obj_cri']:
                    #Cluster with the best MAC
                    if max(MAC_list_left) > max(MAC_list):
                        pos = int(indicies[pos2_2][0]) #Match with best MAC
                        result_pairs[str(idx)] = pos #group to a tracked cluster
                    else:
                        pos = int(indicies[pos2][0]) #Match with best X
                        result_pairs[str(idx)] = pos #group to a tracked cluster
                else: #If none of the above choose the one with lowest opjective function
                    pos = int(indicies[pos1][0])
                    result_pairs[str(idx)] = pos #group to a tracked cluster

        elif len(indicies) == 1: #If one cluster combly with the mode shape criteria
            pos = int(indicies[0][0])
            result_pairs[str(idx)] = pos #group to a tracked cluster

        else: #Does not comply with mode shape criteria
            result_pairs[str(idx)] = "new"

    return result_pairs
