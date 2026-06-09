from typing import Any, Dict, List
import numpy as np
from functions.calculate_mac import calculate_mac
from scipy import stats
from scipy.stats import ttest_ind, ttest_ind_from_stats
from scipy.stats import norm
import matplotlib.pyplot as plt
# pylint:  disable=C0103, R0912, R0913, R0914, R0915, R0917, R1702

def match_cluster_to_tracked_cluster(cluster_dict: Dict[str,Any], tracked_clusters: Dict[str,Any],
                                     params: Dict[str,Any], result_pairs_prev: Dict[str,Any] = None,
                                     skip_cluster: List = None,
                                     skip_tracked_cluster: List = None) -> Dict[str,Any]:
    """
    Match clusters to tracked clusters

    The result dictionary consist of keys: cluster indecies,
    and values: indecies of tracked cluster to match with

    Example:
        Cluster 1 match with tracked cluster 2
        Cluster 2 match with tracked cluster 1
        Cluster 3 match with tracked cluster 1
        Cluster 4 match with "new", i.e. could not be matched with an existing tracked cluster

    Args:
        cluster_dict (dict): Dictionary of clusters
        tracked_clusters (dict): Previously tracked clusters
        params (dict): tracking parameters
        result_pairs_prev (dict): Dictionary of previous match result
        skip_cluster (list): List of clusters that are the optimal match with a tracked cluster
        skip_tracked_cluster (list): List of tracked clusters are an optimal match with a cluster

    Returns:
        result (dict): Dictionary of matches

    """
    fig_ax1 = None
    fig_ax2 = None
    fig_ax3 = None
    fig_ax4 = None
    if skip_tracked_cluster is None:
        skip_tracked_cluster = []

    l = params.get('l_lastest_clusters',1) #Number of tracked clusters to compare with

    #Calculate parameters for tracked clusters that are universal for all comparisons.
    greatest_interval_f = []
    greatest_interval_d = []
    zeta_w_list = []
    zeta_w_var_list = []
    zeta_t_mean_list = []
    RSS_zeta_std = []
    for key_t in tracked_clusters: #Go through all tracked clusters.
        #They are identified with keys which are integers from 0 up to total number of clusters
        if key_t == 'iteration':
            pass

        elif key_t in skip_tracked_cluster:
            greatest_interval_f.append([-1,-1])
            greatest_interval_d.append([-1,-1])
        else:
            #Accessing all cluster in a tracked cluster group
            tracked_cluster_list = tracked_clusters[key_t]
            n_last_tracked_clusters = np.min((len(tracked_cluster_list),l))
            freq_intervals = None
            damp_intervals = None
            omega_t_list = []
            omega_mean_t_list = []
            zeta_t_list = []
            zeta_list = []
            zeta_inv_var_list = []
            zeta_var_list = []
            for ii in range(n_last_tracked_clusters):
                tracked_cluster = tracked_cluster_list[-1*(ii+1)]

                intervals_f = np.array([tracked_cluster['median_f']-tracked_cluster['global_ci'][0,0], tracked_cluster['median_f']+tracked_cluster['global_ci'][0,0]])
                intervals_d = np.array([tracked_cluster['median_d']-tracked_cluster['global_ci'][1,1], tracked_cluster['median_d']+tracked_cluster['global_ci'][1,1]])
                if freq_intervals is None:
                    freq_intervals = intervals_f
                else:
                    freq_intervals = np.vstack((freq_intervals,intervals_f))

                if damp_intervals is None:
                    damp_intervals = intervals_d
                else:
                    damp_intervals = np.vstack((damp_intervals,intervals_d))
                
                #phi of last cluster in tracked cluster group
                phi_t_all = tracked_cluster['mode_shapes']

                omega_t_list.append(tracked_cluster['median_f'])
                omega_mean_t_list.append(np.mean(tracked_cluster['f']))
                zeta_t_list.append(tracked_cluster['median_d'])
                zeta_list.append(tracked_cluster['mean_d'])
                zeta_inv_var_list.append(1/(tracked_cluster['global_std'][1,1]**2))
                zeta_var_list.append(tracked_cluster['global_std'][1,1]**2)
                

            omega_t = np.mean(omega_t_list)
            zeta_t = np.mean(zeta_t_list)
            zeta_w_var = 1/np.sum(zeta_inv_var_list)
            zeta_w = np.sum(np.matmul(zeta_list,zeta_inv_var_list))/np.sum(zeta_inv_var_list)
            zeta_w_list.append(zeta_w)
            zeta_w_var_list.append(zeta_w_var)
            zeta_t_mean_list.append(zeta_t)
            RSS_zeta_std.append(np.sqrt(np.sum(zeta_var_list))) #Root sum squared of zeta's variance

            if n_last_tracked_clusters > 1:
                greatest_interval_f.append([np.min(freq_intervals[:,0],axis=0),np.max(freq_intervals[:,1],axis=0)])
            else:
                greatest_interval_f.append(freq_intervals)
            
            if n_last_tracked_clusters > 1:
                greatest_interval_d.append([np.min(damp_intervals[:,0],axis=0),np.max(damp_intervals[:,1],axis=0)])
            else:
                greatest_interval_d.append(damp_intervals)


    #Calculate parameters that are relative to the new cluster
    result_pairs = {}
    for idx, key in enumerate(cluster_dict): #Go through all clusters
        if skip_cluster is not None:
            if result_pairs_prev is not None:
                if idx in skip_cluster: #If this cluster is already matched skip it
                    result_pairs[str(idx)] = result_pairs_prev[str(idx)]
                    continue

        #Get mode shapes
        cluster = cluster_dict[key]
        omega = cluster['median_f']
        zeta = cluster['median_d']
        phi_all = cluster['mode_shapes']

        MAC_list = []
        R_freq = []
        R_damp = []
        MAC_max_list = []
        t_test_list = []
        t_list = []
        delta_zeta = []
        counter = -1
        for key_t in tracked_clusters: #Go through all tracked clusters.
            #They are identified with keys which are integers from 0 up to total number of clusters
            if key_t == 'iteration':
                pass

            elif key_t in skip_tracked_cluster:
                MAC_max_list.append(0)
                R_freq.append(10**6)
                R_damp.append(10**6)
                delta_zeta.append(False)
                zeta_t_mean_list.append(10**6)
                t_test_list.append(False)
                t_list.append(0)
            else:
                counter += 1
                #Accessing all cluster in a tracked cluster group
                tracked_cluster_list = tracked_clusters[key_t]
                t_list.append(tracked_cluster_list[-1]['median_f'])
                n_last_tracked_clusters = np.min((len(tracked_cluster_list),l))
                t_test = False

                omega_t = tracked_cluster_list[-1]['median_f']
                zeta_t = zeta_t_mean_list[counter]

                MAC_max = 0
                for ii in range(n_last_tracked_clusters):
                    tracked_cluster = tracked_cluster_list[-1*(ii+1)]
                    
                    #phi of last cluster in tracked cluster group
                    phi_t_all = tracked_cluster['mode_shapes']
                    # MAC_matrix = np.zeros((phi_all.shape[0],phi_t_all.shape[0]))
                    for kk, phi in enumerate(phi_all):
                        for jj, phi_t in enumerate(phi_t_all):
                            MAC = float(calculate_mac(phi_t, phi))
                            #array to compare the cluster with all tracked clusters
                            # MAC_matrix[kk,jj] = MAC
                            if MAC > MAC_max:
                                MAC_max = MAC
                    # MAC_max_n.append(np.max(MAC_matrix)) #Max MAC value between cluster and tracked cluster
                    test_result, fig_ax1, fig_ax2, fig_ax3, fig_ax4 = hypothesis_test(cluster, tracked_cluster, fig_ax1, fig_ax2, fig_ax3, fig_ax4)
                    t, t0, ci_lower, ci_upper = test_result
                    if abs(t0) < abs(t):
                        t_test = True
   
                if t_test:
                    t_test_list.append(True)
                else:
                    t_test_list.append(False)

                MAC_max_list.append(MAC_max)

                zeta_w = zeta_w_list[counter]
                zeta_w_var = zeta_w_var_list[counter]
                if (omega>3) and (omega<4):
                    if (omega_t>3) and (omega_t<4):
                        print(f"[{tracked_cluster_list[-1]['id']}]",omega,omega_t)
                        print(zeta,zeta_t,zeta_w)
                        print(abs(zeta_w-zeta),"<",RSS_zeta_std[counter]*3)
                delta_zeta.append(abs(zeta_w-zeta)<RSS_zeta_std[counter]*3)
                #For cases where the tracked cluster has a frequency of 0
                R_freq.append(abs(omega_t-omega)/omega_t) #Relative frequency difference
                R_damp.append(abs(zeta_t-zeta)/zeta_t)

        # # Median of cluster must be inside interval for l-latest t-clusters
        # lower_mask = (cluster['median_f'] - greatest_interval_f[:,0]) > 0
        # upper_mask = (cluster['median_f'] - greatest_interval_f[:,1]) < 0

        greatest_interval_f = np.array(greatest_interval_f)
        greatest_interval_d = np.array(greatest_interval_d)
        #Interval of cluster must overlap with interval for l-latest t-clusters
        lower_mask = (cluster['median_f']+cluster['global_ci'][0,0] - greatest_interval_f[:,0]) > 0
        upper_mask = (cluster['median_f']-cluster['global_ci'][0,0] - greatest_interval_f[:,1]) < 0
        ci_f_match_mask = lower_mask==upper_mask

        #Interval of cluster must overlap with interval for l-latest t-clusters
        lower_mask = (cluster['median_d']+cluster['global_ci'][1,1] - greatest_interval_d[:,0]) > 0
        upper_mask = (cluster['median_d']-cluster['global_ci'][1,1] - greatest_interval_d[:,1]) < 0
        ci_d_match_mask = lower_mask==upper_mask

        delta_zeta_mask = np.array(delta_zeta)
        t_test_list = np.array(t_test_list)

        mac_match_mask = np.array(MAC_max_list) > params['phi_cri']
        match_mask = np.logical_and(ci_f_match_mask,mac_match_mask)
        # match_mask = np.logical_and(np.logical_and(ci_f_match_mask,ci_d_match_mask),mac_match_mask)
        # match_mask = np.logical_and(match_mask,np.logical_or(delta_zeta_mask,ci_d_match_mask))
        match_mask = np.logical_and(match_mask,ci_d_match_mask)
        # match_mask = np.logical_and(t_test_list,mac_match_mask)
        match_indicies = np.argwhere(match_mask==True).reshape(-1)

        print("\n",omega)
        print(np.argwhere(ci_f_match_mask==True).reshape(-1),"frequency overlap")
        print(np.argwhere(ci_d_match_mask==True).reshape(-1),"damp overlap")
        print(np.argwhere(mac_match_mask==True).reshape(-1),"mac criteria")
        print(np.argwhere(delta_zeta_mask==True).reshape(-1),"zeta change")
        print(np.argwhere(t_test_list==True).reshape(-1),"hyp. test")
        print(np.argwhere(match_mask==True).reshape(-1),"Commom matches")
        print(np.array(t_list))
        print(np.array(MAC_max_list))
        print(np.array(t_list)[np.argwhere(match_mask==True).reshape(-1)],"omega")
        print(np.array(MAC_max_list)[np.argwhere(match_mask==True).reshape(-1)],"MACs")
        print(np.array(zeta_t_mean_list)[np.argwhere(match_mask==True).reshape(-1)],"zeta")

        # match_indicies = item_indices
        if len(match_indicies) > 1: #If two or more clusters combly with the criteria
            print(match_indicies)
            X_list = []
            R_f_list = []
            R_d_list = []
            MAC_list = []
            for pos in match_indicies:
                X = R_freq[pos]/MAC_max_list[pos] #Objective function
                # X = (R_freq[pos]**2+MAC_max_list[pos]**2+R_damp[pos]**2)**0.5 #Objective function
                X_list.append(X)
                R_f_list.append(R_freq[pos])
                R_d_list.append(R_damp[pos])
                MAC_list.append(MAC_max_list[pos])

            pos1 = X_list.index(min(X_list)) #Find the cluster that is most likely
            pos2 = MAC_list.index(max(MAC_list)) #Find the largest MAC
            pos3 = R_f_list.index(min(R_f_list)) #Find the smallest frequency difference
            pos4 = R_d_list.index(min(R_d_list))
            print(pos1,pos2,pos3,pos4)
            #If one match on all three parameters:
            if pos2 == pos3:
                pos = int(match_indicies[pos1])
                result_pairs[str(idx)] = pos #group to a tracked cluster
            else:
                X_list_left = X_list.copy()
                del X_list_left[pos1]
                if isinstance(X_list_left,float):
                    X_list_left = [X_list_left]

                MAC_list_left = MAC_list.copy()
                del MAC_list_left[pos1]
                if isinstance(MAC_list_left,float):
                    MAC_list_left = [MAC_list_left]

                R_f_list_left = R_f_list.copy()
                del R_f_list_left[pos1]
                if isinstance(R_f_list_left,float):
                    R_f_list_left = [R_f_list_left]

                R_d_list_left = R_d_list.copy()
                del R_d_list_left[pos1]
                if isinstance(R_d_list_left,float):
                    R_d_list_left = [R_d_list_left]

                pos1_2 = X_list_left.index(max(X_list_left))
                #Find the cluster that is most likely based on MAC
                pos2_2 = MAC_list_left.index(max(MAC_list_left))

                pos3_2 = R_f_list_left.index(min(R_f_list_left))

                pos4_2 = R_d_list_left.index(min(R_d_list_left))

                print("mac_test",MAC_list_left,MAC_list,pos2_2)
                print(min(X_list),min(X_list_left),pos1_2,match_indicies)
                print(min(R_f_list),min(R_f_list_left),pos3_2)
                #Make different: abs(min(X_list_left)/min(X_list)) < params['obj_cri'] = 2
                #If the objective function results are close
                if abs(min(X_list_left)-min(X_list)) < params['obj_cri']:
                    #Cluster with the best MAC
                    if max(MAC_list_left) > max(MAC_list):
                        pos = int(match_indicies[pos2_2]) #Match with best MAC
                        result_pairs[str(idx)] = pos #group to a tracked cluster
                    else:
                        pos = int(match_indicies[pos2]) #Match with best MAC
                        result_pairs[str(idx)] = pos #group to a tracked cluster
                    # if pos3 == pos4:
                    #     pos = int(match_indicies[pos3]) #Match with best X
                    #     result_pairs[str(idx)] = pos #group to a tracked cluster
                    # elif pos2 == pos4:
                    #     pos = int(match_indicies[pos2]) #Match with best X
                    #     result_pairs[str(idx)] = pos #group to a tracked cluster
                    # else:
                    #     pos = int(match_indicies[pos1]) #Match with best X
                    #     result_pairs[str(idx)] = pos #group to a tracked cluster
                    # if max(R_d_list_left) > max(R_d_list):
                    #     pos = int(match_indicies[pos4_2]) #Match with best damping ratio
                    #     result_pairs[str(idx)] = pos #group to a tracked cluster
                    # else:
                    #     pos = int(match_indicies[pos2]) #Match with best damping ratio
                    #     result_pairs[str(idx)] = pos #group to a tracked cluster

                else: #If none of the above choose the one with lowest opjective function
                    pos = int(match_indicies[pos1]) #Match with best X
                    result_pairs[str(idx)] = pos #group to a tracked cluster
                
                
                # result_pairs[str(idx)] = pos = int(match_indicies[pos4]) #Match with best damping ratio

        elif len(match_indicies) == 1: #If one cluster combly with the mode shape criteria
            # list_tracked_cluster_keys = list(tracked_clusters.keys())[1:]
            pos = int(match_indicies[0])
            tracked_cluster_list = tracked_clusters[str(pos)]
            l = params.get('l_lastest_clusters',1) #Number of tracked clusters to compare with
            n_last_tracked_clusters = np.min((len(tracked_cluster_list),l))
            
            result_pairs[str(idx)] = pos #group to a tracked cluster
        else: #Does not comply with mode shape criteria
            result_pairs[str(idx)] = "new"

    return result_pairs


def hypothesis_test(cluster,tracked_cluster, fig_ax1, fig_ax2, fig_ax3, fig_ax4):
    """
    Args:
    Returns:
    """
    n1 = len(cluster['row'])
    n2 = len(tracked_cluster['row'])
    dof = n1+n2-2
    alpha = (100-99.999)/100/2
    
    # student T-test
    t = stats.t.ppf(alpha,dof)

    y1 = np.mean(cluster['f'].copy())
    y2 = np.mean(tracked_cluster['f'].copy())
    s1 = cluster['global_std'][0,0]
    s2 = tracked_cluster['global_std'][0,0]
    
    delta_0 = 0
    sp2 = ((n1-1)*s1**2+(n2-1)*s2**2) / (dof)
    sp = sp2**0.5
    # student-t score
    t0 = (y1 - y2 - delta_0) / (sp * (1/n1 + 1/n2)**0.5)
    ci_lower = (y1-y2)+t*sp*(1/n1 + 1/n2)**0.5
    ci_upper = (y1-y2)-t*sp*(1/n1 + 1/n2)**0.5
    # print("Confidense interval:",ci_lower,ci_upper)

    test_result = (t,t0,ci_lower,ci_upper)

    # #Normaldistribution z-test
    # z_stat = (y1 - y2) / (sp / (n1)**0.5)
    # # 1. Calculate the Z-statistic
    # z = stats.norm.ppf(alpha)
    # # 2. Calculate the p-value (Two-tailed test)
    # if z_stat > 0:
    #     p_val = 2 * (1 - stats.norm.cdf(z_stat))
    # else:
    #     p_val = 2 * stats.norm.cdf(z_stat)

    # print("ttest_ind_from_stats: z = %g  z0 = %g" % (z_stat, z),t,t0)

    # test_result = (z,z_stat,ci_lower,ci_upper)

    # Use scipy.stats.ttest_ind.
    # t, p = ttest_ind(cluster['f'].copy(),tracked_cluster['f'].copy(),equal_var=False)
    # print("ttest_ind:            t = %g  p = %g" % (t, p))

    # Use scipy.stats.ttest_ind_from_stats.
    # t2, p2 = ttest_ind_from_stats(y1, s1, n1,
    #                             y2, s2, n2,
    #                             equal_var=False)
    # print("ttest_ind_from_stats: t = %g  p = %g" % (t2, p2),t,t0)

    return test_result, fig_ax1, fig_ax2, fig_ax3, fig_ax4

# def normplot(a,b,fig_ax=None):
#     # Generate sample data
#     # Calculate quantiles and least-square-fit curve
#     if fig_ax is None:
#         fig, (ax1,ax2) = plt.subplots(1,2,figsize=(12, 6), tight_layout=True)
#     else:
#         fig, (ax1,ax2) = fig_ax
#         ax1.clear()
#         ax2.clear()
    
#     (quantiles, values), (slope, intercept, r) = stats.probplot(a, dist='norm')
#     #plot results
#     ax1.plot(values, quantiles,'ob')
#     ax1.plot(quantiles * slope + intercept, quantiles, 'r')
    
#     (quantiles, values), (slope, intercept, r) = stats.probplot(b, dist='norm')
#     #plot results
#     ax2.plot(values, quantiles,'ob')
#     ax2.plot(quantiles * slope + intercept, quantiles, 'r')

#     #define ticks
#     ticks_perc=[1, 5, 10, 20, 50, 80, 90, 95, 99]

#     #transfrom them from precentile to cumulative density
#     ticks_quan=[stats.norm.ppf(i/100.) for i in ticks_perc]

#     #assign new ticks
#     ax1.set_yticks(ticks_quan,ticks_perc)
#     ax1.set_title("Normal Probability Plot")
#     ax2.set_yticks(ticks_quan,ticks_perc)
#     ax2.set_title("Normal Probability Plot")
#     #show plot
#     ax1.grid()
#     ax2.grid()
#     plt.show()

#     return fig, (ax1,ax2)

# def boxplot(a,b,fig_ax = None):
#     if fig_ax is None:
#         fig, (ax1,ax2) = plt.subplots(1,2,figsize=(12, 6), tight_layout=True)
#     else:
#         fig, (ax1,ax2) = fig_ax
#         ax1.clear()
#         ax2.clear()
#     bp = ax1.boxplot(a)
#     bp = ax2.boxplot(b)
#     ax1.grid()
#     ax2.grid()
#     plt.show()
    
#     return fig, (ax1,ax2)

# def histplot(a,b,fig_ax = None):
#     if fig_ax is None:
#         fig, (ax1,ax2) = plt.subplots(1,2,figsize=(12, 6), tight_layout=True)
#     else:
#         fig, (ax1,ax2) = fig_ax
#         ax1.clear()
#         ax2.clear()
#     ax1.hist(a)
#     ax1.set_title(f"Modes from cluster:{np.median(a)}")
#     ax2.hist(b)
#     ax2.set_title(f"Modes from cluster:{np.median(b)}")
    
#     return fig, (ax1,ax2)

# def distribution_overlap_plot(a,b,fig_ax = None):
#     if fig_ax is None:
#         fig, (ax1) = plt.subplots(1,1,figsize=(6, 6), tight_layout=True)
#     else:
#         fig, (ax1) = fig_ax
#         ax1.clear()

#     mu = np.mean(a['f'])

#     xlim = [min(min(a['f']),min(b['f']))-mu/60,max(max(a['f']),max(b['f']))+mu/60]
#     x_axis = np.arange(xlim[0], xlim[1], 0.00005)

#     std_dev = a['global_std'][0,0]
#     norm_pdf = norm.pdf(x_axis, mu, std_dev)
#     ax1.plot(x_axis, norm_pdf,color="r",label=f"{a['median_f']:.2f}")
#     ax1.axvline(mu,color="r")

#     mu = np.mean(b['f'])
#     std_dev = b['global_std'][0,0]
#     norm_pdf = norm.pdf(x_axis, mu, std_dev)
#     ax1.plot(x_axis, norm_pdf,color="b",label=f"{b['median_f']:.2f}")
#     ax1.axvline(mu,color="b")
#     ax1.legend()

#     return fig, (ax1)