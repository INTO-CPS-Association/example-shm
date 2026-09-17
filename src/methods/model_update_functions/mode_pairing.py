from typing import Dict, Any, Tuple
import numpy as np
from functions.calculate_mac import calculate_mac
# pylint: disable=C0103, C0301, R0912, R0914, R0915, R1702

def pair_modes(model_freq: np.ndarray[float], model_mode_shapes: np.ndarray[float],
               cluster_dict: Dict[str,Any], params) -> Tuple[np.ndarray,
                                                             np.ndarray,np.ndarray,np.ndarray]:
    """
    Args:
    model_freq (np.ndarray[float]): Model frequencies in Hz
    model_mode_shapes (np.ndarray[float]): Model mode shape 
    cluster_dict (Dict[str,Any]): Dictionary of clusters
    params: Update parameters

    Returns:
    paired_c_freq (): Paired cluster median frequencies
    paired_c_mode_shapes (): Paired cluster mode shapes
    paired_model_freq (): Paired model median frequencies
    paried_model_mode_shapes (): Paired model mode shapes
    
    JVM: 03/11/2025

    """
    #Define number of sensors
    sensors = model_mode_shapes.shape[0]
    mode_count = model_mode_shapes.shape[1]  # Number of modes in PhiM
    model_mode_shapes = model_mode_shapes.T
    search_limit = 4
    # Initialize matrix to store MAC values
    MAX_MAC_model = np.zeros((len(cluster_dict),mode_count))

    skip_c_mode = []
    skip_m_mode = []
    no_pairing_counter = -1

    pairs = {} #Initilize pairs 
    for ii in range(len(cluster_dict)):
        pairs[ii] = [no_pairing_counter, 0, 0, 0, 0] # Model mode pair id, model frequency, frequency disrepency, MAC, cluster frequency
        no_pairing_counter -= 1

    while True:
        text_to_print = []
        for ii, key in enumerate(cluster_dict):
            MAX_MAC_model = np.zeros((len(cluster_dict[key]['mode_shapes']),mode_count))
            cluster = cluster_dict[key]
            mode_shape = cluster['mode_shapes']  # Mode shapes in current dictionary
            m_f = cluster['median_f']
            # print('median',m_f)
            f_dis = np.abs(model_freq - m_f) #Frequency discrepency
            id_list = np.argsort(f_dis)
            # print(f_dis)
            # print(id_list)
            # print(skip_c_mode)
            # print(skip_m_mode)
            for jj, ms in enumerate(mode_shape):
                if jj not in skip_c_mode:
                    for kk, idx in enumerate(id_list):
                        if (kk < search_limit) and (idx not in skip_m_mode):
                            ms_model = model_mode_shapes[idx,:]
                            MAC = calculate_mac(ms,ms_model)
                            if MAC > MAX_MAC_model[jj,idx]:
                                MAX_MAC_model[jj,idx] = MAC
            avg_mac = np.mean(MAX_MAC_model,axis=0)
            # print(avg_mac)
            for ll, mac in enumerate(avg_mac):
                if mac > params['tMAC_MU']:
                    if pairs[ii][3] < mac: #Is new MAC larger than previous pair?
                        pairs[ii] = [int(ll),float(model_freq[ll]),float(f_dis[ll]),float(mac),float(m_f)]
                else: #Store data for non-match because of low MAC
                    if pairs[ii][3] < mac: #Is new MAC larger than previous pair?
                        pairs[ii] = [pairs[ii][0],float(model_freq[ll]),float(f_dis[ll]),float(mac),float(m_f)]

        #######

        pair_id_list = []
        pair_MAC_list = []
        for mode in pairs:
            pair_id_list.append(pairs[mode][0])
            pair_MAC_list.append(pairs[mode][3])
        if len(set(pair_id_list)) == len(pair_id_list):
            break
        else:
            # print(pairs)
            for jj, possible_pair_id in enumerate(set(pair_id_list)): #Go through all unique values
                itemindex = np.argwhere(np.array(pair_id_list) == possible_pair_id).reshape(-1)
                #If multiple clusters match to the same tracked cluster
                if len(itemindex) > 1:
                    pair_macs = np.array(pair_MAC_list)[itemindex]
                    idx = np.argmax(pair_macs)
                    best_pair_id = itemindex[idx]
                    # print(itemindex,idx)
                    skip_c_mode.append(int(best_pair_id))
                    skip_m_mode.append(possible_pair_id)
                    # print(possible_pair_id,int(best_pair_id))
                    for kk in itemindex:
                        if kk != best_pair_id:
                            pairs[kk] = [no_pairing_counter,0,0,0,0]
                            no_pairing_counter -= 1

    if params['verbose'] % params.get('verbose_interval',1) == 0:
        for mode in pairs:
            if pairs[mode][0] >= 0:
                print(f"Cluster {mode,round(pairs[mode][4],5)} "
                            +f"is matched. Model freq.: {pairs[mode][1]}, with MAC: {pairs[mode][3]}")
            else:
                print(f"Cluster {mode,round(pairs[mode][4],5)} "
                    +f"is NOT matched. Best match model freq.: {pairs[mode][1]}, with MAC: {pairs[mode][3]}")

    params['verbose'] += 1

    paired_c_freq = []
    paired_c_mode_shapes = np.zeros((sensors,1))
    paired_model_freq = []
    paried_model_mode_shapes = np.zeros((1,sensors))
    for ii, mode in enumerate(pairs):
        if pairs[mode][0] >= 0:
            paired_c_freq.append(cluster_dict[ii]['median_f'])

            #If no paried mode shapes have been done before
            if np.sum(paired_c_mode_shapes) == 0:
                paired_c_mode_shapes = cluster_dict[ii]['mode_shapes'][0,:].reshape(sensors,1)
            else:
                paired_c_mode_shapes = np.append(paired_c_mode_shapes,
                            cluster['mode_shapes'][0,:].reshape(sensors,1),
                            axis=1)

            paired_model_freq.append(model_freq[pairs[mode][0]])
            if np.sum(paried_model_mode_shapes) == 0:

                paried_model_mode_shapes = model_mode_shapes[pairs[mode][0],:].reshape(sensors,1)
            else:
                paried_model_mode_shapes = np.append(paried_model_mode_shapes,
                            model_mode_shapes[pairs[mode][0],:].reshape(sensors,1),axis=1)

    paired_c_freq = np.array(paired_c_freq)
    paired_model_freq = np.array(paired_model_freq)
    
    return paired_c_freq, paired_c_mode_shapes, paired_model_freq, paried_model_mode_shapes
