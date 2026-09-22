from typing import Any, Dict, Tuple
import numpy as np
from src.methods.sysid_functions.clean_sysid_output import clean_and_transform
from methods.mode_clustering_functions.create_cluster import cluster_creation
from methods.mode_clustering_functions.expand_cluster import cluster_expansion
from methods.mode_clustering_functions.initialize_Ip import cluster_initial
from methods.mode_clustering_functions.align_clusters import alignment
from methods.mode_clustering_functions.global_uncertainty import global_uncertainty
# pylint: disable=C0103, R0912, R0914, R0915, R1702

from methods.mode_clustering_functions.plot_clusters import plot_clusters

# Following the algorithm proposed here: https://doi.org/10.1007/978-3-031-61421-7_56
# JVM 22/10/2025

def cluster_func(sysid_output: Dict[str,Any],
                 params: Dict[str,Any])-> Tuple[Dict[str,Any],
                                                Dict[str,Any], Dict[str,Any]]:
    """
        Clustering of OMA results

        Args:
            sysid_output (Dict[str,Any]): PyOMA results
            params (Dict[str,Any]): Algorihm parameters
        Returns:
            cluster_dict_1 (Dict[str,Any]): Dictionary of clusters after clustering
            cluster_dict_2 (Dict[str,Any]): Dictionary of clusters after alignment
            cluster_dict_3 (Dict[str,Any]): Dictionary of clusters after cardinailty check

    """

    (frequencies, std_freq, damping_ratios, std_damping, mode_shapes2, _, Ufx_list, model_orders
     ) = clean_and_transform(sysid_output, params)

    row, col = np.indices(model_orders.shape)
    row = row.flatten(order="C")
    col = col.flatten(order="C")

    #Initiate data. Data1 =  which is unclustered modes/poles
    data1 = {'frequencies':frequencies,
            'damping_ratios':damping_ratios,
            'std_f':std_freq,
            'std_d':std_damping,
            'mode_shapes':mode_shapes2,
            'row':row,
            'col':col}
    cluster_dict = {}
    cluster_counter = 0
    for count, _ in enumerate(frequencies.flatten(order="f")):
        #Extract data
        frequencies = data1['frequencies']
        damping_ratios = data1['damping_ratios']
        std_freq = data1['std_f']
        std_damping = data1['std_d']

        #Inital point
        r = row[count]
        c = col[count]
        ip = [frequencies[r,c],std_freq[r,c],damping_ratios[r,c],std_damping[r,c]]

        if np.isnan(ip[0]) == True: #Pass if the pole does not exist.
            pass
        else:
            initial_points = cluster_initial(ip,data1,params) #Algorithm. 1 step 3 - Initialization

            #Creating clusters
            cluster = cluster_creation(initial_points,params)

            #Rerun first to algorithms with updated initial point.
            r_id = np.argmin(cluster['row'])
            ip2 = [cluster['f'][r_id],cluster['std_f'][r_id],cluster['d'][r_id],cluster['std_d'][r_id]]
            if ip2 == ip:
                initial_points = cluster_initial(ip,data1,params)
                cluster = cluster_creation(initial_points,params)

            data2 = data1.copy()

            # Cluster expansion
            expansion = True
            kk = 0
            while expansion:
                kk += 1
                prev_cluster = cluster
                clusters_expan = cluster_expansion(cluster,data2,params)
                if ((clusters_expan['f'].shape == prev_cluster['f'].shape) and
                    ((clusters_expan['f'] == prev_cluster['f']).all())):
                    expansion = False
                else:
                    if kk > 10: #If expansion does not end
                        if np.mean(cluster['MAC']) > np.mean(prev_cluster['MAC']):
                            clusters_expan = cluster
                        else:
                            clusters_expan = prev_cluster
                        expansion = False
                        breakpoint()
                    cluster = clusters_expan

            #Sort if more than one pole exist in the cluster
            if isinstance(clusters_expan['f'],np.ndarray):
                clusters_expan = sort_cluster(clusters_expan)

            #Save cluster
            if isinstance(clusters_expan['f'],np.ndarray): #Must atleast have two poles
                cluster_dict[str(cluster_counter)] = clusters_expan
                cluster_counter += 1
                data1 = remove_data_from_S(data2,clusters_expan) #Remove clustered poles from data
            else:
                print("cluster too short:",1,"But must be:",params['mstab'])

    # Debug clusters before alignment af cardinality check. Uncomment the line below.
    # cluster_with_global_unc = append_information(cluster_dict,params,Ufx_list,cardinality_check=False)
    print(cluster_dict.keys())
    #Allignment or merging of stacked clusters
    cluster_dict_aligned = alignment(cluster_dict.copy(),params)
    print(cluster_dict_aligned.keys())
    #Add information
    cluster_with_global_unc = append_information(cluster_dict_aligned,params,Ufx_list,cardinality_check=True)
    return cluster_with_global_unc

def remove_data_from_S(data: Dict[str,Any],cluster: Dict[str,Any]) -> Dict[str,Any]:
    """
        Remove cluster from data or S

        Args:
            data (Dict[str,Any]): OMA points data
            cluster (Dict[str,Any]): cluster
        Returns:
            data2 (Dict[str,Any]): Filtered OMA points data

    """
    #Copy data
    frequencies = data['frequencies'].copy()
    damping_ratios = data['damping_ratios'].copy()
    std_freq = data['std_f'].copy()
    std_damping = data['std_d'].copy()
    mode_shapes = data['mode_shapes'].copy()
    row = data['row'].copy()
    col = data['col'].copy()
    #Make new data dictionary
    data2 = {'frequencies':frequencies,
            'damping_ratios':damping_ratios,
            'std_f':std_freq,
            'std_d':std_damping,
            'mode_shapes':mode_shapes,
            'row':row,
            'col':col}
    #Remove data
    row = cluster['row']
    col = cluster['col']
    for ii, r in enumerate(row):
        c = col[ii]
        data2['frequencies'][r,c] = np.nan
        data2['damping_ratios'][r,c] = np.nan
        data2['std_f'][r,c] = np.nan
        data2['std_d'][r,c] = np.nan
        data2['mode_shapes'][r,c,:] = np.nan

    return data2

def append_information(cluster_dict,params,Ufx_list,cardinality_check=True) -> Dict[str, Any]:
    """
    Append data, make cardinaility check, sort clusters and add global uncertainty.

    Args:
        cluster_dict (Dict[str,Any]): Clusters in dictionary
        params (Dict[str,Any]): Parameters
        Ufx_list (List): List of Ufx from sysid
        cardinality_check (bool): Should cardinality check be applied. Default = True
    Returns:
    """
    #Add median and confidence intervals (one sided) to cluster data
    for key in cluster_dict:
        cluster = cluster_dict[key]
        cluster['median_f'] = np.median(cluster['f'])
        cluster['median_d'] = np.median(cluster['d'])
        cluster['mean_f'] = np.mean(cluster['f'])
        cluster['mean_d'] = np.mean(cluster['d'])
        cluster['ci_f'] = cluster['std_f']*params['bound_multiplier']
        cluster['ci_d'] = cluster['std_d']*params['bound_multiplier']

    if cardinality_check:
        #Custom cardinality check
        cluster_dict_cardinality = {}
        cluster_counter = 0
        short_clusters = ""
        saved_clusters = ""
        for ii, key in enumerate(cluster_dict.keys()):
            cluster = cluster_dict[key]
            if 'f' in cluster:
                if isinstance(cluster['f'],np.ndarray):
                    if cluster['f'].shape[0] < params['mstab']:
                        short_clusters = short_clusters+"("+str(int(key)+1)+","+f"{cluster['median_f']:.3f}"+")"+","
                        # print("Cluster", np.median(cluster['f']),
                        #     "too short:",cluster['f'].shape[0],
                        #     "Must be: >",params['mstab'])
                    else:
                        saved_clusters = saved_clusters +"("+str(int(key)+1)+","+f"{cluster['median_f']:.3f}"+")"+","
                        # print("Cluster saved:", np.median(cluster['f']))
                        cluster_dict_cardinality[str(ii)] = cluster
                        cluster_counter += 1
                else:
                    # print("cluster too short:",1,"But must be:",params['mstab'])
                    short_clusters = short_clusters+"("+str(int(key)+1)+","+f"{cluster['median_f']:.3f}"+")"+","
                    short_clusters.append(int(key)+1)
                    cluster_dict.pop(key)
        if saved_clusters != "":
            print(f"Saved clusters: [",saved_clusters,"]")
    else:
        cluster_dict_cardinality = cluster_dict.copy()

    #Sort the clusters into accending order of median frequency
    median_frequencies = np.zeros(len(cluster_dict_cardinality))
    for ii, key in enumerate(cluster_dict_cardinality.keys()):
        cluster = cluster_dict_cardinality[key]
        median_frequencies[ii] = cluster['median_f']
    indices = np.argsort(median_frequencies)
    cluster_dict_renamed = {}
    #Rename all cluster dict from 0 to len(cluster_dict2)
    for ii, key in enumerate(np.array(list(cluster_dict_cardinality.keys()))[indices]):
        cluster_dict_renamed[str(ii)] = cluster_dict_cardinality[key] #Insert a cluster into a key

    #Add global uncertainty
    for ii, key in enumerate(cluster_dict_renamed.keys()):
        Ufx = []
        cluster = cluster_dict_renamed[key]
        for ii, r in enumerate(cluster['row']):
            Ufx.append(Ufx_list[r,cluster['col'][ii],:,:])
        cluster_dict_renamed[key]['Ufx'] = np.array(Ufx)

    cluster_with_global_unc = global_uncertainty(cluster_dict_renamed,bound=params['bound_multiplier'])

    return cluster_with_global_unc

def sort_cluster(cluster: Dict[str,Any]) -> Dict[str,Any]:
    """
        Sort cluster based on row/model order

        Args:
            cluster (Dict[str,Any]): Cluster
        Returns:
            cluster (Dict[str,Any]): Sorted cluster

    """
    sort_id = np.argsort(cluster['row'])

    cluster['f'] = cluster['f'][sort_id]
    cluster['std_f'] = cluster['std_f'][sort_id]
    cluster['d'] = cluster['d'][sort_id]
    cluster['std_d'] = cluster['std_d'][sort_id]
    cluster['mode_shapes'] = cluster['mode_shapes'][sort_id,:]
    cluster['MAC'] = cluster['MAC'][sort_id]
    cluster['model_order'] = cluster['model_order'][sort_id]
    cluster['row'] = cluster['row'][sort_id]
    cluster['col'] = cluster['col'][sort_id]

    return cluster
