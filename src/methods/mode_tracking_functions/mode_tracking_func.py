from typing import Any, Dict
import numpy as np
from methods.mode_tracking_functions.match_to_tracked_cluster import (
    match_cluster_to_tracked_cluster)
from methods.mode_tracking_functions.resolve_nonunique_matches import (
    resolve_nonunique_matches)
from functions.calculate_mac import calculate_mac
from methods.mode_tracking_functions.mahalanobis import MSD, construct_x
# pylint: disable=C0103, R0914, R0915, R0912, R1702
# JVM 22/10/2025

def cluster_tracking(cluster_dict: Dict[str,Any],tracked_clusters: Dict[str,Any],
                     params: Dict[str,Any] = None) -> Dict[str,Any]:
    """
    Tracking of modes across experiments

    Args:
        cluster_dict (Dict[str,Any]): Dictionary of clusters
        tracked_clusters (Dict[str,Any]): Previously tracked clusters
        params (Dict[str,Any]): tracking parameters

    Returns:
        tracked_clusters (Dict[str,Any]): Previously tracked clusters

    """
    if params is None:
        params = {'phi_cri':0.8,
                  'freq_cri':0.2}
    else:
        params['phi_cri'] = params.get('phi_cri',0.8)
        params['freq_cri'] = params.get('freq_cri',0.2)

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
            cluster['MSD_muX'] = np.array((cluster['median_f'],cluster['median_d'])).reshape(-1,1)
            cluster["MSD_cov"] = cluster['global_std']**2

            tracked_clusters['iteration'] = 0
            tracked_clusters[str(idx)] = [cluster]
    else:
        iteration = tracked_clusters['iteration'] + 1
        tracked_clusters['iteration'] = iteration

        #Match clusters to tracked clusters
        result = match_cluster_to_tracked_cluster(cluster_dict,tracked_clusters,params)

        result_int = []
        for val in result.values(): #Get all non-"new" results
            if isinstance(val,int):
                result_int.append(val)

        #If all clusters match with a unique tracked cluster
        if len(result_int) == len(set(result_int)):
            tracked_clusters = add_clusters_to_tracked_clusters(cluster_dict,tracked_clusters,result,iteration,params)
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
                    else:
                        #Test if "new" is present.
                        # If so, then we must match with str instead of int.
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
                            pos, result = resolve_nonunique_matches(
                                possible_match_id, itemindex, result, cluster_dict,
                                tracked_clusters)
                            #Skip the best tracked cluster which is matced with another cluster.
                            cluster_index = itemindex[:,0] # The indecies of clusters that have
                                                            # the same match (formatted)
                            skip_tracked_cluster.append(str(result[str(cluster_index[pos])]))
                            #Skip the best tracked cluster which is matced with another cluster.
                            skip_cluster.append(cluster_index[pos])
                #Match with tracked clusters, but skip the already matched.
                print("\nSecond round matching")
                print("Skipped",skip_tracked_cluster)
                result = match_cluster_to_tracked_cluster(cluster_dict,
                                                          tracked_clusters,params,
                                                          result,skip_cluster,
                                                          skip_tracked_cluster)
                result_int = []
                for val in result.values():
                    if isinstance(val,int):
                        result_int.append(val)

            #Add the clusters to tracked clusters
            tracked_clusters = add_clusters_to_tracked_clusters(cluster_dict,tracked_clusters,result,iteration,params)


        tracked_clusters = MSD_align_tracked_clusters(tracked_clusters,params)
        
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

def add_clusters_to_tracked_clusters(cluster_dict,tracked_clusters,result,iteration,params):
    """
    Add a cluster to a tracked cluster group and apply MSD information
    Args:

    Returns:

    """
    for ii, key in enumerate(cluster_dict.keys()):
        cluster = cluster_dict[key]
        pos = result[str(ii)] #Find pos in result dict
        cluster['id'] = iteration
        if pos == "new":
            cluster['MSD_muX'] = np.array((cluster['median_f'],cluster['median_d'])).reshape(-1,1)
            cluster["MSD_cov"] = cluster["global_std"]**2
            new_key = len(tracked_clusters)-1
            # Why -1? -1 for "iteration" which is not a cluster,
            # + 1 for adding a new cluster and -1 for starting at 0 = -1
            tracked_clusters[str(new_key)] = [cluster]
        else:
            cluster_to_add_to = tracked_clusters[str(pos)]
            len_c = len(cluster_to_add_to)
            mu = cluster_to_add_to[-1]['MSD_muX']
            x = np.array((cluster['median_f'],cluster['median_d'])).reshape(-1,1)
            Xx = construct_x(cluster_to_add_to,params)
            cluster["MSD_cov"] = np.cov(np.hstack((Xx,x))) #Apply information regarding the covariance of the full tracked cluster group
            cluster['MSD_muX'] = mu + (1/(len_c+1))*(x-mu) #Update mean vector
            cluster_to_add_to.append(cluster)
            tracked_clusters[str(pos)] = cluster_to_add_to
    return tracked_clusters

def MSD_align_tracked_clusters(tracked_clusters, params):
    """
    Align tracked clusters in time.
    If the tracked cluster group contains two or more clusters we look for possible alignment to other tracked cluster groups.
    Args:
        tracked_clusters (dict[str,Any]): Dictionary of all tracked cluster groups
        params (dict[str,Any]): Parameters
    Returns:
        tracked_clusters (dict[str,Any]): Dictionary of all tracked cluster groups
    """
    print("\n --Tracked cluster alignment--")

    #Sort tracked clusters by length
    tracked_cluster_keys_sorted_by_size = []
    counter = -1
    for t_key in tracked_clusters:
        if t_key != "iteration":
            counter += 1
            if len(tracked_cluster_keys_sorted_by_size) < 1:
                tracked_cluster_keys_sorted_by_size.append(t_key)
            else:
                keys_for_loop = tracked_cluster_keys_sorted_by_size
                for ii, sorted_key in enumerate(keys_for_loop):
                    already_sorted_t_cluster = tracked_clusters[sorted_key]
                    if len(already_sorted_t_cluster) > len(tracked_clusters[t_key]):
                        tracked_cluster_keys_sorted_by_size.insert(ii,t_key)
                        break
                    elif ii == len(keys_for_loop):
                        tracked_cluster_keys_sorted_by_size.append(t_key)

    t_ids_list = []
    muX_list = []
    covX_list = []
    X_len_list = []
    for t_key in tracked_clusters:
        if t_key != "iteration":
            t_cluster = tracked_clusters[t_key]
            t_ids = []
            for cluster in t_cluster:
                t_ids.append(cluster['id'])
            t_ids_list.append(t_ids)

            mu = t_cluster[-1]["MSD_muX"]
            muX_list.append(mu)
            covX_list.append(t_cluster[-1]["MSD_cov"])
            X_len_list.append(len(t_cluster))
            
    size_order_int = [int(key) for key in tracked_cluster_keys_sorted_by_size]
    t_ids_list_sorted = []
    for ii in size_order_int:
        t_ids_list_sorted.append(t_ids_list[ii])

    i_counter = -1
    delete_tracked = []
    prev_tracked_clusters = tracked_clusters.copy()
    for t_key in prev_tracked_clusters:
        if t_key == "iteration":
            iteration = prev_tracked_clusters[t_key]
        elif iteration > 1:
            i_counter += 1
            t_ids_main = set(t_ids_list[i_counter])

            if (t_key not in delete_tracked):
                t_cluster = prev_tracked_clusters[t_key]
                if (len(t_cluster) > 1):
                    mf_1 = []
                    md_1 = []
                    for cluster in t_cluster:
                        mf_1.append(cluster["median_f"])
                        md_1.append(cluster["median_d"])
                    x = construct_x(t_cluster,params)

                    d2_min = []
                    t = 10**6
                    id_to_match_list = []
                    max_MAC_list = []
                    for ii, muX in enumerate(muX_list):
                        t_ids_second = set(t_ids_list[ii])
                        if (str(ii) not in delete_tracked) and (len(t_ids_second)>1) and (len(t_ids_main)>len(t_ids_second)):
                            d2_list = []
                            m_f = muX[0]
                            if (abs(np.mean(mf_1)-np.mean(m_f))/np.mean(m_f) < 0.25): #Only search through near clusters
                                print("length",len(t_cluster),t_cluster[0]['median_f'],"iteration",iteration)
                                if len(t_ids_main.intersection(t_ids_second)) == 0: #No clusters must intersect in time
                                    for jj in range(x.shape[1]): #Calculate MSD for each clusters in the possible tracked cluster alignment
                                        y = x[:,jj].reshape(-1,1)
                                        chi_dof = X_len_list[ii]
                                        covX = covX_list[ii]
                                        d2, t = MSD(muX,covX,y,t_cluster[jj]["global_std"]**2,chi_dof,alpha=params['alpha'])
                                        d2_list.append(d2)
                                    print("f",t_cluster[-1]['median_f'],"id",len(t_cluster),"f",prev_tracked_clusters[str(ii)][-1]['median_f'],"id",len(prev_tracked_clusters[str(ii)]),"avg d2",np.mean(d2_list),"max d2",max(d2_list),"min d2",min(d2_list))
                                    if np.min(d2_list) < t:
                                        id_to_match = ii
                                        phi_all = t_cluster[-1]['mode_shapes']
                                        t_key_second = str(id_to_match)
                                        t_ids_second = set(t_ids_list[id_to_match])
                                        t_cluster_second = prev_tracked_clusters[t_key_second]
                                        phi_t_all = t_cluster_second[-1]['mode_shapes']
                                        MAC_max = 0
                                        for phi in phi_all:
                                            for phi_t in phi_t_all:
                                                MAC = float(calculate_mac(phi_t, phi))
                                                #array to compare the cluster with all tracked clusters
                                                if MAC > MAC_max:
                                                    MAC_max = MAC
                                        print('mac',MAC_max)
                                        if (MAC_max > params['phi_cri']):
                                            d2_min.append(np.min(d2_list))
                                            id_to_match_list.append(id_to_match)
                                            max_MAC_list.append(MAC_max)
                                        else:
                                            d2_min.append(10**6)

                    print(d2_min)
                    if len(np.argwhere(np.array(d2_min) < t)) > 0: # Merge the two alligned clusters
                        max_MAC = 0
                        for ii, kk in enumerate(id_to_match_list): #Align only clusters with the best MAC criteria
                            t_key_second = str(kk)
                            t_cluster_second = prev_tracked_clusters[t_key_second]
                            if max_MAC_list[ii] > max_MAC:
                                id_to_match = kk
                        t_key_second = str(id_to_match)
                        t_ids_second = set(t_ids_list[id_to_match])
                        t_cluster_second = prev_tracked_clusters[t_key_second]
                        union_set = t_ids_main | t_ids_second
                        union_set = sorted(union_set)
                        merged = []
                        ll = 0
                        oo = 0
                        for set_val in union_set:
                            if set_val in t_ids_main:
                                merged.append(tracked_clusters[t_key][ll])
                                ll += 1
                            elif set_val in t_ids_second:
                                merged.append(tracked_clusters[t_key_second][oo])
                                oo += 1
                        if ll >= oo:
                            tracked_clusters[t_key] = merged
                            delete_tracked.append(t_key_second)
                            t_ids_list[i_counter] = list(union_set)
                        else:
                            tracked_clusters[t_key_second] = merged
                            delete_tracked.append(t_key)
                            t_ids_list[int(t_key_second)] = list(union_set)
                        continue

    if delete_tracked != []: #Delete aligned groups
        for del_key in delete_tracked:
            tracked_clusters.pop(del_key)
        old_tracked_clusters = tracked_clusters.copy()
        tracked_clusters = {'iteration': old_tracked_clusters['iteration']}
        for pp, key in enumerate(old_tracked_clusters):
            if key != "iteration":
                tracked_clusters[str(pp-1)] = old_tracked_clusters[key]
    
    return tracked_clusters