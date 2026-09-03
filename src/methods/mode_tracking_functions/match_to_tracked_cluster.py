from typing import Any, Dict, List
import numpy as np
from functions.calculate_mac import calculate_mac
from methods.mode_tracking_functions.mahalanobis import MSD, construct_x
np.set_printoptions(formatter={'float':"{0:0.5f}".format})
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
    if skip_tracked_cluster is None:
        skip_tracked_cluster = []

    l = params.get('l_lastest_clusters',1) #Number of tracked clusters to compare with
    #Calculate parameters for tracked clusters that are universal for all comparisons.
    greatest_interval_f = []
    greatest_interval_d = []
    zeta_t_mean_list = []
    f_mean = []
    muX_list = []
    covX_list = []
    for key_t in tracked_clusters: #Go through all tracked clusters.
        #They are identified with keys which are integers from 0 up to total number of clusters
        if key_t == 'iteration':
            pass
        elif key_t in skip_tracked_cluster:
            greatest_interval_f.append([-1,-1])
            greatest_interval_d.append([-1,-1])
        else:
            #Accessing all cluster in a tracked cluster group
            tracked_cluster_list = tracked_clusters[key_t]

            #Mahalanobis
            mu = tracked_cluster_list[-1]["MSD_muX"]
            muX_list.append(mu)
            covX_list.append(tracked_cluster_list[-1]["MSD_cov"])


    #Calculate parameters that are relative to the new cluster
    result_pairs = {}
    for idx, key in enumerate(cluster_dict): #Go through all clusters
        if skip_cluster is not None:
            if result_pairs_prev is not None:
                if idx in skip_cluster: #If this cluster is already matched skip it
                    result_pairs[str(idx)] = result_pairs_prev[str(idx)]
                    continue

        cluster = cluster_dict[key]
        omega = cluster['median_f']
        zeta = cluster['median_d']
        phi_all = cluster['mode_shapes']
        x = construct_x(cluster,params)

        MAC_list = []
        R_freq = []
        R_damp = []
        MAC_max_list = []
        t_test_list = []
        t_list = []
        R_iteration_diff = []
        msd_list = []
        id_list = []
        MSD_mask_list = []
        history_mask_list = []
        counter = -1
        for key_t in tracked_clusters: #Go through all tracked clusters.
            #They are identified with keys which are integers from 0 up to total number of clusters
            
            if key_t == 'iteration':
                iteration = tracked_clusters[key_t]
                pass

            elif (key_t in skip_tracked_cluster) or (abs(tracked_clusters[key_t][-1]['median_f']-omega)/omega > 0.25):
                MAC_max_list.append(0)
                R_freq.append(10**6)
                R_damp.append(10**6)
                id_list.append(-1)
                R_iteration_diff.append(100)
                msd_list.append(10**6)
                t_test_list.append(False)
                t_list.append(0)
                MSD_mask_list.append(False)
                history_mask_list.append(False)
                counter += 1
            else:
                counter += 1
                #Accessing all cluster in a tracked cluster group
                tracked_cluster_list = tracked_clusters[key_t]
                t_list.append(tracked_cluster_list[-1]['median_f'])
                omega_t = tracked_cluster_list[-1]['median_f']
                zeta_t = tracked_cluster_list[-1]['median_d']
                id_list.append(tracked_cluster_list[-1]['id'])

                MAC_max = 0
                for ii in range(len(tracked_cluster_list)):
                    tracked_cluster = tracked_cluster_list[-1*(ii+1)]
                    
                    #phi of last cluster in tracked cluster group
                    phi_t_all = tracked_cluster['mode_shapes']
                    for kk, phi in enumerate(phi_all):
                        for jj, phi_t in enumerate(phi_t_all):
                            MAC = float(calculate_mac(phi_t, phi))
                            #array to compare the cluster with all tracked clusters
                            if MAC > MAC_max:
                                MAC_max = MAC

                MAC_max_list.append(MAC_max)

                last_tracked_cluster = tracked_cluster_list[-1]
                iteration_t = last_tracked_cluster['id']

                #For cases where the tracked cluster has a frequency of 0
                R_freq.append(abs(omega_t-omega)/omega_t) #Relative frequency difference
                R_damp.append(abs(zeta_t-zeta)/zeta_t)
                R_iteration_diff.append(abs(iteration_t-iteration)/iteration) #Relative iterration difference

                muX = muX_list[counter]
                covX = covX_list[counter]

                d2, t = MSD(muX,covX,x,cluster["global_std"]**2,muX.shape[0],alpha=params['alpha'])
                msd_list.append(d2)
                print(muX[0],d2,t)
                if d2 < t:
                    MSD_mask_list.append(True)
                else:
                    MSD_mask_list.append(False)
        
        MSD_mask = np.array(MSD_mask_list)
        mac_match_mask = np.array(MAC_max_list) > params['phi_cri']

        match_mask = mac_match_mask
        match_mask = np.logical_and(match_mask,MSD_mask)
        match_indicies = np.argwhere(match_mask==True).reshape(-1)

        print("\n",omega)
        print(np.argwhere(mac_match_mask==True).reshape(-1),"mac criteria")
        print(np.argwhere(MSD_mask==True).reshape(-1),"MSD")
        print(np.argwhere(match_mask==True).reshape(-1),"Commom matches")
        print(np.array(t_list)[np.argwhere(match_mask==True).reshape(-1)],"omega")
        print(np.array(MAC_max_list)[np.argwhere(match_mask==True).reshape(-1)],"MACs")
        print(np.array(id_list)[np.argwhere(match_mask==True).reshape(-1)],"id")
        print("\n")
        
        # match_indicies = item_indices
        if len(match_indicies) > 1: #If two or more clusters combly with the criteria
            X_list = []
            R_f_list = []
            R_d_list = []
            MAC_list = []
            for pos in match_indicies:
                
                # X = (R_freq[pos]**2+(1-MAC_max_list[pos])**2+R_damp[pos]**2+R_iteration_diff[pos]**2)**0.5 #Objective function
                X = (R_freq[pos]**2+(1-MAC_max_list[pos])**2+R_damp[pos]**2)**0.5 #Objective function
                print(t_list[pos],"id",id_list[pos],"rel_iteration",R_iteration_diff[pos],"rel_f",R_freq[pos],"rel_d",R_damp[pos],"MAC",MAC_max_list[pos],"score",X,"MSD",msd_list[pos])
                X_list.append(X)
                R_f_list.append(R_freq[pos])
                R_d_list.append(R_damp[pos])
                MAC_list.append(MAC_max_list[pos])

            pos1 = X_list.index(min(X_list)) #Find the cluster that is most likely
            pos2 = MAC_list.index(max(MAC_list)) #Find the largest MAC
            pos3 = R_f_list.index(min(R_f_list)) #Find the smallest frequency difference
            pos4 = R_d_list.index(min(R_d_list))
            print(t_list[pos],pos1,pos2,pos3,pos4)
            #If one match on all three parameters:
            if (pos2 == pos3) and (pos2 == pos4):
                pos = int(match_indicies[pos1])
                result_pairs[str(idx)] = pos #group to a tracked cluster
            else:
                pos = int(match_indicies[pos2]) #Match with best MAC
                result_pairs[str(idx)] = pos

        elif len(match_indicies) == 1: #If one cluster combly with the mode shape criteria
            pos = int(match_indicies[0])
            result_pairs[str(idx)] = pos #group to a tracked cluster
        else: #Does not comply with mode shape criteria
            result_pairs[str(idx)] = "new"

    return result_pairs