from typing import Optional, Any
import numpy as np
from methods.fatigue_functions.synthetic import synthetic_sn
from methods.fatigue_functions.eurocode import eurocode_sn
from methods.fatigue_functions.IIW import iiw_sn
from methods.fatigue_functions.DNV import dnv_sn
# pylint: disable=C0103, C0301, R0912, R0914, R0915, R1702

"""Fatigue analysis functions
[1] Four-point rainflow counting https://doi.org/10.1016/0142-1123(94)90343-3. Standardization of the rainflow counting method for fatigue analysis C. Amzallag et al.
[2] Rainflow counting for continuous data https://doi.org/10.1016/j.ijfatigue.2015.10.007

Definitions:
sigma: normal stress
tau: shear stress

sigma_a: stress amplitude
Delta_sigma: stress range (2*amplitude)
sigma_m: mean stress

N: fatigue life, i.e. number of cycles
N_D: cycles at knee point (subscript D indicates knee point)

sigma_R: fatigue strength (subscript R indicates resistance)
sigma_R_D: fatigue strength at knee point
sigma_R_D_mat: fatigue strength of material at knee point

R_m: tensile strength (ultimate)

C: Fatigue capacity, a log-linear curves (power function) intersection with the x-axis (cycles)
log_a_bar: is the log10 of fatigue capacity (used in DNV: C = 10**log_a_bar)

SF: Safety factor

DC,FAT,detail: Detail catagory from code
"""

def rainflow_c(series: list[float],
                residual: Optional[list[float]] = None,
                output: str="unique",
                plot: bool=False) -> tuple[list[float], list[float],
                                            list[int], list[float],
                                            dict[str, list[float]]]:
    """Continuous rainflow counting implemented as four-point counting

    Four-point rainflow counting following [1]
    NB: Does not double count the residual! [2]

    Args:
        time_series (list(float)): List of stress or load time series
        residual (list(float)): Previous residual for continuous evaluation
        output (str): Choose between unique list or full list output
        plot (bool): Return plot data

    Returns:
        Delta_stress (list(float)): List if stress ranges counted
        sigma_mean (list(float)): List of mean of the stress ranges
        n_count (list(float)): List of counts of each stress range (and associated stress mean)
        time_series ():
        plot_data ():
    """

    # Reapeating values are scaled down a tiny bit,
    # so the extremes() function can keep the extremes
    def repeating_values(time_series):
        for i in range(len(time_series)-1):
            if time_series[i] == time_series[i+1]: #If consecutive values are identical
                time_series[i+1] = time_series[i+1]*0.999999
        return time_series

    # Reducing time series to extremum points
    def extremes(time_series):
        time_series_extremes = [time_series[0]] # Keep the first value of the time series
        for i in range(1,len(time_series)-1):
            if (time_series[i]>time_series[i-1]) and (time_series[i]>time_series[i+1]): # If point is a maximum
                time_series_extremes.append(time_series[i])
            if (time_series[i]<time_series[i-1]) and (time_series[i]<time_series[i+1]): # If point is a minimum
                time_series_extremes.append(time_series[i])
        time_series_extremes.append(time_series[-1]) # Keep the last value of the time series
        return time_series_extremes

    time_series = series.copy()

    if residual != []: #If residual is not empty
        time_series = residual+time_series #Add residual before time series

    if (max(time_series) == min(time_series)) or (len(time_series)<3): #Test to verify the time series is valid for rainflow counting
        raise Exception('Time series is either too short or flat')

    plot_data = {} #Plot data:
    if plot is True:
        plot_data["0"] = time_series.copy() #Plot data:

    time_series = repeating_values(time_series) #Take care of repeated values before extremums are found

    if plot is True:
        plot_data["1"] = time_series.copy() #Plot data:

    time_series = extremes(time_series) #Reducing time_series to extreme points

    if plot is True:
        plot_data["2"] = time_series.copy() #Plot data:

    #Four-point rainflow counting
    result = {}
    i = 0
    stress_list = []
    mean_list = []
    n_list = []
    i2 = -1
    while (i+3)<len(time_series): #As long as the lenght of the remaining time series is longer than 3 values
        R1 = abs(time_series[i+1]-time_series[i])
        R2 = abs(time_series[i+2]-time_series[i+1]) #Middle line
        R3 = abs(time_series[i+3]-time_series[i+2])

        if (R2 <= R1) and (R2 <= R3): #If R2 is shorter than the surronding lines
            stress_mean = (time_series[i+2]+time_series[i+1])/2 #the mean of points of range 2
            Delta_stress = R2
            try: # If stress range and mean already exists add 1 to existing count
                result[R2,stress_mean] += 1
            except KeyError: # If stress range and mean does not already exists
                result[R2,stress_mean] = 1
            stress_list.append(R2)
            mean_list.append(stress_mean)
            n_list.append(1)
            del time_series[i+2] # Delete the two points from the range just counted
            del time_series[i+1]
            i = 0

            if plot is True:
                i2 += 1 #Plot data:
                plot_data[str(i2+3)] = time_series.copy() #Plot data:

        else:
            i +=1

        #if len(time_series) < 3: #Exrta stop criterium

    stress_keys = list(result.keys())
    #Unpacking stress ranges from dictionary keys
    Delta_stress = [stress_keys[x][0] for x in range(len(stress_keys))]
    #Unpacking stress ranges from dictionary keys
    stress_mean = [stress_keys[x][1] for x in range(len(stress_keys))]
    n_count = list(result.values()) #unpacking counts from dictionary values

    if not n_count: #If no counts are done, mainly done to prevent errors in later analysis.
        Delta_stress = [0]
        stress_mean = [0]
        n_count = [0]

    if output == "unique":
        return Delta_stress, stress_mean, n_count, time_series, plot_data
    return stress_list, mean_list, n_list, time_series, plot_data

def synthetic_SN(material: str, R_m: float, SF: Optional[float] = 1) -> dict[str, Any]:
    """Synthetic SN curve generator.
    Generates SN curves from material data and safety factors.

    Definitions:
    cast_iron (GS)
    ductile_cast_iron (GJS)
    laminar_cast_iron (GJL)
    Mallable_cast_iron (GTS)

    Args:
        material (str): Material to build SN curve for [4]
        R_M (float): Ultimate tenstile strength
        SF (float): Safety factor from k_reliab * k_mean * k_size * k_env * k_surf * n (n = notch support factor, comes from K_f and K_t)

    Returns:
        sn_curve (dict): Dictionary consisting of SN curve parameters.
            - 'DC' (int): Detail catagory.
            - 'SF' (float): Safty factor.
            - 'N_DC' (int): Fatigue life at detail catagoy.
            - 'N_D' (List(int)): Fatigue life at knee points.
            - 'C' (List(float)): Fatigue capacity.
            - 'Delta_s_R_D' (List(float)): Fatigue limit at knee point(s).
            - 'm' List(int): SN-curve slope(s).
    """
    return synthetic_sn(material, R_m, SF)

def eurocode_SN(DC: int, stress_type: str, SF: Optional[float]=1,
                material: Optional[str] = "steel",**kwargs: Optional[Any]) -> dict[str, Any]:
    """Eurocode 2007 SN curves
    Generates SN curves from a given detail catagory, stress type and safety factor.

    Args:
        DC (int): Detail catagory.
        stress_type (str): Either 'sigma' (normal), 'tau' (shear) or alternative 'sigma*'.
        SF (float): Safety factor from Eurocode.
        material (str): Steel or aluminium (al). For aluminium maximum principle stress should be used.
    **kwargs (any):
        - signal_type (str): CA (Constant amplitude) or VA (Variable amplitude) signal.
        - m1 (int): different slope override.
        - m2 (int): different slope override.

    returns:
        sn_curve (dict): Dictionary consisting of SN curve parameters.
            - 'DC' (int): Detail catagory.
            - 'SF' (float): Safty factor.
            - 'N_DC' (int): Fatigue life at detail catagoy.
            - 'N_D' (List(int)): Fatigue life at knee points.
            - 'C' (List(float)): Fatigue capacity.
            - 'Delta_s_R_D' (List(float)): Fatigue limit at knee point(s).
            - 'm' List(int): SN-curve slope(s).

    """
    return eurocode_sn(DC, stress_type, SF, material, **kwargs)

def IIW_SN(FAT: int, stress_type: str,SF: Optional[float] = 1,
            material: Optional[str] = "steel", **kwargs: Optional[Any])-> dict[str, Any]:
    """International insitute of welding (IIW) fatigue SN curves
    Generates SN curves from a given FAT catagory, stress type and safety factor

    Args:
        FAT (int): Fatigue catagory.
        stress_type (str): Either 'sigma' (normal), 'tau' (shear).
        SF (float): Safety factor.
        material (str): Steel or aluminium (al). For aluminium maximum principle stress should be used.
    **kwargs (any):
        - signal_type (str): CA (Constant amplitude) or VA (Variable amplitude) signal.
        - m1 (int): different slope override.
        - m2 (int): different slope override.

    returns:
        sn_curve (dict): Dictionary consisting of SN curve parameters.
            - 'DC' (int): Detail catagory.
            - 'SF' (float): Safty factor.
            - 'N_DC' (int): Fatigue life at detail catagoy.
            - 'N_D' (List(int)): Fatigue life at knee points.
            - 'C' (List(float)): Fatigue capacity.
            - 'Delta_s_R_D' (List(float)): Fatigue limit at knee point(s).
            - 'm' List(int): SN-curve slope(s).

    Definitions
    ------
    FAT = DC in IIW language
    """
    return iiw_sn(FAT, stress_type, SF, material, **kwargs)

def DNV_SN(joint_type: str,enviroment: str,**kwargs: Optional[Any])-> dict[str, Any]: #2016 version
    """DNV fatigue

    Args:
        joint_type (str): Type of joint.
        enviroment (str): Enviroment type: 'air', 'seawater_cp' with cathodic protection and 'seawater' with free corrosion.
        **kwargs (any):
            - Detail (str): SN curve detail.
            - surf (float): Surface roughness.
            - stress_type (str): for bolts either in 'shear' or 'tension'
            - DFF (int): Design fatigue factor.
            - SF (float): Safety factor.

    Returns:
        sn_curve (dict): Dictionary consisting of SN curve parameters.
                - 'SN_type' (str): Standard SN-curve is based on.
                - 'joint_type' (str): Type of joint.
                - 'enviroment' (str): Type of enviroment.
                - 'detail' (str): DNV detail.
                - 'SF' (float): Safty factor.
                - 'N_DC' (int): Fatigue life at detail catagoy.
                - 'N_D' (List(int)): Fatigue life at knee points.
                - 'C' (List(float)): Fatigue capacity.
                - 'log_a_bar' (List(float)): log10 of C,
                - 'Delta_s_R_D' (List(float)): Fatigue limit at knee point(s).
                - 'm' List(int): SN-curve slope(s).
                - 'k' (float): size exponent.

    """
    return dnv_sn(joint_type, enviroment, **kwargs)

def cycles_SN(sn_curve: dict[str, Any], stress_list: list[float],
                n_count: list[int], mean_list: list[float])-> tuple[list[float], list[int],
                                                                    list[float], list[float]]:
    """Finds the fatigue life associated with a given stress range from the given SN curve

    Args:
        sn_curve (dict): SN curve parameters in a dictionary.
        stress_list (List(float)): List of stress ranges that is to be iterated over.
        n_count (List(float)): List of counts.
        mean_list (List(float)): List of means.

    Returns:
        cycles (List(float)): List of fatigue life cycles (N).
        n_cycles (List(float)): List of of counts associated with the significant stress ranges.
        res_stress (List(float)): List of significant stress ranges.
        res_mean (List(float)): List of mean stress associated to significant stress.
    """

    if stress_list == [0]: #error handling if rainflow results in 0 counts
        return [0], [0], [0], [0]

    cycles = []
    n_cycles = [] #Cycle count list for significant stresses
    res_stress = [] #Stress list for significant stresses
    res_mean = [] #Mean stress list

    m = sn_curve['m']
    knee_stress = sn_curve['Delta_s_R_D'].copy()
    if m[-1] != 0: #If there are no cut-offs
        knee_stress.append(0) #This allows for cycle counting for all stress ranges.
    C = sn_curve['C']
    knees = len(knee_stress)
    for i, x in enumerate(stress_list): #For all stresses
        for j in range(knees): #Test if stress is above all knees
            if x > knee_stress[j]: #Is stress above knee?
                N = C[j]/(x**m[j])
                if not np.isinf(N): #if value is not infinite
                    res_stress.append(x)
                    cycles.append(C[j]/(x**m[j]))
                    n_cycles.append(n_count[i])
                    res_mean.append(mean_list[i])
                break

    return cycles, n_cycles, res_stress, res_mean

def damage(N1: list[float], n1: list[int],
            N2: Optional[list[float]] = None,
            n2: Optional[list[int]] = None, **kwargs) -> float | list[float]: #Palmgren-Miner damage
    """Calculate the Palmgren-Miner damage
    for both uni- and multiaxial stress ranges (sigma and tau).
    Multiaxial damage following Eurocode 3.
    IIW uses Gough-Pollard elipse to asses multiaxial stress state in welds. (Not implemented)

    Args:
        N1 (List(float)): cycles.
        n1 (List(int)): counts.
        N2 (List(float)): cycles for second direction (Optional).
        n2 (List(int)): counts (Optional)
    **kwargs: (any)
        - list_D (bool): Gives a listed result enstead of accumulated result (Optional)

    Returns:
        - damage (float/List(float)): Damage
    """
    if N1 == [0]: #If no cycles are counted
        return 0, 0

    #Try if the damage output should be summed or listed for all cycles
    list_D = kwargs.get("list_D",False)

    if isinstance(n1,(int,float)): # If value given is not a list, then make it a list
        n1 = [n1]

    N1 = np.array(N1) #Use np.arrays
    n1 = np.array(n1)

    if list_D is True: #Output as list
        if N2 is not None: #Multiaxial damage
            if isinstance(n2,(int,float)):
                n2 = [n2]

            N2 = np.array(N2)
            n2 = np.array(n2)
            D = np.array([np.multiply(n1,np.reciprocal(N1)),np.multiply(n2,np.reciprocal(N2))])

        else: # Uniaxial damage
            D = np.multiply(n1,np.reciprocal(N1)) #np.sum(n1*np.reciprocal(N1)) works too

    else: #Output as sum
        if N2 is not None: #Multiaxial damage
            if isinstance(n2,(int,float)):
                n2 = [n2]
            N2 = np.array(N2)
            n2 = np.array(n2)
            D = np.matmul(n1,np.reciprocal(N1)) + np.matmul(n2,np.reciprocal(N2))

        else: # Uniaxial damage
            D = np.matmul(n1,np.reciprocal(N1)) #np.sum(n1*np.reciprocal(N1)) works too

    return D.tolist() #Convert back to native float/list from np.float/np.array

def damage_accum(result: dict[str, Any], prev_result: dict[str, Any]) -> dict[str, Any]:
    """Accumulate damage for a continuous data stream
    
    Args:
        result (dict): Dictionary of results from continous data stream.
            - 'D' (float): Damage from batch
            - 'D_residual' (float): Damage from residual signal
        prev_result (dict): Dictionary of previous results from continous data stream
            - 'D_accum' (float): Accumulated damage without residual damage
    
    Returns:
        result (dict): Dictionary of results from continous data stream
            - 'D_accum' (float): Accumulated damage without residual damage
            - 'D_t' (float): Accumulated damage total with residual damage (D_accum + D_res)
    """

    D = result["D"]
    D_res = result["D_residual"]

    if prev_result == {}:
        result["D_accum"] = D
        result["D_t"] = D + D_res
    else:
        D_accum = prev_result["D_accum"]
        result["D_accum"] = D_accum + D
        result["D_t"] = result["D_accum"] + D_res

    return result
