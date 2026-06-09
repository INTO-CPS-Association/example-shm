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
        phi_all = cluster['mode_shapes']

        MAC_list = []
        R_freq = []
        MAC_max_list = []
        greatest_interval = []
        t_test_list = []
        for key_t in tracked_clusters: #Go through all tracked clusters.
            #They are identified with keys which are integers from 0 up to total number of clusters
            if key_t == 'iteration':
                pass
                # if tracked_clusters[key_t] == 20:
                #     breakpoint()

            elif key_t in skip_tracked_cluster:
                    MAC_max_list.append(0)
                    R_freq.append(10**6)
                    greatest_interval.append([-1,-1])
                    t_test_list.append(False)
            else:
                #Accessing all cluster in a tracked cluster group
                tracked_cluster_list = tracked_clusters[key_t]
                l = params.get('l_lastest_clusters',1) #Number of tracked clusters to compare with
                n_last_tracked_clusters = np.min((len(tracked_cluster_list),l))
                freq_intervals = None
                list_of_tracked_clusters = []
                omega_t_list = []
                omega_mean_t_list = []
                t_test = False
                for ii in range(n_last_tracked_clusters):
                    tracked_cluster = tracked_cluster_list[-1*(ii+1)]
                    list_of_tracked_clusters.append(tracked_cluster)
                    
                    intervals = np.array([tracked_cluster['median_f']-tracked_cluster['global_ci'][0,0], tracked_cluster['median_f']+tracked_cluster['global_ci'][0,0]])
                    if freq_intervals is None:
                        freq_intervals = intervals
                    else:
                        freq_intervals = np.vstack((freq_intervals,intervals))
                    
                    #phi of last cluster in tracked cluster group
                    phi_t_all = tracked_cluster['mode_shapes']

                    omega_t_list.append(tracked_cluster['median_f'])
                    omega_mean_t_list.append(np.mean(tracked_cluster['f']))
                    MAC_matrix = np.zeros((phi_all.shape[0],phi_t_all.shape[0]))
                    for kk, phi in enumerate(phi_all):
                        for jj, phi_t in enumerate(phi_t_all):
                            MAC = float(calculate_mac(phi_t, phi))
                            #array to compare the cluster with all tracked clusters
                            MAC_matrix[kk,jj] = MAC
                    
                    test_result, fig_ax1, fig_ax2, fig_ax3, fig_ax4 = hypothesis_test(cluster,tracked_cluster, fig_ax1, fig_ax2, fig_ax3, fig_ax4)
                    t, t0, ci_lower, ci_upper = test_result
                    if abs(t0) < abs(t):
                        t_test = True

                # y_pop = np.mean(omega_t_list)
                # if len(omega_t_list) < 4:
                #     sigma = tracked_cluster['global_std'][0,0]**2
                # else:
                #     sigma = np.var(omega_t_list)
                #     print(omega_t_list)
                #     print("sigma",sigma)
                # y1 = cluster['median_f']
                # n1 = len(cluster['row'])
                # #Normaldistribution z-test
                # z_stat = (y1 - y_pop) / (sigma / (n1)**0.5)
                # # 1. Calculate the Z-statistic

                # # 2. Calculate the p-value (Two-tailed test)
                # if z_stat > 0:
                #     p_val = 2 * (1 - stats.norm.cdf(z_stat))
                # else:
                #     p_val = 2 * stats.norm.cdf(z_stat)

                
                # alpha = 0.05
                # if p_val > alpha:
                #     t_test_list.append(True)
                # else:
                #     t_test_list.append(False)

                # print(p_val,alpha)
   
                if t_test:
                    t_test_list.append(True)
                else:
                    t_test_list.append(False)
                # fig_ax1, fig_ax2, fig_ax3, fig_ax4 = hypothesis_test(cluster,tracked_cluster, fig_ax1, fig_ax2, fig_ax3, fig_ax4)

                MAC_max = np.max(MAC_matrix) #Max MAC value between cluster and tracked cluster
                MAC_max_list.append(MAC_max)
                #mean freq of median freq of l-last cluster in tracked cluster group
                omega_t = np.mean(omega_t_list)
                #For cases where the tracked cluster has a frequency of 0
                R_freq.append(abs(omega_t-omega)/omega_t) #Relative frequency difference

                if n_last_tracked_clusters > 1:
                    greatest_interval.append([np.min(freq_intervals[:,0],axis=0),np.max(freq_intervals[:,1],axis=0)])
                else:
                    greatest_interval.append(freq_intervals)
                
                # if MAC_max > params['phi_cri']:
                #     if (abs(omega_t-omega)/omega_t) < params['freq_cri']:
                #         print(omega,omega_t)
                #         tracked_cluster = tracked_cluster_list[-1]
                #         fig_ax1, fig_ax2, fig_ax3, fig_ax4 = hypothesis_test(cluster,tracked_cluster, fig_ax1, fig_ax2, fig_ax3, fig_ax4)
                

        greatest_interval = np.array(greatest_interval)

        #Find where the cluster matches the tracked cluster regarding the MAC criteria
        item_mask_1 = np.array(MAC_max_list) > params['phi_cri']
        #Find where the cluster matches the tracked cluster regarding the MAC and frequency criteria
        item_mask_2 = np.array(R_freq) < params['freq_cri']
        item_mask = np.logical_and(item_mask_1,item_mask_2)
        # print(item_mask_1)
        # print(item_mask_2)
        # print(item_mask)
        item_indices = np.argwhere(item_mask == True).reshape(-1)

        # Median of cluster must be inside interval for l-latest t-clusters
        lower_mask = (cluster['median_f'] - greatest_interval[:,0]) > 0
        upper_mask = (cluster['median_f'] - greatest_interval[:,1]) < 0

        #Interval of cluster must overlap with interval for l-latest t-clusters
        lower_mask = (cluster['median_f']+cluster['global_ci'][0,0] - greatest_interval[:,0]) > 0
        upper_mask = (cluster['median_f']-cluster['global_ci'][0,0] - greatest_interval[:,1]) < 0
        
        ci_match_mask = lower_mask==upper_mask
        mac_match_mask = np.array(MAC_max_list) > params['phi_cri']
        match_mask = np.logical_and(ci_match_mask,mac_match_mask)
        match_mask = np.logical_and(t_test_list,mac_match_mask)
        match_indicies = np.argwhere(match_mask==True).reshape(-1)

        # if omega > 60:
        #     print(omega)
        #     print(ci_match_mask)
        #     print(mac_match_mask)
        #     print(np.array(t_test_list))
        #     print(match_mask)
        #     print(match_indicies)
        #     print(item_indices)

        # match_indicies = item_indices
        if len(match_indicies) > 1: #If two or more clusters combly with the criteria
            X_list = []
            R_f_list = []
            MAC_list = []
            # print("R",R_freq)
            # print("M",MAC_max_list)
            for pos in match_indicies:
                # print("pow",pos)
                # print(R_freq[pos],MAC_max_list[pos])
                X = R_freq[pos]/MAC_max_list[pos] #Objective function
                X_list.append(X)
                R_f_list.append(R_freq[pos])
                MAC_list.append(MAC_max_list[pos])

            pos1 = X_list.index(min(X_list)) #Find the cluster that is most likely
            pos2 = MAC_list.index(max(MAC_list)) #Find the largest MAC
            pos3 = R_f_list.index(min(R_f_list)) #Find the smallest frequency difference
            #If one match on all three parameters:
            # print("pos",pos1,pos2,pos3)
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

                #Find the cluster that is most likely based on MAC
                pos2_2 = MAC_list_left.index(max(MAC_list_left))

                #Make different: abs(min(X_list_left)/min(X_list)) < params['obj_cri'] = 2
                #If the objective function results are close
                if abs(min(X_list_left)-min(X_list)) < params['obj_cri']:
                    # print("X")
                    # breakpoint()
                    #Cluster with the best MAC
                    if max(MAC_list_left) > max(MAC_list):
                        pos = int(match_indicies[pos2_2]) #Match with best MAC
                        result_pairs[str(idx)] = pos #group to a tracked cluster
                    else:
                        pos = int(match_indicies[pos2]) #Match with best X
                        result_pairs[str(idx)] = pos #group to a tracked cluster
                else: #If none of the above choose the one with lowest opjective function
                    # print("one is better")
                    # breakpoint()
                    pos = int(match_indicies[pos1])
                    result_pairs[str(idx)] = pos #group to a tracked cluster

        elif len(match_indicies) == 1: #If one cluster combly with the mode shape criteria
            # list_tracked_cluster_keys = list(tracked_clusters.keys())[1:]
            pos = int(match_indicies[0])
            # print("omega",omega,"Omega_t",tracked_clusters[str(pos)][-1]['median_f'])
            tracked_cluster_list = tracked_clusters[str(pos)]
            l = params.get('l_lastest_clusters',1) #Number of tracked clusters to compare with
            n_last_tracked_clusters = np.min((len(tracked_cluster_list),l))

            hyp_test_true = False
            for ii in range(n_last_tracked_clusters):
                tracked_cluster = tracked_cluster_list[-1*(ii+1)]
                test_result, fig_ax1, fig_ax2, fig_ax3, fig_ax4 = hypothesis_test(cluster,tracked_cluster, fig_ax1, fig_ax2, fig_ax3, fig_ax4)
                t, t0, ci_lower, ci_upper = test_result
                if abs(t0) < abs(t):
                    hyp_test_true = True
            
            # if hyp_test_true is True:
            #     print(f"Hypothesis test is accepted. Cluster is a member of tracked cluster. t_crit: {t:.3f}, t0: {t0:.3f}")
            #     print("Confidence interval",ci_lower,ci_upper)
            # else:
            #     print(f"Hypothesis test is discarded. Cluster is not a member of tracked cluster. t_crit: {t:.3f}, t0: {t0:.3f}")
            #     print("Confidence interval",ci_lower,ci_upper)
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
    alpha = (100-95)/100/2
    
    # student T-test
    t = stats.t.ppf(alpha,dof)
    # print("Critical value",t)

    y1 = np.mean(cluster['f'].copy())
    y2 = np.mean(tracked_cluster['f'].copy())
    s1 = cluster['global_std'][0,0]
    s2 = tracked_cluster['global_std'][0,0]
    
    delta_0 = 0
    sp2 = ((n1-1)*s1**2+(n2-1)*s2**2) / (dof)
    sp = sp2**0.5
    t0 = (y1 - y2 - delta_0) / (sp * (1/n1 + 1/n2)**0.5)
    # print("t0:",t0)
    # if abs(t0) < abs(t):
    #     test_result = f"Hypothesis test is accepted. Cluster is a member of tracked cluster. t_crit: {t:.3f}, t0: {t0:.3f}"
    # else:
    #     if test_result is None:
    #         test_result = f"Hypothesis test is discarded. Cluster is not a member of tracked cluster. t_crit: {t:.3f}, t0: {t0:.3f}"
    ci_lower = (y1-y2)+t*sp*(1/n1 + 1/n2)**0.5
    ci_upper = (y1-y2)-t*sp*(1/n1 + 1/n2)**0.5
    # print("Confidense interval:",ci_lower,ci_upper)


    # #Normaldistribution z-test
    # z_stat = (y1 - y2) / (sp / (n1)**0.5)
    # # 1. Calculate the Z-statistic
    # z = stats.norm.ppf(1-alpha)
    # # 2. Calculate the p-value (Two-tailed test)
    # if z_stat > 0:
    #     p_val = 2 * (1 - stats.norm.cdf(z_stat))
    # else:
    #     p_val = 2 * stats.norm.cdf(z_stat)

    # # print(f"Z-statistic: {z_stat:.3f}")
    # # print(f"P-value: {p_val:.3f}")
    # if p_val > alpha:
    #     print("This is statistically likely:",p_val, alpha,"Cluster:",y1,y2)
    # if abs(z_stat) < abs(z):
    #     print("This is statistically likely:",z_stat, z,"Cluster:",y1,y2)
    # if abs(t0) < abs(t):
    #     print("This is statistically likely:",abs(t0),"<",abs(t),"Cluster:",y1,y2)
    
    # test_result = (p_val,alpha,ci_lower,ci_upper)
    # test_result = (z,z_stat,ci_lower,ci_upper)


    test_result = (t,t0,ci_lower,ci_upper)

    # fig_ax1 = normplot(cluster['f'],tracked_cluster['f'],fig_ax=fig_ax1)
    # fig_ax2 = boxplot(cluster['f'],tracked_cluster['f'],fig_ax=fig_ax2)
    # fig_ax3 = histplot(cluster['f'],tracked_cluster['f'],fig_ax=fig_ax3)
    # fig_ax4 = distribution_overlap_plot(cluster,tracked_cluster,fig_ax=fig_ax4)

    # t_result = ttest_ind(cluster['f'].copy(),tracked_cluster['f'].copy(),equal_var=False)
    # print(t_result)

    

    # # Compute the descriptive statistics of a and b.
    # abar = y1
    # avar = s1_2
    # na = n1
    # adof = na - 1

    # bbar = y2
    # bvar = s2_2
    # nb = n2
    # bdof = nb - 1

    # # Use scipy.stats.ttest_ind.
    # t, p = ttest_ind(cluster['f'].copy(),tracked_cluster['f'].copy(),equal_var=False)
    # print("ttest_ind:            t = %g  p = %g" % (t, p))

    # # Use scipy.stats.ttest_ind_from_stats.
    # t2, p2 = ttest_ind_from_stats(abar, np.sqrt(avar), na,
    #                             bbar, np.sqrt(bvar), nb,
    #                             equal_var=False)
    # print("ttest_ind_from_stats: t = %g  p = %g" % (t2, p2))

    # # Use the formulas directly.
    # from scipy.special import stdtr
    # tf = (abar - bbar) / np.sqrt(avar/na + bvar/nb)
    # dof = (avar/na + bvar/nb)**2 / (avar**2/(na**2*adof) + bvar**2/(nb**2*bdof))
    # pf = 2*stdtr(dof, -np.abs(tf))

    # print("formula:              t = %g  p = %g" % (tf, pf))

    # breakpoint()

    return test_result, fig_ax1, fig_ax2, fig_ax3, fig_ax4

def normplot(a,b,fig_ax=None):
    # Generate sample data
    # Calculate quantiles and least-square-fit curve
    if fig_ax is None:
        fig, (ax1,ax2) = plt.subplots(1,2,figsize=(12, 6), tight_layout=True)
    else:
        fig, (ax1,ax2) = fig_ax
        ax1.clear()
        ax2.clear()
    
    (quantiles, values), (slope, intercept, r) = stats.probplot(a, dist='norm')
    #plot results
    ax1.plot(values, quantiles,'ob')
    ax1.plot(quantiles * slope + intercept, quantiles, 'r')
    
    (quantiles, values), (slope, intercept, r) = stats.probplot(b, dist='norm')
    #plot results
    ax2.plot(values, quantiles,'ob')
    ax2.plot(quantiles * slope + intercept, quantiles, 'r')

    #define ticks
    ticks_perc=[1, 5, 10, 20, 50, 80, 90, 95, 99]

    #transfrom them from precentile to cumulative density
    ticks_quan=[stats.norm.ppf(i/100.) for i in ticks_perc]

    #assign new ticks
    ax1.set_yticks(ticks_quan,ticks_perc)
    ax1.set_title("Normal Probability Plot")
    ax2.set_yticks(ticks_quan,ticks_perc)
    ax2.set_title("Normal Probability Plot")
    #show plot
    ax1.grid()
    ax2.grid()
    plt.show()

    return fig, (ax1,ax2)

def boxplot(a,b,fig_ax = None):
    if fig_ax is None:
        fig, (ax1,ax2) = plt.subplots(1,2,figsize=(12, 6), tight_layout=True)
    else:
        fig, (ax1,ax2) = fig_ax
        ax1.clear()
        ax2.clear()
    bp = ax1.boxplot(a)
    bp = ax2.boxplot(b)
    ax1.grid()
    ax2.grid()
    plt.show()
    
    return fig, (ax1,ax2)

def histplot(a,b,fig_ax = None):
    if fig_ax is None:
        fig, (ax1,ax2) = plt.subplots(1,2,figsize=(12, 6), tight_layout=True)
    else:
        fig, (ax1,ax2) = fig_ax
        ax1.clear()
        ax2.clear()
    ax1.hist(a)
    ax1.set_title(f"Modes from cluster:{np.median(a)}")
    ax2.hist(b)
    ax2.set_title(f"Modes from cluster:{np.median(b)}")
    
    return fig, (ax1,ax2)

def distribution_overlap_plot(a,b,fig_ax = None):
    if fig_ax is None:
        fig, (ax1) = plt.subplots(1,1,figsize=(6, 6), tight_layout=True)
    else:
        fig, (ax1) = fig_ax
        ax1.clear()

    mu = np.mean(a['f'])

    xlim = [min(min(a['f']),min(b['f']))-mu/60,max(max(a['f']),max(b['f']))+mu/60]
    x_axis = np.arange(xlim[0], xlim[1], 0.00005)

    std_dev = a['global_std'][0,0]
    norm_pdf = norm.pdf(x_axis, mu, std_dev)
    ax1.plot(x_axis, norm_pdf,color="r",label=f"{a['median_f']:.2f}")
    ax1.axvline(mu,color="r")

    mu = np.mean(b['f'])
    std_dev = b['global_std'][0,0]
    norm_pdf = norm.pdf(x_axis, mu, std_dev)
    ax1.plot(x_axis, norm_pdf,color="b",label=f"{b['median_f']:.2f}")
    ax1.axvline(mu,color="b")
    ax1.legend()

    return fig, (ax1)