from typing import Any
import numpy as np
from methods.mode_tracking_functions.match_to_tracked_cluster import (
    match_cluster_to_tracked_cluster)
from methods.mode_tracking_functions.resolve_nonunique_matches import (
    resolve_nonunique_matches)
# pylint: disable=C0103
# JVM 22/10/2025

def cluster_tracking(cluster_dict: dict[str,Any],tracked_clusters: dict[str,Any],
                     Params: dict[str,Any] = None) -> dict[str,Any]:
    """
    Tracking of modes across experiments

    Args:
        cluster_dict (dict): Dictionary of clusters
        tracked_clusters (dict): Previously tracked clusters
        Params (dict): tracking parameters

    Returns:
        tracked_clusters (dict): Previously tracked clusters

    """
    if Params is None:
        Params = {'phi_cri':0.8,
                  'freq_cri':0.2}

    m_f = []
    for key in cluster_dict.keys():
        cluster = cluster_dict[key]
        m_f.append(cluster['median_f'])

    t_list = []
    t_length = []
    for key in tracked_clusters: #Go through all tracked clusters.
        # They are identified with keys which are integers from 0 and up to total number of clusters
        if key == 'iteration':
            pass
        else:
            #Accessing all cluster in a tracked cluster group
            tracked_cluster_list = tracked_clusters[key]
            t_length.append(len(tracked_cluster_list))
            #Accessing the last cluster for each tracked cluster group
            tracked_cluster = tracked_cluster_list[-1]
            #median freq of last cluster in tracked cluster group
            t_list.append(tracked_cluster['median_f'])

    # No tracked clusters yet?
    if not tracked_clusters:
        for idx, key in enumerate(cluster_dict.keys()):
            cluster = cluster_dict[key]
            cluster['id'] = 0

            tracked_clusters['iteration'] = 0
            tracked_clusters[str(idx)] = [cluster]
    else:
        iteration = tracked_clusters['iteration'] + 1
        tracked_clusters['iteration'] = iteration

        #Match clusters to tracked clusters
        result = match_cluster_to_tracked_cluster(cluster_dict,tracked_clusters,Params)

        result_int = []
        for val in result.values(): #Get all non-"new" results
            if isinstance(val,int):
                result_int.append(val)

        #If all clusters match with a unique tracked cluster
        if len(result_int) == len(set(result_int)):
            for ii, key in enumerate(cluster_dict.keys()):
                cluster = cluster_dict[key]
                pos = result[str(ii)] #Find pos in result dict
                cluster['id'] = iteration
                if pos == "new": #Add cluster as a new tracked cluster
                    new_key = len(tracked_clusters)-1
                    # why -1? -1 for "iteration", + 1 for next cluster and -1 for starting at 0 = -1
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
                    raise RuntimeError("Unresolved mode tracking")

                for possible_match_id in set(result.values()): #Go through all unique values
                    if possible_match_id == "new": #Do nothing if "new"
                        pass
                    #Test if "new" is present. If so, then we must match with str instead of int.
                    else:
                        test_if_str = np.argwhere(
                            np.array(list(result.values())) == "new")
                        if len(test_if_str) > 0: #Find the index of the unique cluster match
                            itemindex = np.argwhere(
                                np.array(list(result.values())) == str(possible_match_id))
                        else: #Find the index of the unique cluster match
                            itemindex = np.argwhere(
                                np.array(list(result.values())) == possible_match_id)

                        #If multiple clusters match to the same tracked cluster
                        if len(itemindex) > 1:
                            pos, result, cluster_index = resolve_nonunique_matches(
                                possible_match_id, itemindex, result, cluster_dict,
                                tracked_clusters)
                            #Skip the best tracked cluster which is matced with another cluster.
                            skip_tracked_cluster.append(str(result[str(cluster_index[pos])]))
                            #Skip the best tracked cluster which is matced with another cluster.
                            skip_cluster.append(cluster_index[pos])
                #Match with tracked clusters, but skip the already matched.
                result = match_cluster_to_tracked_cluster(cluster_dict,
                                                          tracked_clusters,Params,
                                                          result,skip_cluster,
                                                          skip_tracked_cluster)
                result_int = []
                for val in result.values():
                    if isinstance(val,int):
                        result_int.append(val)

            #Add the clusters to tracked clusters
            for ii, key in enumerate(cluster_dict.keys()):
                cluster = cluster_dict[key]
                pos = result[str(ii)] #Find pos in result dict
                cluster['id'] = iteration
                if pos == "new":
                    new_key = len(tracked_clusters)-1
                    #Why -1? -1 for "iteration", + 1 for next cluster and -1 for starting at 0 = -1
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
            print(cluster['median_f'],str(ii),pos)
        else:
            print(cluster['median_f'],str(ii),pos,t_list[pos])
