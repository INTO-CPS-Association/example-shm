from typing import Any, Dict
import numpy as np
from methods.mode_tracking_functions.match_to_tracked_cluster import match_cluster_to_tracked_cluster
from methods.mode_tracking_functions.resolve_nonunique_matches import resolve_nonunique_matches
# JVM 22/10/2025

def cluster_tracking(cluster_dict: Dict[str, Any], tracked_clusters: Dict[str, Any], Params: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Tracking of modes across experiments

    Args:
        cluster_dict (dict): Dictionary of clusters
        tracked_clusters (dict): Previously tracked clusters
        Params (dict): tracking parameters

    Returns:
        tracked_clusters (dict): Previously tracked clusters

    """
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
                    raise("Unresolved mode tracking")

                for possible_match_id in set(result.values()): #Go through all unique values
                    if possible_match_id == "new": #Do nothing if "new"
                        pass
                    else:
                        test_if_str = np.argwhere(np.array(list(result.values())) == "new") #Test if "new" is present. If so, then we must match with str instead of int.
                        if len(test_if_str) > 0:
                            itemindex = np.argwhere(np.array(list(result.values())) == str(possible_match_id)) #Find the index of the unique cluster match
                        else:
                            itemindex = np.argwhere(np.array(list(result.values())) == possible_match_id) #Find the index of the unique cluster match
                        
                        if len(itemindex) > 1: #If multiple clusters match to the same tracked cluster
                            pos, result, cluster_index = resolve_nonunique_matches(possible_match_id, itemindex, result, cluster_dict, tracked_clusters)
                            skip_tracked_cluster.append(str(result[str(cluster_index[pos])])) #Skip the best tracked cluster which is matced with another cluster.
                            skip_cluster.append(cluster_index[pos]) #Skip the best tracked cluster which is matced with another cluster.

                result = match_cluster_to_tracked_cluster(cluster_dict,tracked_clusters,Params,result,skip_cluster,skip_tracked_cluster) #Match with tracked clusters, but skip the already matched.

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