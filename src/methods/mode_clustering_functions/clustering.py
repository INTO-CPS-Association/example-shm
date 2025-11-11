from typing import Any
import numpy as np
from functions.clean_sysid_output import (remove_highly_uncertain_points,transform_sysid_features)
from methods.mode_clustering_functions.create_cluster import cluster_creation
from methods.mode_clustering_functions.expand_cluster import cluster_expansion
from methods.mode_clustering_functions.initialize_Ip import cluster_initial
from methods.mode_clustering_functions.align_clusters import alignment
# pylint: disable=C0103

# Following the algorithm proposed here: https://doi.org/10.1007/978-3-031-61421-7_56
# JVM 22/10/2025

def cluster_func(sysid_output: dict[str,Any],
                 params: dict[str,Any])-> tuple[dict[str,Any],
                                                dict[str,Any], dict[str,Any]]:
    """
        Clustering of OMA results

        Args:
            sysid_output (dict): PyOMA results
            params (dict): Algorihm parameters
        Returns:
            cluster_dict_1 (dict): Dictionary of clusters after clustering
            cluster_dict_2 (dict): Dictionary of clusters after alignment
            cluster_dict_3 (dict): Dictionary of clusters after cardinailty check

    """

    #Preeliminary cleaning
    (frequencies, cov_freq, damping_ratios, cov_damping, mode_shapes
     ) = remove_highly_uncertain_points(sysid_output,params)

    (frequencies, cov_freq, damping_ratios, cov_damping,mode_shapes2, model_orders
     ) = transform_sysid_features(frequencies, cov_freq, damping_ratios,
                                  cov_damping, mode_shapes)

    row, col = np.indices(model_orders.shape)
    row = row.flatten(order="C")
    col = col.flatten(order="C")

    #Initiate data
    data1 = {'frequencies':frequencies,
            'damping_ratios':damping_ratios,
            'cov_f':cov_freq,
            'cov_d':cov_damping,
            'mode_shapes':mode_shapes2,
            'row':row,
            'col':col}

    cluster_dict = {}
    cluster_counter = 0
    for count, f in enumerate(frequencies.flatten(order="f")):
        #Extract data
        frequencies = data1['frequencies']
        damping_ratios = data1['damping_ratios']
        cov_freq = data1['cov_f']
        cov_damping = data1['cov_d']

        #Inital point
        r = row[count]
        c = col[count]
        ip = [frequencies[r,c],cov_freq[r,c],damping_ratios[r,c],cov_damping[r,c]]

        if np.isnan(ip[0]) == True: #Pass if the pole does not exist.
            pass
        else:
            initial_points = cluster_initial(ip,data1) #Algorithm. 1 step 3 - Initialization

            #Creating clusters
            cluster1 = cluster_creation(initial_points,params)

            data2 = data1.copy()

            # Cluster expansion
            expansion = True
            kk = 0
            while expansion:
                kk += 1
                if kk > 10:
                    raise RuntimeError("Expansion never ends, something is wrong.")
                pre_cluster = cluster1
                cluster2 = cluster_expansion(cluster1,data2,params)
                if cluster2['f'].shape == pre_cluster['f'].shape:
                    if (cluster2['f'] == pre_cluster['f']).all():
                        expansion = False
                    else:
                        cluster1 = cluster2
                else:
                    cluster1 = cluster2

            #Sort if more than one pole exist in the cluster
            if isinstance(cluster2['f'],np.ndarray):
                cluster2 = sort_cluster(cluster2)

            #Save cluster
            if isinstance(cluster2['f'],np.ndarray): #Must atleast have two poles
                cluster_dict[str(cluster_counter)] = cluster2
                cluster_counter += 1
                data1 = remove_data_from_S(data2,cluster2) #Remove clustered poles from data
            else:
                print("cluster2 too short:",1,"But must be:",params['mstab'])

    #Allignment or merging of stacked clusters
    cluster_dict2 = alignment(cluster_dict.copy(),params)

    #Custom cardinality check
    cluster_dict3 = {}
    cluster_counter = 0
    for ii, key in enumerate(cluster_dict2.keys()):
        cluster = cluster_dict2[key]
        if isinstance(cluster['f'],np.ndarray):
            if cluster['f'].shape[0] < params['mstab']:
                print("Cluster", np.median(cluster['f']),
                      "too short:",cluster['f'].shape[0],
                      "Must be: >",params['mstab'])
            else:
                print("Cluster saved:", np.median(cluster['f']))
                cluster_dict3[str(ii)] = cluster
                cluster_counter += 1
                data1 = remove_data_from_S(data2,cluster) #Remove clustered poles from data
        else:
            print("cluster too short:",1,"But must be:",params['mstab'])
            cluster_dict2.pop(key)

    #Add median and confidence intervals (one sided) to cluster data
    for key in cluster_dict3.keys():
        cluster = cluster_dict3[key]
        cluster['median_f'] = np.median(cluster['f'])
        ci_f = np.sqrt(cluster['cov_f']) * params['bound_multiplier']
        ci_d = np.sqrt(cluster['cov_d']) * params['bound_multiplier']
        cluster['ci_f'] = ci_f
        cluster['ci_d'] = ci_d

    #Sort the clusters into accending order of median frequency
    median_frequencies = np.zeros(len(cluster_dict3))
    for ii, key in enumerate(cluster_dict3.keys()):
        cluster = cluster_dict3[key]
        median_frequencies[ii] = cluster['median_f']

    indices = np.argsort(median_frequencies)
    cluster_dict4 = {}
    #Rename all cluster dict from 0 to len(cluster_dict2)
    for ii, key in enumerate(np.array(list(cluster_dict3.keys()))[indices]):
        cluster_dict4[ii] = cluster_dict3[key] #Insert a cluster into a key

    return cluster_dict4

def remove_data_from_S(data: dict[str,Any],cluster: dict[str,Any]) -> dict[str,Any]:
    """
        Remove cluster from data or S

        Args:
            data (dict): OMA points data
            cluster (dict): cluster
        Returns:
            data2 (dict): Filtered OMA points data

    """
    #Copy data
    frequencies = data['frequencies'].copy()
    damping_ratios = data['damping_ratios'].copy()
    cov_freq = data['cov_f'].copy()
    cov_damping = data['cov_d'].copy()
    mode_shapes = data['mode_shapes'].copy()
    row = data['row'].copy()
    col = data['col'].copy()
    #Make new data dictionary
    data2 = {'frequencies':frequencies,
            'damping_ratios':damping_ratios,
            'cov_f':cov_freq,
            'cov_d':cov_damping,
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
        data2['cov_f'][r,c] = np.nan
        data2['cov_d'][r,c] = np.nan
        data2['mode_shapes'][r,c,:] = np.nan

    return data2

def sort_cluster(cluster: dict[str,Any]) -> dict[str,Any]:
    """
        Sort cluster based on row/model order

        Args:
            cluster (dict): Cluster
        Returns:
            cluster (dict): Sorted cluster

    """
    sort_id = np.argsort(cluster['row'])

    cluster['f'] = cluster['f'][sort_id]
    cluster['cov_f'] = cluster['cov_f'][sort_id]
    cluster['d'] = cluster['d'][sort_id]
    cluster['cov_d'] = cluster['cov_d'][sort_id]
    cluster['mode_shapes'] = cluster['mode_shapes'][sort_id,:]
    cluster['MAC'] = cluster['MAC'][sort_id]
    cluster['model_order'] = cluster['model_order'][sort_id]
    cluster['row'] = cluster['row'][sort_id]
    cluster['col'] = cluster['col'][sort_id]

    return cluster
