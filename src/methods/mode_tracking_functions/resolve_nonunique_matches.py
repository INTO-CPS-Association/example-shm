from typing import Any
import numpy as np
from functions.calculate_mac import calculate_mac

def resolve_nonunique_matches(possible_match_id, itemindex, result, cluster_dict, tracked_clusters):
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