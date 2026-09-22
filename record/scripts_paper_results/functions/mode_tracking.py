import matplotlib.pyplot as plt
import numpy as np
from functions.clustering import calculate_mac

def cluster_tracking(cluster_dict,tracked_clusters,Params=None):
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
        print("this is the first tracking")
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

                # print(result)
                for possible_match_id in set(result.values()): #Go through all unique values
                    if possible_match_id == "new": #Do nothing if "new"
                        pass
                    else:
                        test_if_str = np.argwhere(np.array(list(result.values())) == "new") #Test if "new" is present. If so, then we must match with str instead of int.
                        if len(test_if_str) > 0:
                            #print(test_if_str)
                            itemindex = np.argwhere(np.array(list(result.values())) == str(possible_match_id)) #Find the index of the unique cluster match
                        else:
                            itemindex = np.argwhere(np.array(list(result.values())) == possible_match_id) #Find the index of the unique cluster match
                        #print(possible_match_id,np.array(list(result.values())),itemindex, len(itemindex))
                        
                        if len(itemindex) > 1: #If multiple clusters match to the same tracked cluster
                            pos, result, cluster_index = resolve_unique_matches(possible_match_id, itemindex, result, cluster_dict, tracked_clusters)
                            # print(result)
                            #print(pos,result[str(cluster_index[pos])])
                            # print("Frequency",cluster_dict[cluster_index[pos]]['median_f'],"Best match with tracked cluster:",result[str(cluster_index[pos])],t_list[result[str(cluster_index[pos])]])

                            skip_tracked_cluster.append(str(result[str(cluster_index[pos])])) #Skip the best tracked cluster which is matced with another cluster.
                            skip_cluster.append(cluster_index[pos]) #Skip the best tracked cluster which is matced with another cluster.

                result = match_cluster_to_tracked_cluster(cluster_dict,tracked_clusters,Params,result,skip_cluster,skip_tracked_cluster) #Match with tracked clusters, but skip the already matched.
                # print("After resolving",result)

                #Debug info:
                unique_match_debug_info(result,cluster_dict,t_list)

                result_int = []
                for val in result.values():
                    if type(val) == int:
                        result_int.append(val)

            # print("All cluster matches are now unique")
            
            # if tracked_clusters['iteration'] == 28:
            #     breakpoint()

            #Add the clusters to tracked clusters
            for ii, key in enumerate(cluster_dict.keys()): 
                cluster = cluster_dict[key]
                pos = result[str(ii)] #Find pos in result dict
                cluster['id'] = iter
                if pos == "new":
                    # if list(tracked_clusters.keys())[-1] is not "iteration":
                    #     new_key = int(list(tracked_clusters.keys())[-1])+1
                    # else:
                    #     new_key = int(list(tracked_clusters.keys())[-2])+1
                    new_key = len(tracked_clusters)-1 #-1 for "iteration", + 1 for next cluster and -1 for starting at 0 = -1
                    #print(f"new key: {new_key}")
                    tracked_clusters[str(new_key)] = [cluster]
                else:
                    # print("Cluster:",cluster['median_f'],", Tracked with: ",t_list[pos])
                    cluster_to_add_to = tracked_clusters[str(pos)]
                    cluster_to_add_to.append(cluster)
                    tracked_clusters[str(pos)] = cluster_to_add_to



    return tracked_clusters

def match_cluster_to_tracked_cluster(cluster_dict,tracked_clusters,Params,result_pairs_prev={},skip_cluster=[],skip_tracked_cluster=[]):
    result_pairs = {}
    for id, key in enumerate(cluster_dict): #Go through all clusters
        if id in skip_cluster: #If this cluster is already matched skip it
            result_pairs[str(id)] = result_pairs_prev[str(id)]
            continue

        #Get mode shapes
        cluster = cluster_dict[key]
        omega = cluster['median_f']
        phi = cluster['mode_shapes'][0]
        phi_all = cluster['mode_shapes']

        MAC_list = []
        R_freq = []
        MAC_max_list = []
        MAC_avg_list = []
        omega_t_list = []
        for key in tracked_clusters: #Go through all tracked clusters. They are identified with keys which are integers from 0 and up to total number of clusters
            if key == 'iteration':
                pass
            else:
                tracked_cluster_list = tracked_clusters[key] #Accessing all cluster in a tracked cluster group
                # tracked_cluster = tracked_cluster_list[-1] #Accessing the last cluster for each tracked cluster group
                # omega_t = tracked_cluster['median_f'] #median freq of last cluster in tracked cluster group
                # phi_t_all = tracked_cluster['mode_shapes'] #phi of last cluster in tracked cluster group

                n_last_tracked_clusters = np.min((len(tracked_cluster_list),6))
                for ii in range(n_last_tracked_clusters):
                    tracked_cluster = tracked_cluster_list[-1*(ii+1)]
                
                    omega_t = tracked_cluster['median_f'] #median freq of last cluster in tracked cluster group
                    phi_t_all = tracked_cluster['mode_shapes'] #phi of last cluster in tracked cluster group
                    MACs = np.zeros((phi_all.shape[0],phi_t_all.shape[0]))
                    for ii, phi in enumerate(phi_all):
                        for jj, phi_t in enumerate(phi_t_all):
                            MAC = float(calculate_mac(phi_t, phi))
                            MACs[ii,jj] = MAC #array to compare the cluster with all tracked clusters
                    # if np.max(MACs) > Params['phi_cri']:
                    #     break

                tracked_cluster = tracked_cluster_list[-1]
                omega_t = tracked_cluster['median_f']
                print("omega_t",omega_t)

                if key in skip_tracked_cluster:
                    MAC_avg = np.mean(0)
                    MAC_max = np.max(0)
                    MAC_max_list.append(0)
                    MAC_avg_list.append(0)
                    R_freq.append(10**6)
                    omega_t_list.append(0)
                else:
                    MAC_avg = np.mean(MACs)
                    MAC_max = np.max(MACs)
                    MAC_max_list.append(MAC_max)
                    MAC_avg_list.append(MAC_avg)
                    R_freq.append(abs(omega_t-omega)/omega_t)
                    omega_t_list.append(omega_t)
                
        itemindex1 = np.argwhere(np.array(MAC_max_list) > Params['phi_cri']) #Find where the cluster matches the tracked cluster regarding the MAC criteria
        itemindex = np.argwhere(np.array(R_freq)[itemindex1[:,0]] < Params['freq_cri']) #Find where the cluster matches the tracked cluster regarding the MAC and frequency criteria
        indicies = itemindex1[itemindex[:,0]]
        if len(indicies) > 1: #If two or more clusters combly with the mode shape criteria
            X_list = []
            R_f_list = []
            MAC_list = []
            for pos in indicies[:,0]:
                # pos = nn[0]
                X = R_freq[pos]/MAC_max_list[pos] #Objective function
                X_list.append(X)
                R_f_list.append(R_freq[pos])
                MAC_list.append(MAC_max_list[pos])
            
                print(omega,omega_t_list[pos],R_freq[pos],MAC_max_list[pos])

            pos1 = X_list.index(min(X_list)) #Find the cluster that is most likely
            pos2 = MAC_list.index(max(MAC_list)) #Find the largest MAC
            pos3 = R_f_list.index(min(R_f_list)) #Find the smallest frequency difference

            if (pos1 == pos2) and (pos1 == pos3): #If one match on all three parameters: objective function, max MAC and frequency difference
                pos = int(indicies[pos1][0])
                result_pairs[str(id)] = pos #group to a tracked cluster
            else:
                X_list_left = X_list.copy()
                del X_list_left[pos1]
                if type(X_list_left) == np.float64:
                    X_list_left = [X_list_left]

                MAC_list_left = MAC_list.copy()
                del MAC_list_left[pos1]
                if type(MAC_list_left) == np.float64:
                    MAC_list_left = [MAC_list_left]

                pos2_2 = MAC_list_left.index(max(MAC_list_left)) #Find the cluster that is most likely based on MAC
            
                #Make different: abs(min(X_list_left)/min(X_list)) < Params['obj_cri'] = 2
                if abs(min(X_list_left)-min(X_list)) < Params['obj_cri']: #If the objective function results are close
                    #Cluster with the best MAC
                    if max(MAC_list_left) > max(MAC_list):
                        pos = int(indicies[pos2_2][0]) #Match with best MAC
                        result_pairs[str(id)] = pos #group to a tracked cluster
                    else:
                        pos = int(indicies[pos2][0]) #Match with best X
                        result_pairs[str(id)] = pos #group to a tracked cluster
                else: #If none of the above choose the one with lowest opjective function
                    pos = int(indicies[pos1][0])
                    result_pairs[str(id)] = pos #group to a tracked cluster
    
        elif len(indicies) == 1: #If one cluster combly with the mode shape criteria
            pos = int(indicies[0][0])
            result_pairs[str(id)] = pos #group to a tracked cluster

        else: #Does not comply with mode shape criteria
            result_pairs[str(id)] = "new"
    
    return result_pairs

def resolve_unique_matches(possible_match_id, itemindex, result, cluster_dict, tracked_clusters):
        mean_MAC = []
        max_MAC = []
        keys = [str(y[0]) for y in itemindex.tolist()] #Make keys for dictionary based on indices in itemindex
        for nn in itemindex: #Go through possible clusters match index
            cluster = cluster_dict[int(nn[0])]
            m_f = ['median_f']
            phi_all = cluster["mode_shapes"] #Find mode shapes in cluster
            #print(possible_match_id)
            tracked_cluster_list = tracked_clusters[str(possible_match_id)] #Accessing all cluster in a tracked cluster group
            tracked_cluster = tracked_cluster_list[-1] #Accessing the last cluster for each tracked cluster group
            if abs(tracked_cluster['median_f']-m_f)/tracked_cluster['median_f'] > 0.02:
                continue
            phi_t_all = tracked_cluster['mode_shapes'] #Find mode shapes in tracked cluster
            
            # #Make list of mode shapes have the same length, i.e. same number of poles
            # if len(phi_all) > len(phi_t_all):
            #     phi_all = phi_all[0:len(phi_t_all)]
            # elif len(phi_all) < len(phi_t_all):
            #     phi_t_all = phi_t_all[0:len(phi_all)]
            # else: #Equal length
            #     pass
            MAC_matrix = np.zeros((len(phi_all),len(phi_t_all))) #Initiate a matrix of MAC values
            for ii, phi in enumerate(phi_all):
                for jj, phi_t in enumerate(phi_t_all):
                    MAC_matrix[ii,jj] = calculate_mac(phi,phi_t) #Mac

            mean_MAC.append(np.mean(MAC_matrix)) #Save the mean values of MAC from this cluster compared to the matched tracked cluster
            max_MAC.append(np.max(MAC_matrix)) #Save the mean values of MAC from this cluster compared to the matched tracked cluster
        print((max(mean_MAC)),(max(max_MAC)))
        print(mean_MAC.index(max(mean_MAC)),max_MAC.index(max(max_MAC)))
        pos = mean_MAC.index(max(mean_MAC)) #Find the index with higest mean MAC, i.e. the cluster that match best with the tracked cluster.
        # breakpoint()
        cluster_index = itemindex[:,0]

        for key in keys:
            if keys[pos] == key: #Let the best cluster match stay
                pass
            else: #Add the clusters with the worst match as a new cluster
                result[key] = "new"
        return pos, result, cluster_index

def unique_match_debug_info(result,cluster_dict,t_list):
    #Debug info:
    print('\n')
    for ii, key in enumerate(cluster_dict.keys()):
        cluster = cluster_dict[key]
        pos = result[str(ii)] #Find pos in result dict
        if pos == "new":
            print(cluster_dict[key]['median_f'],str(ii),pos)
        else:
            print(cluster_dict[key]['median_f'],str(ii),pos,t_list[pos])

def track_for_plotting(tracked_clusters):
    tracked_modaldata = {}
    for ii in range(tracked_clusters['iteration']+1):
        matched = {}
        for key in tracked_clusters.keys():
            if key == "iteration":
                continue
            
            if len(tracked_clusters[key]) > 30:
                # print(key,tracked_clusters[key][-1]['median_f'],len(tracked_clusters[key]))
                cluster_data = tracked_clusters[key]
                for jj, cluster in enumerate(cluster_data):
                    if cluster['id'] == ii:
                        if key == "4" and ii == (13-1):
                            continue
                        if key == "4" and ii == (74-1):
                            continue
                        if key == "4" and ii == (31-1):
                            continue
                        if key == "4" and ii == (33-1):
                            continue
                        if key == "4" and ii == (34-1):
                            continue
                        if key == "4" and ii == (50-1):
                            continue
                        if key == "4" and ii == (53-1):
                            continue
                        if key == "4" and ii == (62-1):
                            continue

                        if cluster['median_f'] < 8:
                            median_freq = cluster['median_f']
                            damp_mean = np.mean(cluster['d'])
                            median_damp = np.median(cluster['d'])
                            matched['1'] = {'freq': median_freq,'damping': median_damp,'ci_f': cluster['ci_f'],'ci_d':cluster['ci_d']}
                        elif cluster['median_f'] < 30:
                            median_freq = cluster['median_f']
                            damp_mean = np.mean(cluster['d'])
                            median_damp = np.median(cluster['d'])
                            matched['2'] = {'freq': median_freq,'damping': median_damp,'ci_f': cluster['ci_f'],'ci_d':cluster['ci_d']}
                        elif cluster['median_f'] < 90:
                            median_freq = cluster['median_f']
                            damp_mean = np.mean(cluster['d'])
                            median_damp = np.median(cluster['d'])
                            matched['3'] = {'freq': median_freq,'damping': median_damp,'ci_f': cluster['ci_f'],'ci_d':cluster['ci_d']}
                        break
        tracked_modaldata[ii] = matched #Preperation for storing data
    return tracked_modaldata
