from typing import Any
import numpy as np
from methods.packages.clustering import calculate_mac

# JVM 14/10/2025

def cluster_tracking(cluster_dict: dict[str,Any],tracked_clusters: dict[str,Any],Params: dict[str,Any]=None) -> dict[str,Any]:
    """
    Tracking of modes across experiments

    Args:
        cluster_dict (dict): Dictionary of clusters
        tracked_clusters (dict): Previously tracked clusters
        Params (dict): tracking parameters

    Returns:
        tracked_clusters (dict): Previously tracked clusters

    """
    print("Cluster tracking")
    if Params == None:
        Params = {'phi_cri':0.8,
                  'freq_cri':0.2}

    m_f = []
    for key in cluster_dict.keys():
        cluster = cluster_dict[key]
        m_f.append(cluster['median_f'])

    t_list = []
    t_length = []
    for key in tracked_clusters: #Go through all tracked clusters. They are identified with keys which are integers from 0 and up to total number of clusters
        if key == 'iteration':
            pass
        else:
            tracked_cluster_list = tracked_clusters[key] #Accessing all cluster in a tracked cluster group
            t_length.append(len(tracked_cluster_list))
            tracked_cluster = tracked_cluster_list[-1] #Accessing the last cluster for each tracked cluster group
            #median freq of last cluster in tracked cluster group
            t_list.append(tracked_cluster['median_f'])

    # No tracked clusters yet?
    if not tracked_clusters:
        first_track = 1
    else:
        first_track = 0

    if first_track == 1:
        for id, key in enumerate(cluster_dict.keys()):
            cluster = cluster_dict[key]
            cluster['id'] = 0

            tracked_clusters['iteration'] = 0
            tracked_clusters[str(id)] = [cluster]
    else:
        iter = tracked_clusters['iteration'] + 1
        tracked_clusters['iteration'] = iter

        result = match_cluster_to_tracked_cluster(cluster_dict,tracked_clusters,Params) #Match clusters to tracked clusters
    
        result_int = [] 
        for val in result.values(): #Get all non-"new" results
            if type(val) == int:
                result_int.append(val)

        if len(result_int) == len(set(result_int)): #If all clusters match with a unique tracked cluster
            for ii, key in enumerate(cluster_dict.keys()):
                cluster = cluster_dict[key]
                pos = result[str(ii)] #Find pos in result dict
                cluster['id'] = iter
                if pos == "new": #Add cluster as a new tracked cluster
                    new_key = len(tracked_clusters)-1 #-1 for "iteration", + 1 for next cluster and -1 for starting at 0 = -1
                    #print(f"new key: {new_key}")
                    tracked_clusters[str(new_key)] = [cluster]
                else: #Add cluster to an existing tracked cluster
                    cluster_to_add_to = tracked_clusters[str(pos)]
                    cluster_to_add_to.append(cluster)
                    tracked_clusters[str(pos)] = cluster_to_add_to

        else: #If there are some clusters that match with the same tracked cluster.
            kk = 0
            skip_tracked_cluster = []
            skip_cluster = []
            while len(result_int) != len(set(result_int)):
                kk += 1
                if kk > 10:                    
                    #Debug info:
                    unique_match_debug_info(result,cluster_dict,t_list)
                    print("Unresolved mode tracking")
                    breakpoint()

                for possible_match_id in set(result.values()): #Go through all unique values
                    if possible_match_id == "new": #Do nothing if "new"
                        pass
                    else:
                        test_if_str = np.argwhere(np.array(list(result.values())) == "new") #Test if "new" is present. If so, then we must match with str instead of int.
                        if len(test_if_str) > 0:
                            itemindex = np.argwhere(np.array(list(result.values())) == str(possible_match_id)) #Find the index of the unique cluster match
                        else:
                            itemindex = np.argwhere(np.array(list(result.values())) == possible_match_id) #Find the index of the unique cluster match
                        print(possible_match_id,np.array(list(result.values())),itemindex, len(itemindex))
                        
                        if len(itemindex) > 1: #If multiple clusters match to the same tracked cluster
                            pos, result, cluster_index = resolve_unique_matches(possible_match_id, itemindex, result, cluster_dict, tracked_clusters)
                            skip_tracked_cluster.append(str(result[str(cluster_index[pos])])) #Skip the best tracked cluster which is matced with another cluster.
                            skip_cluster.append(cluster_index[pos]) #Skip the best tracked cluster which is matced with another cluster.

                result = match_cluster_to_tracked_cluster(cluster_dict,tracked_clusters,Params,result,skip_cluster,skip_tracked_cluster) #Match with tracked clusters, but skip the already matched.

                #Debug info:
                unique_match_debug_info(result,cluster_dict,t_list)

                result_int = []
                for val in result.values():
                    if type(val) == int:
                        result_int.append(val)

            #Add the clusters to tracked clusters
            for ii, key in enumerate(cluster_dict.keys()): 
                cluster = cluster_dict[key]
                pos = result[str(ii)] #Find pos in result dict
                cluster['id'] = iter
                if pos == "new":
                    new_key = len(tracked_clusters)-1 #-1 for "iteration", + 1 for next cluster and -1 for starting at 0 = -1
                    tracked_clusters[str(new_key)] = [cluster]
                else:
                    cluster_to_add_to = tracked_clusters[str(pos)]
                    cluster_to_add_to.append(cluster)
                    tracked_clusters[str(pos)] = cluster_to_add_to



    return tracked_clusters

def match_cluster_to_tracked_cluster(cluster_dict: dict[str,Any], tracked_clusters: dict[str,Any], Params: dict[str,Any], result_prev: dict[str,Any] = {},skip_cluster: list = [], skip_tracked_cluster: list = []) -> dict[str,Any]:
    """
    Match clusters to tracked clusters

    The result dictionary consist of keys: cluster indecies, and values: indecies of tracked cluster to match with
    Example:
        Cluster 1 match with tracked cluster 2
        Cluster 2 match with tracked cluster 1
        Cluster 3 match with tracked cluster 1
        Cluster 4 match with "new", i.e. could not be matched with an existing tracked cluster

    Args:
        cluster_dict (dict): Dictionary of clusters
        tracked_clusters (dict): Previously tracked clusters
        Params (dict): tracking parameters
        result_prev (dict): Dictionary of previous match result
        skip_cluster (list): List of clusters that have proven they are a optimal match with a tracked cluster
        skip_tracked_cluster (list): List of tracked clusters that have an optimal match with a cluster

    Returns:
        result (dict): Dictionary of matches

    """
    result = {}
    for id, key in enumerate(cluster_dict): #Go through all clusters
        if id in skip_cluster: #If this cluster is already matched skip it
            result[str(id)] = result_prev[str(id)]
            continue

        #Get mode shapes
        cluster = cluster_dict[key]
        omega = cluster['median_f']
        phi = cluster['mode_shapes'][0]
        phi_all = cluster['mode_shapes']

        Xres = []
        MAC_list = []
        D_freq = []
        omega_t_list = []
        MAC_max_list = []
        MAC_avg_list = []
        for key in tracked_clusters: #Go through all tracked clusters. They are identified with keys which are integers from 0 and up to total number of clusters
            if key == 'iteration':
                pass
            else:
                tracked_cluster_list = tracked_clusters[key] #Accessing all cluster in a tracked cluster group
                tracked_cluster = tracked_cluster_list[-1] #Accessing the last cluster for each tracked cluster group
                omega_t = tracked_cluster['median_f'] #median freq of last cluster in tracked cluster group
                omega_t_list.append(omega_t)
                phi_t_all = tracked_cluster['mode_shapes'] #phi of last cluster in tracked cluster group
                phi_t = phi_t_all[0]

                MAC_list.append(float(calculate_mac(phi_t, phi)))

                MACs = np.zeros((phi_all.shape[0],phi_t_all.shape[0]))
                for ii, phi in enumerate(phi_all):
                    for jj, phi_t in enumerate(phi_t_all):
                        MAC = float(calculate_mac(phi_t, phi))
                        MACs[ii,jj] = MAC #Compare the cluster with all tracked clusters

                if key in skip_tracked_cluster:
                    MAC_avg = np.mean(0)
                    MAC_max = np.max(0)
                    MAC_max_list.append(0)
                    MAC_avg_list.append(0)
                    D_freq.append(10**6)
                else:
                    MAC_avg = np.mean(MACs)
                    MAC_max = np.max(MACs)
                    MAC_max_list.append(MAC_max)
                    MAC_avg_list.append(MAC_avg)
                    D_freq.append(abs(omega_t-omega)/omega)
                
        itemindex1 = np.argwhere(np.array(MAC_max_list) > Params['phi_cri']) #Find where the cluster matches the tracked cluster regarding the MAC criteria
        itemindex = np.argwhere(np.array(D_freq)[itemindex1[:,0]] < Params['freq_cri']) #Find where the cluster matches the tracked cluster regarding the MAC and frequency criteria
        indicies = itemindex1[itemindex[:,0]]
        if len(indicies) > 1: #If two or more clusters combly with the mode shape criteria
            Xres = []
            Xres_f = []
            Xres_MAC = []
            for nn in indicies:
                pos = nn[0]
                X = D_freq[pos]/MAC_max_list[pos] #Objective function
                Xres.append(X)
                Xres_f.append(D_freq[pos])
                Xres_MAC.append(MAC_max_list[pos])

            if Xres != []: # One or more cluster(s) combly with the frequency criteria
                pos1 = Xres.index(min(Xres)) #Find the cluster that is most likely
                pos2 = Xres_MAC.index(max(Xres_MAC)) #Find the largest MAC
                pos3 = Xres_f.index(min(Xres_f)) #Find the smallest frequency difference
                
                if len(Xres) > 1: #If more than one cluster comply with criteria
                    Xres_left = Xres.copy()
                    del Xres_left[pos1]
                    if type(Xres_left) == np.float64:
                        Xres_left = [Xres_left]

                    Xres_MAC_left = Xres_MAC.copy()
                    del Xres_MAC_left[pos1]
                    if type(Xres_MAC_left) == np.float64:
                        Xres_MAC_left = [Xres_MAC_left]

                    Xres_f_left = Xres_f.copy()
                    del Xres_f_left[pos1]
                    if type(Xres_f_left) == np.float64:
                        Xres_f_left = [Xres_f_left]

                    pos1_2 = Xres_left.index(min(Xres_left)) #Find the cluster that is most likely
                    pos2_2 = Xres_MAC_left.index(max(Xres_MAC_left)) #Find the cluster that is most likely based on MAC
                    pos3_2 = Xres_f_left.index(min(Xres_f_left)) #Find the cluster that is most likely based on Freq

                if (pos1 == pos2) and (pos1 == pos3): #If one match on all three parameters: objective function, max MAC and frequency difference
                    pos = int(indicies[pos1][0])
                    result[str(id)] = pos #group to a tracked cluster
                
                #Make different: abs(min(Xres_left)/min(Xres)) < Params['obj_cri'] = 2
                elif abs(min(Xres_left)-min(Xres)) < Params['obj_cri']: #If the objective function results are close
                    if (min(Xres_f) < Params['freq_cri']) and (min(Xres_f_left) < Params['freq_cri']): #If both frequency differences are close to the target cluster
                        pos = int(indicies[pos2_2][0]) #Match with best MAC
                        result[str(id)] = pos #group to a tracked cluster
                    elif (min(Xres_f) < Params['freq_cri']) and (min(Xres_f_left) > Params['freq_cri']): #If Xres_f is smaller than the threshold
                        pos = int(indicies[pos3][0]) #Match with lowest frequency difference
                        result[str(id)] = pos #group to a tracked cluster
                    elif (min(Xres_f) > Params['freq_cri']) and (min(Xres_f_left) < Params['freq_cri']):
                        pos = int(indicies[pos3_2][0]) #Match with lowest frequency difference
                        result[str(id)] = pos #group to a tracked cluster
                    else: #If none of the above choose the one with highest MAC
                        pos = int(indicies[pos2_2][0])
                        result[str(id)] = pos #group to a tracked cluster
                else: #If none of the above choose the one with lowest onjective function
                    pos = int(indicies[pos1][0])
                    result[str(id)] = pos #group to a tracked cluster
    
            else:  #No cluster comply with frequency criteria, so a new cluster is saved
                result[str(id)] = "new"
    
        elif len(indicies) == 1: #If one cluster combly with the mode shape criteria
            pos = int(indicies[0][0])
            result[str(id)] = pos #group to a tracked cluster

        else: #Does not comply with mode shape criteria
            result[str(id)] = "new"
    
    return result

def resolve_unique_matches(possible_match_id, itemindex, result, cluster_dict, tracked_clusters):
    """
    Resolve if two clusters match with the same tracked cluster. Determine what match is the most optimal.
    Those clusters that does not have an optimal match, they are given the match result = "new"

    Example:
        Cluster 2 match with tracked cluster 1
        Cluster 3 match with tracked cluster 1

    Args:
        possible_match_id (int): The index of tracked cluster
        itemindex (np.ndarray): The indecies of clusters that have the same match
        result (dict): Dictionary of suggested matches
        cluster_dict (dict): Dictionary of clusters
        tracked_clusters (dict): Previously tracked clusters

    Returns:
        pos (int): Value of cluster that have the most optimal match.
        result (dict): Dictionary of re-done matches
        cluster_index: The indecies of clusters that have the same match

    """
    mean_MAC = []
    keys = [str(y[0]) for y in itemindex.tolist()] #Make keys for dictionary based on indices in itemindex
    for nn in itemindex: #Go through possible clusters match index
        cluster = cluster_dict[int(nn[0])]
        phi_all = cluster["mode_shapes"] #Find mode shapes in cluster
        tracked_cluster_list = tracked_clusters[str(possible_match_id)] #Accessing all cluster in a tracked cluster group
        tracked_cluster = tracked_cluster_list[-1] #Accessing the last cluster for each tracked cluster group
        phi_t_all = tracked_cluster['mode_shapes'] #Find mode shapes in tracked cluster
        
        #Make list of mode shapes have the same length, i.e. same number of poles
        if len(phi_all) > len(phi_t_all):
            phi_all = phi_all[0:len(phi_t_all)]
        elif len(phi_all) < len(phi_t_all):
            phi_t_all = phi_t_all[0:len(phi_all)]
        else: #Equal length
            pass
        MAC_matrix = np.zeros((len(phi_all),len(phi_all))) #Initiate a matrix of MAC values
        for ii, phi in enumerate(phi_all):
            for jj, phi_t in enumerate(phi_t_all):
                MAC_matrix[ii,jj] = calculate_mac(phi,phi_t) #Mac

        mean_MAC.append(np.mean(MAC_matrix)) #Save the mean values of MAC from this cluster compared to the matched tracked cluster
    pos = mean_MAC.index(max(mean_MAC)) #Find the index with higest mean MAC, i.e. the cluster that match best with the tracked cluster.
    
    cluster_index = itemindex[:,0]

    for key in keys:
        if keys[pos] == key: #Let the best cluster match stay
            pass
        else: #Add the clusters with the worst match as a new cluster
            result[key] = "new"
    return pos, result, cluster_index

def unique_match_debug_info(result,cluster_dict,t_list):
    """
    Debug info

    Args:
        result (dict): Dictionary of matches
        cluster_dict (dict): Dictionary of clusters
        t_list (list): List of median frequencies of last tracked tracked clusters

    Returns:

    """
    print('\n')
    for ii, key in enumerate(cluster_dict.keys()):
        cluster = cluster_dict[key]
        pos = result[str(ii)] #Find pos in result dict
        if pos == "new":
            print(cluster_dict[key]['median_f'],str(ii),pos)
        else:
            print(cluster_dict[key]['median_f'],str(ii),pos,t_list[pos])