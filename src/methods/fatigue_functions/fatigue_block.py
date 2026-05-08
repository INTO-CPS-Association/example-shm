from typing import Optional, Any
from datetime import datetime
import numpy as np

class fatigue():
    """Fatigue analysis functions"""
    """
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
        if plot == True:
            plot_data["0"] = time_series.copy() #Plot data:

        time_series = repeating_values(time_series) #Take care of repeated values before extremums are found

        if plot == True:
            plot_data["1"] = time_series.copy() #Plot data:

        time_series = extremes(time_series) #Reducing time_series to extreme points

        if plot == True:
            plot_data["2"] = time_series.copy() #Plot data:

        # time_series2 = time_series.copy()
        # idx = time_series.index(max(time_series))
        # time_series2.pop(idx)
        # print(max(time_series),max(time_series2))

        #Four-point rainflow counting
        result = {}
        i = 0
        stress_list = []
        mean_list = []
        n_list = []
        i2 = -1
        while ((i+3)<len(time_series)): #As long as the lenght of the remaining time series is longer than 3 values
                
            R1 = abs(time_series[i+1]-time_series[i])
            R2 = abs(time_series[i+2]-time_series[i+1]) #Middle line
            R3 = abs(time_series[i+3]-time_series[i+2])

            if (R2 <= R1) and (R2 <= R3): #If R2 is shorter than the surronding lines
                stress_mean = (time_series[i+2]+time_series[i+1])/2 #the mean of points of range 2
                Delta_stress = R2
                try: # If stress range and mean already exists add 1 to existing count
                    result[R2,stress_mean] += 1
                except: # If stress range and mean does not already exists
                    result[R2,stress_mean] = 1   
                stress_list.append(R2)
                mean_list.append(stress_mean)
                n_list.append(1)
                del time_series[i+2] # Delete the two points from the range just counted
                del time_series[i+1]
                i = 0

                if plot == True:
                    i2 += 1 #Plot data:
                    plot_data[str(i2+3)] = time_series.copy() #Plot data:
                
            else:
                i +=1

            #if len(time_series) < 3: #Exrta stop criterium
        
        stress_keys = list(result.keys())
        Delta_stress = [stress_keys[x][0] for x in range(len(stress_keys))] #Unpacking stress ranges from dictionary keys
        stress_mean = [stress_keys[x][1] for x in range(len(stress_keys))] #Unpacking stress ranges from dictionary keys
        n_count = list(result.values()) #unpacking counts from dictionary values

        if n_count == []: #If no counts are done, mainly done to prevent errors in later analysis.
            Delta_stress = [0]
            stress_mean = [0]
            n_count = [0]

        if output == "unique":
            return Delta_stress, stress_mean, n_count, time_series, plot_data
        else:
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
        
        # Given material data from [4]
        material_table = {'rolled_steel': [0.45, 0], 'cast_iron': [0.27, 85], 'ductile_cast_iron': [0.27, 100], 'laminar_cast_iron': [0.27, 110], 'Mallable_cast_iron': [0.39, 0]} #dictionary of material SN-curve parameters
        
        if material in material_table: #If material is know from dictionary
            alpha_0 = material_table[material][0]
            beta_0 = material_table[material][1]

            sigma_R_D_mat = alpha_0 * R_m + beta_0 #Calculate stress amplitude at knee point of SN-curve
            Delta_sigma_R_D_mat = sigma_R_D_mat*2

        else:
            #raise Exception("This is not a defined material")
            print("This is not a defined material. Curve-generator will proceed with standard values of alpha = 0.5 and beta = 0.")
            alpha_0 = 0.5
            beta_0 = 0
            sigma_R_D_mat = alpha_0 * R_m + beta_0 #Calculate stress amplitude at knee point of SN-curve for the material.
            Delta_sigma_R_D_mat = sigma_R_D_mat*2

        m1 = 5 #reciprocal slope of first slope (left most slope)
        m2 = m1*2-1 #reciprocal slope of second slope (right most slope. It is only used if the stress series consist of variable loading)
        N_D = 10**6 #Knee point
        C1_mat = N_D * Delta_sigma_R_D_mat**m1 #Calculating fatigue capacity of first slope of material SN-curve
        C2_mat = N_D * Delta_sigma_R_D_mat**m2 #Calculating fatigue capacity of second slope of material SN-curve
        

        Delta_sigma_R_D = Delta_sigma_R_D_mat * SF #Component or local stress amplitude at knee point
        C1 = N_D * Delta_sigma_R_D**m1 #Calculating fatigue capacity of first slope of component SN-curve
        C2 = N_D * Delta_sigma_R_D**m2 #Calculating fatigue capacity of second slope of component SN-curve
        
        sn_curve = { #Dictionary of SN-curves
            'DC': None,
            'N_D':[N_D],
            'C_mat':[C1_mat,C2_mat],
            'C':[C1,C2],
            'Delta_s_R_D_mat':[Delta_sigma_R_D_mat],
            'Delta_s_R_D':[Delta_sigma_R_D],
            'm':[m1,m2]}


        return sn_curve

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
        
        if material.lower()[0:2] == "al": #Test for valid DC
            DC_list = [12, 14, 16, 18, 20, 23, 25, 28, 32, 36, 40, 45, 50, 56, 63, 71, 80, 90, 100, 112, 125, 140]
        else:
            DC_list = [36,40,45,50,56,63,71,80,90,100,112,125,140,160]
        if not DC in DC_list:
            raise ValueError("The supplied DC is not known to EC SN-curves") 

        DC = DC/SF
        if material.lower()[0:2] == "al": #Aluminium
            try: #Test signal type, CA or VA, it must be supplied
                signal_type = kwargs["signal_type"].upper()
                if (signal_type == "VA") or (signal_type == "CA"):
                    pass
                else:
                    raise ValueError('Unknown signal type, use eg. signal_type = "VA" or "CA"')
            except:
                raise ValueError('Signal type must be specefied, eg. signal_type = "VA" or "CA"')

            if DC >= 71: #For large DC the slope is defined
                m1 = 7
                m2 = 7
                N_DC = 2*10**6 #Cycles at Detail Catagory
                N_D_CA = 2*10**6 #Cycles at constant amplitude
                N_D_VA = 10**8 #Cycles from knee-point to cut-off when the signal have variable amplitude
            else: #At other DC the slopes vary
                try:
                    m1 = kwargs["m1"]
                except:
                    raise ValueError("m1-slope must be provided")
                
                try: #Most DC have m2 as m1+2. So m2 is mostly not needed.
                    m2 = kwargs["m2"]
                except:
                    m2 = m1+2

                N_DC = 2*10**6 #Cycles at Detail Catagory
                N_D_CA = 5*10**6 #Cycles at constant amplitude
                N_D_VA = 10**8 #Cycles from knee-point to cut-off when the signal have variable amplitude

            #Calculate SN-curve parameters
            C1 = DC**m1*N_DC
            Delta_sigma_R_D = (C1/N_D_CA)**(1/m1)
            C2 = Delta_sigma_R_D**m2*N_D_CA
            Delta_sigma_R_L = (C2/N_D_VA)**(1/m2)

            if signal_type == "VA":
                sn_curve = { #Dictionary of SN-curve
                        'DC':DC,
                        'SF':SF,
                        'N_DC':N_DC,
                        'N_D':[N_D_CA,N_D_VA],
                        'C':[C1,C2],
                        'Delta_s_R_D':[Delta_sigma_R_D,Delta_sigma_R_L],
                        'm':[m1,m2,0]}
            else:
                sn_curve = { #Dictionary of SN-curve
                        'DC':DC,
                        'SF':SF,
                        'N_DC':N_DC,
                        'N_D':[N_D_CA],
                        'C':[C1],
                        'Delta_s_R_D':[Delta_sigma_R_D],
                        'm':[m1,0]}



        else: #Steel
            if stress_type.lower() == "sigma": # Normal stress
                try: #Test signal type, CA or VA, it must be supplied
                    signal_type = kwargs["signal_type"].upper()
                    if (signal_type == "VA") or (signal_type == "CA"):
                        pass
                    else:
                        raise ValueError('Unknown signal type, use eg. signal_type = "VA" or "CA"')
                except:
                    raise ValueError('Signal type must be specefied, eg. signal_type = "VA" or "CA"')

                try: #For override of slope
                    m1 = kwargs["m1"]
                except:
                    m1 = 3 #Slope
                try: #For override of slope
                    m2 = kwargs["m2"]
                except:
                    m2 = 5

                N_DC = 2*10**6 #Cycles at Detail Catagory
                N_D_CA = 5*10**6 #Cycles at constant amplitude
                N_D_VA = 10**8 #Cycles from knee-point to cut-off when the signal have variable amplitude
                
                #Calculate SN-curve parameters
                C1 = DC**m1*N_DC
                Delta_sigma_R_D = (C1/N_D_CA)**(1/m1)
                C2 = Delta_sigma_R_D**m2*N_D_CA
                Delta_sigma_R_L = (C2/N_D_VA)**(1/m2)

                if signal_type == "VA":
                    sn_curve = { #Dictionary of SN-curve
                            'DC':DC,
                            'SF':SF,
                            'N_DC':N_DC,
                            'N_D':[N_D_CA,N_D_VA],
                            'C':[C1,C2],
                            'Delta_s_R_D':[Delta_sigma_R_D,Delta_sigma_R_L],
                            'm':[m1,m2,0]}
                else:
                    sn_curve = { #Dictionary of SN-curve
                            'DC':DC,
                            'SF':SF,
                            'N_DC':N_DC,
                            'N_D':[N_D_CA],
                            'C':[C1],
                            'Delta_s_R_D':[Delta_sigma_R_D],
                            'm':[m1,0]}
            
            elif stress_type.lower() == "tau": # Shear stress
                try: #For override of slope
                    m1 = kwargs["m1"]
                except:
                    m1 = 5 #Slope
                N_DC = 2*10**6 #Cycles at Detail Catagory
                N_D = 1*10**8 #Cycles at constant amplitude

                #Calculate SN-curve parameters
                C1 = DC**m1*N_DC
                Delta_tau_R_D = (C1/N_D)**(1/m1)
                
                sn_curve = { #Dictionary of SN-curve
                            'DC':DC,
                            'SF':SF,
                            'N_DC':N_DC,
                            'N_D':[N_D],
                            'C':[C1],
                            'Delta_s_R_D':[Delta_tau_R_D],
                            'm':[m1,0]}
                
            elif stress_type.lower() == "sigma*":
                try: #Test signal type, CA or VA, it must be supplied
                    signal_type = kwargs["signal_type"].upper()
                    if (signal_type == "VA") or (signal_type == "CA"):
                        pass
                    else:
                        raise ValueError('Unknown signal type, use eg. signal_type = "VA" or "CA"')
                except:
                    raise ValueError('Signal type must be specefied, eg. signal_type = "VA" or "CA"')
                
                # Find the nearest DC above the given DC*
                DC_old = DC*SF
                
                result = next(k for k, value in enumerate(DC_list) if value > DC_old)
                DC_new = DC_list[result]/SF

                try: #For override of slope
                    m1 = kwargs["m1"]
                except:
                    m1 = 3 #Slope

                try: #For override of slope
                    m2 = kwargs["m2"]
                except:
                    m2 = 5
                N_DC = 2*10**6 #Cycles at Detail Catagory
                N_D_CA = 1*10**7 #Cycles at constant amplitude
                N_D_VA = 1*10**8 #Cycles at constant amplitude

                #Calculate SN-curve parameters
                C1 = DC_new**m1*N_DC
                Delta_sigma_R_D = (C1/N_D_CA)**(1/m1)
                C2 = Delta_sigma_R_D**m2*N_D_CA
                Delta_sigma_R_L = (C2/N_D_VA)**(1/m2)

                if signal_type == "VA":
                    sn_curve = { #Dictionary of SN-curve
                            'SN_type': "EC3",
                            'DC':DC,
                            'SF':SF,
                            'N_DC':N_DC,
                            'N_D':[N_D_CA,N_D_VA],
                            'C':[C1,C2],
                            'Delta_s_R_D':[Delta_sigma_R_D,Delta_sigma_R_L],
                            'm':[m1,m2,0]}
                else:
                    sn_curve = { #Dictionary of SN-curve
                            'SN_type': "EC3",
                            'DC':DC,
                            'SF':SF,
                            'N_DC':N_DC,
                            'N_D':[N_D_CA],
                            'C':[C1],
                            'Delta_s_R_D':[Delta_sigma_R_D],
                            'm':[m1,0]}
            else:
                raise ValueError('This is not a valid stress type. Try: "sigma", "tau" or "sigma*"')

        
        return sn_curve

    def IIW_SN(FAT: int, stress_type: str,SF: Optional[float] = 1,
               material: Optional[str] = "steel", **kwargs: Optional[Any])-> dict[str, Any]: #2024 version
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
        if material.lower()[0:2] == "al": #Test for valid FAT
            FAT_list = [71, 50, 45, 40, 36, 32, 28, 25, 22, 20, 18, 16, 14, 12]
        else:
            FAT_list = [160, 140, 125, 112, 100, 90, 80, 71, 61, 56, 50, 45, 40, 36]
        if not FAT in FAT_list:
            raise ValueError("The supplied FAT is not known to IIW SN-curves")
        
        try: #Test signal type, CA or VA, it must be supplied
            signal_type = kwargs["signal_type"].upper()
            if (signal_type == "CA") or (signal_type == "VA"):
                pass
            else:
                raise ValueError('Unknown signal type, use eg. signal_type = "VA" or "CA"')
        except:
            raise ValueError('Signal type must be specefied, eg. signal_type = "VA" or "CA"')


        FAT_list_alu = [50,45,40]

        FAT_ = FAT/SF
        if stress_type.lower() == "sigma":
            
            if material.lower()[0:2] == "al":
                try: #Slope override
                    m1 = kwargs["m1"]
                except:
                    if FAT >= 70:
                        m1 = 5
                    elif FAT in FAT_list_alu:
                        try:
                            m1 = kwargs["m1"]
                        except:
                            raise ValueError("m1 must be supplied in the case of FAT 50, 45, 40")
                    else:
                        m1 = 3
            else: #steel
                try: #Slope override
                    m1 = kwargs["m1"]
                except:
                    if FAT > 125:
                        m1 = 5
                    elif FAT == 125:
                        try:
                            m1 = kwargs["m1"]
                        except:
                            raise ValueError("m1 must be supplied in the case of FAT 125")
                    else:
                        m1 = 3
            try: #Slope override
                m2 = kwargs["m2"]
            except:
                if signal_type == "CA": #IIW 4.2.2
                    m2 = 22
                elif signal_type == "VA": #IIW 4.2.3
                    m2 = 2*m1-1
                else:
                    raise ValueError('Unknown signal type, use eg. signal_type = "VA" or "CA"')
        
            N_FAT = 2*10**6 #Cycles at Detail Catagory
            N_D = 10**7 #Cycles at constant amplitude

            #Calculate SN-curve parameters
            C1 = FAT_**m1*N_FAT
            Delta_sigma_R_D = (C1/N_D)**(1/m1)
            C2 = Delta_sigma_R_D**m2*N_D  

            #Limit curve at low cycle fatigue
            m0 = 5
            if material.lower()[0:2]  == "al":
                FAT_max = 71
            else:
                FAT_max = 160

            #Calculate interscetion with limit curve
            Cmax = FAT_max**m0*N_FAT
            Delta_sigma_R_max_1 = (Cmax/1)**(1/m0)
            Delta_sigma_R_FAT_1 = (C1/1)**(1/m1)
            if (Delta_sigma_R_FAT_1 >= Delta_sigma_R_max_1) and (m1 != m0):
                #Intersection
                a = C1**(1/m1)
                b = Cmax**(1/m0)
                N_D0 = (b/a)**(1/(-1/m1-(-1/m0)))
                Delta_sigma_R_U = (Cmax/N_D0)**(1/m0)

                sn_curve = { #Dictionary of SN-curve
                        'SN_type': "IIW",
                        'DC':FAT,
                        'SF':SF,
                        'N_DC':N_FAT,
                        'N_D':[N_D0,N_D],
                        'C':[Cmax,C1,C2],
                        'Delta_s_R_D':[Delta_sigma_R_U,Delta_sigma_R_D],
                        'm':[m0,m1,m2]}
            else:
                sn_curve = { #Dictionary of SN-curve
                        'SN_type': "IIW",
                        'DC':FAT,
                        'SF':SF,
                        'N_DC':N_FAT,
                        'N_D':[N_D],
                        'C':[C1,C2],
                        'Delta_s_R_D':[Delta_sigma_R_D],
                        'm':[m1,m2]}
        
        elif stress_type.lower() == "tau":
            try: #Slope override
                m1 = kwargs["m1"]
            except: 
                m1 = 5

            try: #Slope override
                m2 = kwargs["m2"]
            except:
                if signal_type == "CA": #IIW 4.2.2
                    m2 = 22
                elif signal_type == "VA": #IIW 4.2.3
                    m2 = 2*m1-1
                else:
                    raise ValueError('Unknown signal type, use eg. signal_type = "VA" or "CA"')
                
            N_FAT = 2*10**6 #Cycles at Detail Catagory
            N_D = 10**8 #Cycles at constant amplitude

            #Calculate SN-curve parameters
            C1 = FAT_**m1*N_FAT
            Delta_tau_R_D = (C1/N_D)**(1/m1)
            C2 = Delta_tau_R_D**m2*N_D
            
            sn_curve = { #Dictionary of SN-curve
                    'SN_type': "IIW",
                    'DC':FAT,
                    'SF':SF,
                    'N_DC':N_FAT,
                    'N_D':[N_D],
                    'C': [C1,C2],
                    'Delta_s_R_D':[Delta_tau_R_D],
                    'm':[m1,m2]}
        else:
            raise ValueError('This is not a valid stress type. Try: "sigma" or "tau"')

        return sn_curve

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
        #Initial values for some variables
        N_DC = 0
        C2 = 0
        Delta_sigma_R_L = 0
        m2 = -1 #if m2 == -1, then m2 does not exist. If m2 == 0 there are run-outs/cut-off
        k = 0
        detail = "None"
        t_ref = 25

        if (joint_type.lower() == "plate") or (joint_type.lower() == "pile") or (joint_type.lower() == "forged_node") or (joint_type.lower() == "cast_node") or (joint_type.lower() == "bolt") or (joint_type.lower() == "pipe"):
            t_ref = 25
            
            detail_list = ['B1','B2','C','C1','C2','D','E','F','F1','F3','G','W1','W2','W3']
            curves_air = {'B1':[4.0,106.97,0], #m, stress at N=10**7, k
                            'B2':[4.0,93.59,0],
                            'C':[3.0,73.10,0.05],
                            'C1':[3.0,65.50,0.1],
                            'C2':[3.0,58.48,0.15],
                            'D':[3.0,52.63,0.2],
                            'E':[3.0,46.78,0.2],
                            'F':[3.0,41.52,0.25],
                            'F1':[3.0,36.84,0.25],
                            'F3':[3.0,32.75,0.25],
                            'G':[3.0,29.24,0.25],
                            'W1':[3.0,26.32,0.25],
                            'W2':[3.0,23.39,0.25],
                            'W3':[3.0,21.05,0.25]          
                    }
            curves_seawater_cp = curves_air
            curves_seawater = {'B1':[12.436,0],#log_a_bar, k
                            'B2':[12.262,0],
                            'C':[12.115,0.05],
                            'C1':[11.972,0.1],
                            'C2':[11.824,0.15],
                            'D':[11.687,0.2],
                            'E':[11.533,0.2],
                            'F':[11.378,0.25],
                            'F1':[11.222,0.25],
                            'F3':[11.068,0.25],
                            'G':[10.921,0.25],
                            'W1':[10.784,0.25],
                            'W2':[10.630,0.25],
                            'W3':[10.493,0.25]          
                    }

            if (joint_type.lower() == "bolt"): #If bolt is chosen, try if stress_type is supplied
                try:
                    stress_type = kwargs['stress_type'].lower()
                except:
                    print("No stress type is given for the bolt. Default = tension is used.")
                    stress_type = "tension" #Default for bolts
            else:
                stress_type = "None" #No bolts present

            if (joint_type.lower() == "bolt") and (stress_type == "shear"):
                pass
            else:
                try: #Test if a sufficient detail is supplied
                    detail = kwargs["detail"].upper()
                    if detail in detail_list:
                        pass
                    else:
                        raise ValueError('Invalid detail. E.g. detail="B1"')
                except:
                    raise ValueError('Joint must be provided with a detail')
            
            if joint_type.lower() == "forges_node":
                pass
                #Removed code. It has been chosen that the user must themself provide the correct detail from code rules.
                # try:
                #     DFF = kwargs['DFF'] # Design fatigue factor
                #     if DFF >= 10:
                #         detail = "B1"
                #     else:
                #         detail = "C"
                # except:
                #     print("No DFF given. Default detail of C is choosen.")
                #     detail = "C"
            if joint_type.lower() == "cast_node":
                t_ref = 38 #Or reduced effective thickness

            if joint_type.lower() == "pipe":
            #Internal cyclic pressure is not available
                t_ref = 25

                pipe_detail = {'D':0.15,
                            'E':0,
                            'F':0,
                            'F1':0,
                            'D':0.15,
                            'C':0
                }

                try: #Test if detail is a pipe detail
                    detail = kwargs["detail"].upper()
                    if detail in pipe_detail:
                        pass
                    else:
                        raise ValueError('Invalid detail. E.g. detail="F1"')
                except:
                    pass          


            if (joint_type.lower() == "bolt") and (stress_type == "shear"): #If bolt is in shear
                    # The enviroment parameter is not needed
                    N_D = 0
                    m1 = 5
                    log_a_bar = 16.301
                    C1 = 10**log_a_bar
                    Delta_sigma_R_D = 0
                    k = 0 # Could not find a value
            else: #If no bolt or bolt in tension
                if enviroment.lower() == "air":
                    curves = curves_air
                    N_D = 10**7
                    N_DC = N_D
                    m1 = curves[detail][0]
                    m2 = 5
                    Delta_sigma_R_D = curves[detail][1]
                    C1 = Delta_sigma_R_D**m1*N_D
                    C2 = Delta_sigma_R_D**m2*N_D
                    if (joint_type.lower() == "bolt"): #Choose k depending on joint
                        k = 0.25 #2.4.3
                    elif (joint_type.lower() == "pipe"):
                        k = pipe_detail[detail][0]
                    else:
                        k = curves[detail][2]

                elif enviroment.lower() == "seawater_cp": #Seawater with cathodic protection
                    curves = curves_seawater_cp
                    N_D = 10**6
                    N_DC = 10**7
                    m1 = curves[detail][0]
                    m2 = 5
                    Delta_sigma_R_L = curves[detail][1]
                    C2 = Delta_sigma_R_L**m2*N_DC
                    Delta_sigma_R_D = (C2/N_D)**(1/m2)
                    C1 = Delta_sigma_R_D**m1*N_D
                    if (joint_type.lower() == "bolt"): #Choose k depending on joint
                        k = 0.25 #2.4.3
                    elif (joint_type.lower() == "pipe"):
                        k = pipe_detail[detail][0]
                    else:
                        k = curves[detail][2]

                elif enviroment.lower() == "seawater": #free corrotion
                    curves = curves_seawater
                    m1 = 3
                    N_DC = 10**7
                    N_D = 0
                    C1 = 10**curves[detail][0]
                    Delta_sigma_R_D = 0
                    if (joint_type.lower() == "bolt"): #Choose k depending on joint
                        k = 0.25 #2.4.3
                    elif (joint_type.lower() == "pipe"):
                        k = pipe_detail[detail][0]
                    else:
                        k = curves[detail][1]
                else:
                    raise ValueError('Unknown enviroment given. Try "air" or "seawater_cp"')
                
            #2.4.9 F.6 for spash zone and FPSO tanks
            #2.4.10 High strength steel D1 and D2
            #2.4.11 C-Mn steels?
                
            
        elif joint_type.lower() == "tubular":
            t_ref = 16
            
            if enviroment.lower() == "air":
                N_D = 10**7
                m1 = 3
                m2 = 5
                Delta_sigma_R_D = 67.09
                C1 = Delta_sigma_R_D**m1*N_D
                C2 = Delta_sigma_R_D**m2*N_D
                k = 0.25

            elif enviroment.lower() == "seawater_cp": #Seawater with cathodic protection
                N_D = 1.8*10**6
                N_DC = 10**7
                m1 = 3
                m2 = 5
                Delta_sigma_R_L = 67.09
                C2 = Delta_sigma_R_L**m2*N_DC
                Delta_sigma_R_D = (C2/N_D)**(1/m2)
                C1 = Delta_sigma_R_D**m1*N_D
                k = 0.25

            elif enviroment.lower() == "seawater": #free corrotion
                N_D = 0
                N_DC = 10**7
                m1 = 3
                log_a_bar = 12.03
                C1 = 10**log_a_bar
                Delta_sigma_R_D = 0
                k = 0.25

            else:
                raise ValueError('Unknown enviroment given. Try "air", "seawater_cp" or "seawater"')  
        
        elif joint_type.lower() == "strength_steel_tensile": #Sec. D.1
            # S-N curves for components of high strength steel (not cast steel) subjected to high mean tensile stress
            # For Steel (C-Mn)
            # Yield strength above 500 MPa
            # Surface rougness less or equal to R_a = 3.2µm
            # If requirements are not met use normal curves
            if enviroment.lower() == "air":
                N_D = 2*10**6
                m1 = 4.7
                m2 = 0
                Delta_sigma_R_D = 235
                log_a_bar = 17.446
                C1 = Delta_sigma_R_D**m1*N_D
                k = 0
    

            if enviroment.lower() == "seawater_cp":
                N_D = 0
                m1 = 4.7
                Delta_sigma_R_D = 0
                log_a_bar = 17.446
                C1 = 10**log_a_bar
                k = 0

        elif joint_type.lower() == "strength_steel_forged": #Sec. D.2
            # For carbon and low alloy machined steel forgings in compliance with DNVGL-RP-0034 steel forging class 2, 3 og equivalent.
            #The design S-N curves are valid for steels with tensile strength up to 862 MPa
            # (125 ksi) in air environment and 793 MPa (115 ksi) in seawater with cathodic protection.
            # It is further required that the yield to tensile strength ratio is no higher than 0.9.
            # Should only be used for VA and not CA.
            try:
                detail = kwargs["detail"].upper()
                if enviroment.lower() == "seawater_cp":
                    detail_list = ['BM1','BM2','BM3','BM4']
                    if detail in detail_list:
                        pass
                    else:
                        raise ValueError('Invalid detail. Eg. detail="BM1"')
                else:
                    detail_list = ['BM1','BM2','BM3','BM4','BM5']
                    if detail in detail_list:
                        pass
                    else:
                        raise ValueError('Invalid detail. Eg. detail="BM1"')
            except:
                raise ValueError('Joint must be provided with a detail')
            
            try:
                surf = kwargs["surf"]
            except:
                raise ValueError('Joint must be provided with a surface roughness, R_a [µm]. E.g. surf=3.2')


            if enviroment.lower() == "air":
                curves = {'BM1':[20.402,20.275], #Log_a_bar for Ra <= 3.2µm or Ra <= 6.4µm
                        'BM2':[20.728,20.576],
                        'BM3':[21.018,20.842],
                        'BM4':[21.279,21.078],
                        'BM5':[21.516,21.291],        
                }
                m1 = 6
                N_D = 0
                if surf <= 3.2:
                    C1 = 10**curves[detail][0]
                elif surf <= 6.4:
                    C1 = 10**curves[detail][0]
                else:
                    raise ValueError('Surface roughness too large, R_a > 6.4 µm')
                Delta_sigma_R_D = 0
                k = 0
    

            if enviroment.lower() == "seawater_cp":
                curves = {'BM1':[20.002,19.875],
                        'BM2':[20.328,20.176],
                        'BM3':[20.618,20.442],
                        'BM4':[20.879,20.678],        
                }
                m1 = 6
                N_D = 0
                if surf <= 3.2:
                    C1 = 10**curves[detail][0]
                elif surf <= 6.4:
                    C1 = 10**curves[detail][0]
                else:
                    raise ValueError('Surface roughness too large, R_a > 6.4 µm')
                Delta_sigma_R_D = 0
                k = 0
        elif joint_type.lower() == "umbilical":
            # The enviroment parameter is not needed
            # Small diameter pipe
            # outer diameter 10-100mm
            # Super duplex steel
            # Yield strength larger than 500 MPa
            # Thickness range from 1-10mm

            N_D = 10**7
            m1 = 4
            m2 = 5
            log_a_bar = 15.301
            C1 = 10**log_a_bar
            Delta_sigma_R_D = (C1/N_D)**(1/m1)
            C2 = Delta_sigma_R_D**m2*N_D
            k = 0.25


                #2.4.9 F.6 for splash zone and FPSO tanks
                #2.4.10 High strength steel D1 and D2
                #2.4.11 C-Mn steels?

        else:
            raise ValueError('Unknown joint type given. Try "plate", "tubular", "cast_nodes" or "forged_nodes')
        
        log_a_bar1 = np.log10(C1) #Calculates log_a_bar

        #Construct the SN-curve dictionary
        C = []
        m = []
        Delta_s_R_D = []
        log_a_bar = []
        if C2 != 0: #Build list of C
            C.append(C1)
            C.append(C2)
        else:
            C.append(C1)
        if m2 >= 0: #Build list of m
            m.append(m1)
            m.append(m2)
        elif m2 < 0:
            m.append(m1)
        
        if Delta_sigma_R_L != 0: #Build list of knee point stresses
            Delta_s_R_D.append(Delta_sigma_R_D)
            Delta_s_R_D.append(Delta_sigma_R_L)
        else:
            Delta_s_R_D.append(Delta_sigma_R_D)

        #Apply DFF and safety factor
        DFF = kwargs.get("DFF",1)
        SF  = kwargs.get("SF",1)
        for id, x in enumerate(Delta_s_R_D):
            Delta_s_R_D[id] = x*SF*DFF**(-1/3)
        for id,x in enumerate(C):
            C[id] = Delta_s_R_D[0]**m[id]*N_D
            log_a_bar_ = np.log10(C[id])
            log_a_bar.append(log_a_bar_ )

        sn_curve = { #Dictionary of SN-curve
                    'SN_type': "DNV",
                    'joint_type':joint_type.lower(),
                    'enviroment':enviroment.lower(),
                    'detail': detail,
                    'N_DC':N_DC,
                    'N_D':[N_D],
                    'C':C,
                    'log_a_bar':log_a_bar,
                    'Delta_s_R_D':Delta_s_R_D,
                    'm':m,
                    'k':k}

        return sn_curve

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
                        try:
                            res_mean.append(mean_list[i])
                        except:
                            pass
                        break
                    else:
                        break
        
        return cycles, n_cycles, res_stress, res_mean

    def damage(N1: list[float], n1: list[int],
               N2: Optional[list[float]] = [], n2: Optional[list[int]] = [], **kwargs) -> float | list[float]: #Palmgren-Miner damage
        """Calculate the Palmgren-Miner damage
        for both uni- and multiaxial stress ranges (sigma and tau). Multiaxial damage following Eurocode 3.
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

        try: #Try if the damage output should be summed or listed for all cycles
            list_D = kwargs["list_D"]
        except:
            list_D = False

        if (type(n1) == int) or (type(n1) == float): # If value given is not a list, then make it a list
            n1 = [n1]
        
        N1 = np.array(N1) #Use np.arrays
        n1 = np.array(n1)

        if list_D == True: #Output as list
            if N2 != []: #Multiaxial damage
                if (type(n2) == int) or (type(n2) == float):
                    n2 = [n2]
                
                N2 = np.array(N2)
                n2 = np.array(n2)
                D = np.array([np.multiply(n1,np.reciprocal(N1)),np.multiply(n2,np.reciprocal(N2))])


            else: # Uniaxial damage
                D = np.multiply(n1,np.reciprocal(N1)) #np.sum(n1*np.reciprocal(N1)) works too

        else: #Output as sum
            if N2 != []: #Multiaxial damage
                if (type(n2) == int) or (type(n2) == float):
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
    
    def EOF_RUL(result: dict[str, Any], time_passed: datetime, output_time_unit: Optional[str] = "hrs", damage_sum: Optional[float] = 1) -> tuple[float,float]:
        """End of life (EOF) or endurable life and Remaining useful life (RUL)

        Example 1:
        time_passed = 24 hr
        D_t = 0.1

        EOF = 240 hr #The end of life is at 240 hours
        RUL = (time_passed - EOF) = 226 hr #Remaining useful life (RUL) is then 226 hours

        Example 2:
        time_passed = 1,000,000 cycles
        D_t = 0.2

        EOF = 5,000,000 cycles #The end of life is at 5 mio. cycles.
        RUL = (time_passed - EOF) = 4,000,000 cycles #Remaining useful life (RUL) is then 4 mio. cycles
        
        Args:
            result (dict): Dictionary of results from continous data stream.
                - 'D_t' (float): New damage applied
            time_passed (int/datetime.timedelta): Specified cycles or time passed
            output_time_unit (int/datetime): Output unit for cycles or time       
        
        Returns:
            EOF (float): End of life (EOF) or endurable life
            RUL (float): Remaining useful life (RUL) 
        """

        d_tot = result["D_t"]

        if output_time_unit == "years":
            years = time_passed.days/365.25
            seconds = time_passed.seconds
            years_seconds = seconds/60/60/24/365.25
            time_elapsed = years + years_seconds
            
        elif output_time_unit == "days":
            days = time_passed.days
            seconds = time_passed.seconds
            days_seconds = seconds/60/60/24
            time_elapsed = days + days_seconds
        
        elif output_time_unit == "hrs":
            hr = time_passed.days*24
            seconds = time_passed.seconds
            hr_seconds = seconds/60/60
            time_elapsed = hr + hr_seconds
        
        elif output_time_unit == "cycles":
            time_elapsed = time_passed
        
        EOF = time_elapsed / (d_tot/damage_sum)
        RUL = EOF - time_elapsed

        return EOF, RUL

    def bin_func(xx: list[float], hist_data: dict[str, Any], **kwargs: Optional[Any]) -> tuple[list[int], list[float]]:
        """Plot SN curve

        Args:
        xx (List(float)): Stress list
        hist_data (dict): Previous histogram data. First iteration hist = {}
            -'hist' (List(int)): Previus histogram data
            -'bin_edges' (List(float)): Previus bin edges
        yy (List(float)): mean stress list, default = []
        **kwargs (any):
            - bin_width (int): Width of the bins default=10
            - bins (int): Override number of x bins to use, not recomended for continuous updating histogram

        Returns:
        hist (List(float)): Next histogram data
        x_edges (List(float): Next bin edges
        """
        
        def align_hist1D(xx: list[float], hist_prev: list[float], bins_prev: list[float], **kwargs: Optional[Any]) -> tuple[np.ndarray, list[float]]:
            """Aligns 1D histograms, such that they can be added together correctly

            Parameters
            ----------
            xx :   list of float
                Stress list
            hist_prev   :   array of int
                Previous histogram
            bins_prev  :   array of float
                Previous bin edges
            **kwargs    :   bin_width, int
                Width of the bins default=10
            **kwargs    :   bins, int
                Override number of x bins to use, not recomended for continuous updating histogram

            Outputs
            ----------
            hist        :   array
                New histogram
            bin_edges  :   Array of float
                bin edges
                
            """
            
            try:
                bin_width = kwargs.get("bin_width",10) #Get bin width if supplied
                rem1 = max(xx) % bin_width #Remainder
                rem2 = min(xx) % bin_width #Remainder
                nbins = ((max(xx)+bin_width-rem1-(min(xx)-rem2))//bin_width) #Calculate number of bins
                nbins = kwargs.get("bins",nbins) #Get number of bins if supplied, and override nbins

                #Find new histogram
                hist_new, bins_new = np.histogram(xx,bins=round(nbins),range=(round(min(xx)-rem2,2),round(max(xx)+bin_width-rem1,2))) #Histogram
                if (bins_new[1]-bins_new[0]) != bin_width:
                    hist_new, bins_new = np.histogram(xx,bins=round(nbins+1),range=(round(min(xx)-rem2,2),round(max(xx)+bin_width-rem1,2))) #Histogram

                #If the previous histogram does not exist
                if np.sum(hist_prev) == [0]:
                    hist_prev = np.array([0]*len(hist_new))
                    bins_prev = bins_new

                #Aligning by adding zeros around the arrays
                binwidth = round(bins_new[1]-bins_new[0],2)
                if min(bins_new) < min(bins_prev):
                    diff = round((min(bins_prev)-min(bins_new))/binwidth)
                    hist_prev = np.concatenate((np.zeros(diff),hist_prev))
                elif min(bins_new) > min(bins_prev):
                    diff = round((min(bins_new)-min(bins_prev))/binwidth)
                    hist_new = np.concatenate((np.zeros(diff),hist_new))
                
                if max(bins_new) < max(bins_prev):
                    diff = round((max(bins_prev)-max(bins_new))/binwidth)
                    hist_new = np.concatenate((hist_new,np.zeros(diff)))
                elif max(bins_new) > max(bins_prev):
                    diff = round((max(bins_new)-max(bins_prev))/binwidth)
                    hist_prev = np.concatenate((hist_prev,np.zeros(diff)))

                nbins = round((max(max(bins_new),max(bins_prev))-min(min(bins_new),min(bins_prev))) / (bins_new[1]-bins_new[0]) + 1)

                bin_edges = np.linspace(min(min(bins_new),min(bins_prev)),max(max(bins_new),max(bins_prev)),nbins)
                hist = np.add(hist_new,hist_prev) #Add hist counts together

                return hist.astype(dtype=np.int64), bin_edges
            except RuntimeError as e:
                print("binfunc Debug info", e)
                print(hist_prev)
                print(hist_new)
                print(len(hist_new),len(hist_prev))
                print(bins_prev)
                print(bins_new)
                print(len(bins_new),len(bins_prev))
                print(binwidth)
                print(diff)
        
        try:
            hist_prev = hist_data["hist"]
            bins_prev = hist_data["bin_edges"]
            
        except:
            hist_prev = np.zeros((1,1))
            bins_prev = [[],[]]

        #Align data
        hist, edges = align_hist1D(xx,hist_prev,bins_prev[0],**kwargs)
        
        return hist, edges
        
    def bin_func2D(xx: list[float], hist_data: dict[str,any],
                   yy: list[float], **kwargs: Optional[Any]) -> tuple[np.ndarray, list[float], list[float]]:
        """Plot SN curve

        Args:
        xx (List(float): Stress list
        hist_data (dict): Previous histogram data. First iteration hist = {}
            -'hist' (List(List(float))): Previus histogram data
            -'bin_edges' (List(float)): Previus bin edges
        yy (List(float): mean stress list, default = []
        **kwargs (any):
            - bin_width (int): Width of the bins default=10
            - xbin_width (int): Override width of the x bins default
            - ybin_width (int): Override width of the y bins default
            - xbins (int): Override number of x bins to use, not recomended for continuous updating histogram
            - ybins (int): Override number of y bins to use, not recomended for continuous updating histogram
            - bins (int): Override number of x bins to use, not recomended for continuous updating histogram

        Returns:
        hist (List(List(float))): Next histogram data
        x_edges (List(float): Next bin edges
        y_edges (List(float): Optional
        """
        def align_hist2D(xx: list[float], yy: list[float],
                         hist_prev: np.ndarray, xbins_prev: list[float],
                         ybins_prev: list[float], **kwargs: Optional[Any]) -> tuple[np.ndarray, list[float], list[float]]:
            """Aligns 2D histograms, such that they can be added together correctly

            Parameters
            ----------
            xx :   list of float
                Stress list
            yy  :   list of float
                mean stress list
            hist_prev   :   array2D of int
                Previous histogram
            xbins_prev  :   array of float
                Previous x bin edges
            ybins_prev  :   array of float
                Previous y bin edges
            **kwargs    :   bin_width, int
                Width of the bins default=10
            **kwargs    :   xbin_width, int
                Override width of the x bins default
            **kwargs    :   ybin_width, int
                Override width of the y bins default
            **kwargs    :   xbins, int
                Override number of x bins to use, not recomended for continuous updating histogram
            **kwargs    :   ybins, int
                Override number of y bins to use, not recomended for continuous updating histogram

            Outputs
            ----------
            hist        :   array2D of int
                Histogram
            xbin_edges  :   Array of float
                x bin edges
            ybin_edges  :   Array of float
                y bin edges
                
            """
            bin_width = kwargs.get("bin_width",10) #Get bin width if supplied
            lim_bin_width = 0.01
            if bin_width < lim_bin_width:
                print(f"Bin width can't be less than {lim_bin_width}. Going forth with bin_width = {lim_bin_width}")
                bin_width = lim_bin_width
            elif round(bin_width,2) != bin_width:
                bin_width = round(bin_width,2)
                print("Bin width can't have a precision less than 0.0. Going forth with bin_width =",bin_width)
            xbin_width = kwargs.get("xbin_width",bin_width) #Get bin width if supplied
            if xbin_width < lim_bin_width:
                print(f"x-bin width can't be less than {lim_bin_width}. Going forth with xbin_width = {lim_bin_width}")
                xbin_width = lim_bin_width
            elif round(xbin_width,2) != xbin_width:
                xbin_width = round(xbin_width,2)
                print("x-bin width can't have a precision less than 0.01. Going forth with xbin_width =",xbin_width)
            ybin_width = kwargs.get("ybin_width",bin_width) #Get bin width if supplied
            if ybin_width < lim_bin_width:
                print(f"y-bin width can't be less than {lim_bin_width}. Going forth with ybin_width = {lim_bin_width}")
                ybin_width = lim_bin_width
            elif round(ybin_width,2) != ybin_width:
                ybin_width = round(ybin_width,2)
                print("y-bin width can't have a precision less than 0.01. Going forth with ybin_width =",ybin_width)
            
            nbins_x = np.ceil(max(xx)/xbin_width) #Calculate number of bins
            nbins_x = kwargs.get("xbins",nbins_x) #Get number of bins if supplied, and override nbins
            nbins_y = (np.ceil(max(yy)/ybin_width)-np.floor(min(yy)/ybin_width)) #Calculate number of bins
            nbins_y = kwargs.get("ybins",nbins_y) #Get number of bins if supplied, and override nbins

            
            rem = max(xx) % xbin_width #Remainder
            rem2 = min(yy) % ybin_width #Remainder
            rem3 = max(yy) % ybin_width #Remainder

            #Find new histrogram
            hist_new, xbins_new, ybins_new = np.histogram2d(xx,yy,bins=(round(nbins_x),round(nbins_y)),range=((0,round(max(xx)+bin_width-rem,2)),(round(min(yy)-rem2,2),round(max(yy)+bin_width-rem3,2)))) #Histogram
            hist_new = np.transpose(hist_new)
            #If the previous histogram does not exist
            if np.sum(hist_prev) == [0]:
                hist_prev = np.zeros((hist_new.shape))
                xbins_prev = xbins_new
                ybins_prev = ybins_new
            

            xbinwidth = round(xbins_new[1]-xbins_new[0],2)
            ybinwidth = round(ybins_new[1]-ybins_new[0],2)

            #Aligning by adding zeros around the matricies
            try:
                if min(xbins_new) > min(xbins_prev):
                    diff = round((min(xbins_new)-min(xbins_prev))/xbinwidth)
                    # print(hist_new.shape)
                    hist_new = np.hstack((np.zeros((hist_new.shape[0],diff)),hist_new))
                    # if hist_new.shape[0] != hist_prev.shape[0]:
                    #     breakpoint()
                elif min(xbins_new) < min(xbins_prev):
                    diff = round((min(xbins_prev)-min(xbins_new))/xbinwidth)
                    # print(hist_prev.shape)
                    hist_prev = np.hstack((np.zeros((hist_prev.shape[0],diff)),hist_prev))
                    # if hist_new.shape[0] != hist_prev.shape[0]:
                    #     breakpoint()
                
                if min(ybins_new) > min(ybins_prev):
                    diff = round((min(ybins_new)-min(ybins_prev))/ybinwidth)
                    # print(hist_new.shape)
                    hist_new = np.vstack((hist_new,np.zeros((diff,hist_new.shape[1]))))
                    # if hist_new.shape[1] != hist_prev.shape[1]:
                    #     breakpoint()
                elif min(ybins_new) < min(ybins_prev):
                    diff = round((min(ybins_prev)-min(ybins_new))/ybinwidth)
                    # print(hist_prev.shape)
                    hist_prev = np.vstack((hist_prev,np.zeros((diff,hist_prev.shape[1]))))
                    # if hist_new.shape[1] != hist_prev.shape[1]:
                    #     breakpoint()
                
                if max(xbins_new) < max(xbins_prev):
                    diff = round((max(xbins_prev)-max(xbins_new))/xbinwidth)
                    # print(hist_new.shape)
                    hist_new = np.hstack((hist_new,np.zeros((hist_new.shape[0],diff))))
                    # if hist_new.shape[0] != hist_prev.shape[0]:
                    #     breakpoint()
                elif max(xbins_new) > max(xbins_prev):
                    diff = round((max(xbins_new)-max(xbins_prev))/xbinwidth)
                    # print(hist_prev.shape)
                    hist_prev = np.hstack((hist_prev,np.zeros((hist_prev.shape[0],diff))))
                    # if hist_new.shape[0] != hist_prev.shape[0]:
                    #     breakpoint()

                if max(ybins_new) < max(ybins_prev):
                    diff = round((max(ybins_prev)-max(ybins_new))/ybinwidth)
                    # print(hist_new.shape)
                    hist_new = np.vstack((np.zeros((diff,hist_new.shape[1])),hist_new))
                    # if hist_new.shape[1] != hist_prev.shape[1]:
                    #     breakpoint()
                elif max(ybins_new) > max(ybins_prev):
                    diff = round((max(ybins_new)-max(ybins_prev))/ybinwidth)
                    # print(hist_prev.shape)
                    hist_prev = np.vstack((np.zeros((diff,hist_prev.shape[1])),hist_prev))
                    # if hist_new.shape[1] != hist_prev.shape[1]:
                    #     breakpoint()

                #Added hisogram and bin edges
                hist = np.add(hist_new,hist_prev.astype(dtype=np.float64)) #Add hist counts together
            except RuntimeError as e:
                print("problem",e)
                breakpoint()
            nbins_x = hist.shape[1]
            nbins_y = hist.shape[0]
            xbin_edges = np.linspace(0,max(max(xbins_new),max(xbins_prev)),round(nbins_x)+1)
            ybin_edges = np.linspace(min(min(ybins_new),min(ybins_prev)),max(max(ybins_new),max(ybins_prev)),round(nbins_y)+1)
            

            return hist.astype(dtype=np.int64), xbin_edges, ybin_edges

        try:
            hist_prev = hist_data["hist"]
            bins_prev = hist_data["bin_edges"]
            
        except:
            hist_prev = np.zeros((1,1))
            bins_prev = [[],[]]

        #Align data
        hist, x_edges, y_edges = align_hist2D(xx,yy,hist_prev,bins_prev[0],bins_prev[1],**kwargs)
        
        return hist, x_edges, y_edges
