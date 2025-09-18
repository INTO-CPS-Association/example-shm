import matplotlib.pyplot as plt
import numpy as np
from methods.packages.clustering import calculate_mac
from typing import Any, NoReturn

def cluster_tracking(cluster_dict: dict[str,dict],tracked_clusters: dict[str,Any],Params: dict[str,Any] = None) -> dict[str,Any]:
    """
    Track cluster across experiments

    Args:
        cluster_dict (dict): Clusters
        tracked_clusters (dict): Dictionary of tracked clusters
        Params (dict): Parameters
    Returns:
        tracked_clusters (dict): Dictionary of tracked clusters
    """
    print("Cluster tracking")
    if Params == None:
        Params = {'phi_cri':0.85,
                  'freq_cri':0.15}

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
        print("this is first track")
        for id, key in enumerate(cluster_dict.keys()):
            cluster = cluster_dict[key]
            cluster['id'] = 0

            tracked_clusters[str(id)] = [cluster]
            tracked_clusters['iteration'] = 0
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
                    new_key = int(list(tracked_clusters.keys())[-1])+1
                    #print(f"new key: {new_key}")
                    tracked_clusters[str(new_key)] = [cluster]
                else: #Add cluster to an existing tracked cluster
                    cluster_to_add_to = tracked_clusters[str(pos)]
                    cluster_to_add_to.append(cluster)
                    tracked_clusters[str(pos)] = cluster_to_add_to

        else: #If there are some clusters that match with the same tracked cluster.
            while len(result_int) != len(set(result_int)):
                #Debug info:
                #unique_match_debug_info(result,cluster_dict,t_list)

                # print(result)
                skip_tracked_cluster = []
                skip_cluster = []
                for possible_match_id in set(result.values()): #Go through all unique values
                    if possible_match_id == "new": #Do nothing if "new"
                        pass
                    else:
                        itemindex = np.argwhere(np.array(list(result.values())) == possible_match_id) #Find the index of the unique cluster match
                        if len(itemindex) > 1: #If multiple clusters match to the same tracked cluster
                            pos, result, cluster_index = resolve_unique_matches(possible_match_id, itemindex, result, cluster_dict, tracked_clusters)
                            # print(result)
                            # print(pos,result[str(cluster_index[pos])])
                            #print("Frequency",cluster_dict[cluster_index[pos]]['median_f'],"Best match with cluster",result[str(cluster_index[pos])],t_list[result[str(cluster_index[pos])]])

                            skip_tracked_cluster.append(str(result[str(cluster_index[pos])])) #Skip the best tracked cluster which is matced with another cluster.
                            skip_cluster.append(cluster_index[pos]) #Skip the best tracked cluster which is matced with another cluster.

                result = match_cluster_to_tracked_cluster(cluster_dict,tracked_clusters,Params,result,skip_cluster,skip_tracked_cluster) #Match with tracked clusters, but skip the already matched.
                # print(result)

                #Debug info:
                #unique_match_debug_info(result,cluster_dict,t_list)

                result_int = []
                for val in result.values():
                    if type(val) == int:
                        result_int.append(val)

            print("All cluster matches are now unique")
            

            #Add the clusters to tracked clusters
            for ii, key in enumerate(cluster_dict.keys()): 
                cluster = cluster_dict[key]
                pos = result[str(ii)] #Find pos in result dict
                cluster['id'] = iter
                if pos == "new":
                    new_key = int(list(tracked_clusters.keys())[-1])+1
                    #print(f"new key: {new_key}")
                    tracked_clusters[str(new_key)] = [cluster]
                else:
                    cluster_to_add_to = tracked_clusters[str(pos)]
                    cluster_to_add_to.append(cluster)
                    tracked_clusters[str(pos)] = cluster_to_add_to



    return tracked_clusters

def match_cluster_to_tracked_cluster(cluster_dict: dict[str,dict], tracked_clusters: dict[str,Any], Params: dict[str,Any], result_prev: dict[str,Any] = {}, skip_cluster: list[int] = [], skip_tracked_cluster: list[int] = []) -> dict[str,Any]:
    """
    Track cluster across experiments

    Args:
        cluster_dict (dict): Clusters
        tracked_clusters (dict): Dictionary of tracked clusters
        Params (dict): Parameters
        result_prev (dict): Dictionary indicies of how the clusters should be tracked
        skip_cluster (list): Indices of clusters that is to be skipped
        skip_tracked_cluster (list): Indices of tracked clusters that is to be skipped
    Returns:
        result (dict): Dictionary indicies of how the clusters should be tracked
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

        #print(np.argmax(np.array(MAC_max_list)),np.argmax(np.array(MAC_avg_list)),np.argmin(np.array(D_freq)))
        # id_max = np.argmax(np.array(MAC_max_list))
        # id_avg = np.argmax(np.array(MAC_avg_list))
        # id_f = np.argmin(np.array(D_freq))
        #print(id_max,id_avg,id_f)     
                
        itemindex = np.argwhere(np.array(MAC_max_list) > Params['phi_cri']) #Find where the cluster matches the tracked cluster regarding the MAC criteria
        #print(itemindex)
        if len(itemindex) > 1: #If two or more clusters combly with the mode shape criteria
            Xres = []
            Xres_f = []
            Xres_MAC = []
            for nn in itemindex:
                pos = nn[0]
                if D_freq[pos] < Params['freq_cri']: #If the cluster combly with the frequency criteria
                    X = D_freq[pos]/MAC_max_list[pos] #Objective function
                    #print(cluster['median_f'],omega_t_list[pos],D_freq[pos],MAC_max_list[pos],X)
                    Xres.append(X)
                    Xres_f.append(D_freq[pos])
                    Xres_MAC.append(MAC_max_list[pos])

            if Xres != []: # One or more cluster(s) combly with the frequency criteria
                pos1 = Xres.index(min(Xres)) #Find the cluster that is most likely
                pos2 = Xres_MAC.index(max(Xres_MAC)) #Find the largest MAC
                pos3 = Xres_f.index(min(Xres_f)) #Find the smallest frequency difference

                Xres_left = Xres.copy()
                Xres_left = Xres_left.pop(pos1)
                if type(Xres_left) == np.float64:
                    Xres_left = [Xres_left]

                Xres_MAC_left = Xres_MAC.copy()
                Xres_MAC_left = Xres_MAC_left.pop(pos1)
                if type(Xres_MAC_left) == np.float64:
                    Xres_MAC_left = [Xres_MAC_left]

                pos1_2 = Xres_MAC_left.index(max(Xres_MAC_left)) #Find the cluster that is most likely based on MAC
                pos1_3 = Xres_left.index(min(Xres_left)) #Find the cluster that is most likely
                #print(pos1,pos2,pos3,pos1_2,pos1_3)

                if (pos1 == pos2) and (pos1 == pos3): #If one match on all three parameters: objective function, max MAC and frequency difference
                    pos = int(itemindex[pos1][0])
                    result[str(id)] = pos #group to a tracked cluster

                elif abs(min(Xres_left)-min(Xres)) < Params['obj_cri']: #If the objective function results are close choose the match with highest MAC
                    if (pos1_3 == pos1_2):
                        #print(pos1,pos2,pos3,pos1_2,pos1_3)
                        pos = int(itemindex[pos1_2][0])
                        result[str(id)] = pos #group to a tracked cluster
                    else: #If none of the above choose the one with highest MAC
                        pos = int(itemindex[pos1_2][0])
                        result[str(id)] = pos #group to a tracked cluster
    
                else: #If none of the above choose the one with lowest onjective function
                    pos = int(itemindex[pos1][0])
                    result[str(id)] = pos #group to a tracked cluster
    
            else:  #No cluster comply with frequency criteria, so a new cluster is saved
                result[str(id)] = "new"
    
        elif len(itemindex) == 1: #If one cluster combly with the mode shape criteria
            pos = int(itemindex[0][0])
            if D_freq[pos] < Params['freq_cri']: #If one cluster combly with the frequency criteria
                result[str(id)] = pos #group to a tracked cluster
            else: #Does not comply with frequency criteria, so a new cluster is saved
                result[str(id)] = "new"

        else: #Does not comply with mode shape criteria
            result[str(id)] = "new"
    
    return result

def resolve_unique_matches(possible_match_id: int, itemindex: np.ndarray[int], result: dict[str,Any], cluster_dict: dict[str,dict],tracked_clusters: dict[str,Any]) -> Any:
    """
    Track cluster across experiments

    Args:
        possible_match_id (int): Index of possible pairing in tracked clusters
        itemindex (numpy.ndarray): Other possible pairng indices in tracked clusters
        result (dict): Dictionary indicies of how the clusters should be tracked
        cluster_dict (dict): Clusters
        tracked_clusters (dict): Dictionary of tracked clusters
    Returns:
        pos (int): Indice of optimal pairing
        result (dict): Dictionary indicies of how the clusters should be tracked
        cluster_index (numpy.array): Array of indicies that corrospond to the cluster
    """
    mean_MAC = []
    keys = [str(y[0]) for y in itemindex.tolist()] #Make keys for dictionary based on indices in itemindex
    for nn in itemindex: #Go through possible clusters match index
        cluster = cluster_dict[int(nn[0])]
        phi_all = cluster["mode_shapes"] #Find mode shapes in cluster
        # print(possible_match_id)
        tracked_cluster_list = tracked_clusters[str(possible_match_id)] #Accessing all cluster in a tracked cluster group
        tracked_cluster = tracked_cluster_list[-1] #Accessing the last cluster for each tracked cluster group
        # print(tracked_cluster['median_f'])
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

def unique_match_debug_info(result: dict[str,Any], cluster_dict: dict[str,dict], t_list: list[float]) -> NoReturn:
    """
    Print debug info

    Args:
        result (dict): Dictionary indicies of how the clusters should be tracked
        cluster_dict (dict): Clusters
        t_list (list): Tracked clusters last tracked median frequency
    """
    #Debug info:

    for ii, key in enumerate(cluster_dict.keys()):
        cluster = cluster_dict[key]
        pos = result[str(ii)] #Find pos in result dict
        if pos == "new":
            print(cluster_dict[key]['median_f'],str(ii),pos)
        else:
            print(cluster_dict[key]['median_f'],str(ii),pos,t_list[pos])

def track_for_plotting(tracked_clusters: dict[str,Any]) -> list[dict[str,Any]]:
    """
    Extract data for plotting
    
    Args:
        tracked_clusters (dict): Tracked clusters
    Returns:
        tracked_modaldata (list): Extracted data for plotting

    """
    tracked_modaldata = {}
    for ii in range(tracked_clusters['iteration']+1):
        matched = {}
        for key in tracked_clusters.keys():
            if key == "iteration":
                continue
            if len(tracked_clusters[key]) > 30:
                #print(key,tracked_clusters[key][-1]['median_f'],len(tracked_clusters[key]))
                cluster_data = tracked_clusters[key]
                for jj, cluster in enumerate(cluster_data):
                    if ii < 30:
                        if cluster['median_f'] > 70:
                            if cluster['median_f'] < 77:
                                continue
                    if cluster['id'] == ii:
                        if cluster['median_f'] < 8:
                            median_freq = cluster['median_f']
                            damp_mean = np.mean(cluster['d'])
                            median_mean = np.median(cluster['d'])
                            matched['1'] = {'freq': median_freq,'damping': median_mean,'ci_f': cluster['ci_f'],'ci_d':cluster['ci_d']}
                        elif cluster['median_f'] < 30:
                            median_freq = cluster['median_f']
                            damp_mean = np.mean(cluster['d'])
                            median_mean = np.median(cluster['d'])
                            matched['2'] = {'freq': median_freq,'damping': median_mean,'ci_f': cluster['ci_f'],'ci_d':cluster['ci_d']}
                        elif cluster['median_f'] < 90:
                            median_freq = cluster['median_f']
                            damp_mean = np.mean(cluster['d'])
                            median_mean = np.median(cluster['d'])
                            matched['3'] = {'freq': median_freq,'damping': median_mean,'ci_f': cluster['ci_f'],'ci_d':cluster['ci_d']}
                        break
        tracked_modaldata[ii] = matched #Preperation for storing data
    return tracked_modaldata
