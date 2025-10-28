from typing import Any
import numpy as np
from methods.mode_clustering_functions.create_cluster import cluster_creation

def cluster_expansion(cluster: dict[str,Any], data: dict[str,Any], Params: dict[str,Any]) -> dict[str,Any]:
    """
        Expand cluster based on minima and maxima bound

        Args:
            cluster (dict): Intermediate cluster
            data (dict): OMA points data
            Params (dict): Dictionary of algorithm parameters
        Returns:
            cluster (dict): Expanded cluster

    """
    #print("\nExpansion")
    unClustered_frequencies = data['frequencies']
    unClustered_damping = data['damping_ratios']
    
    freq_c = cluster['f']
    cov_f = cluster['cov_f']
    damp_c = cluster['d']
    cov_d = cluster['cov_d']
    row = cluster['row']

    bound_multiplier = Params['bound_multiplier']
    
    #Find min-max bounds of cluster
    f_lower_bound = np.min(freq_c - bound_multiplier * np.sqrt(cov_f))  # Minimum of all points for frequencies
    f_upper_bound = np.max(freq_c + bound_multiplier * np.sqrt(cov_f))  # Maximum of all points for frequencies
    d_lower_bound = np.min(damp_c - bound_multiplier * np.sqrt(cov_d))  # Minimum of all points for damping
    d_upper_bound = np.max(damp_c + bound_multiplier * np.sqrt(cov_d))  # Maximum of all points for damping

    #Mask of possible expanded poles
    condition_mask = (unClustered_frequencies >= f_lower_bound) & (unClustered_frequencies <= f_upper_bound) & (unClustered_damping >= d_lower_bound) & (unClustered_damping <= d_upper_bound)
    # Get indices satisfying the condition
    expanded_indices = np.argwhere(condition_mask)

    #Initiate cluster_points for cluster creation
    cluster_points = {}
    cluster_points['f'] = data['frequencies'][condition_mask]
    cluster_points['cov_f'] = data['cov_f'][condition_mask]
    cluster_points['d'] = data['damping_ratios'][condition_mask]
    cluster_points['cov_d'] = data['cov_d'][condition_mask]
    cluster_points['ms'] = data['mode_shapes'][condition_mask,:]
    cluster_points['row'] = expanded_indices[:,0]
    cluster_points['col'] = expanded_indices[:,1]

    #Make the first ip from cluster be the previous first point in cluster_points
    if isinstance(cluster['f'],np.ndarray):
        index_f = np.argwhere(cluster_points['f'] == cluster['f'][0])
    else:
        index_f = np.argwhere(cluster_points['f'] == cluster['f'])
    if len(index_f[:,0]) > 1:
        index_row = np.argwhere(cluster_points['row'][index_f[:,0]] == cluster['row'][0])
        ip_id = int(index_f[index_row[:,0]][:,0])
    else:
        ip_id = int(index_f[:,0])
    indecies = list(range(len(cluster_points['f'])))
    poped_id = indecies.pop(ip_id)
    indecies.insert(0,poped_id)
    indecies = np.array(indecies)

    cluster_points['f'] = cluster_points['f'][indecies]
    cluster_points['cov_f'] = cluster_points['cov_f'][indecies]
    cluster_points['d'] = cluster_points['d'][indecies]
    cluster_points['cov_d'] = cluster_points['cov_d'][indecies]
    cluster_points['ms'] = cluster_points['ms'][indecies,:]
    cluster_points['row'] = cluster_points['row'][indecies]
    cluster_points['col'] = cluster_points['col'][indecies]

    #Check if these values can be clustered
    cluster = cluster_creation(cluster_points,Params)
    if isinstance(cluster['f'],np.ndarray):
        if len(cluster['row']) != len(set(cluster['row'])):
            print("row_before",cluster_points['row'])
            print("row_after",cluster['row'])
            print("exp2",cluster['f'])
            print("double orders",cluster['row'])
            breakpoint()

    return cluster
