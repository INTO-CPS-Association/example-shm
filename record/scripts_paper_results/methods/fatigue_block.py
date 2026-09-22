import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.sans-serif'] = 'cm'
plt.rcParams['mathtext.fontset'] = 'cm'
plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams.update({'font.size': 16})
mpl.rcParams['xtick.labelsize'] = 12
mpl.rcParams['ytick.labelsize'] = 12
from mpl_toolkits.axes_grid1 import make_axes_locatable

class fatigue():
    """Fatigue analysis functions"""
    """
    [1] The module: rainflow #ASTM E1049-85 rainflow cycle counting algorithm for fatigue analysis. The data ahead of the extrenum point is shifted to the end, intermediate values are discarded, and the extrenum value is appended.
    [2] Four-point rainflow counting https://doi.org/10.1016/0142-1123(94)90343-3. Standardization of the rainflow counting method for fatigue analysis C. Amzallag et al.
    [3] Read more at Metal Fatigue Analysis Handbook Practical problem-solving techniques for computer-aided engineering 2012, Pages 89-114 or https://doi.org/10.1016/B978-0-12-385204-5.00003-3
    [4] Compendium of fatigue analysis http://fatiguetoolbox.org/ 
    [5] Compendium of steel structures following Eurocode 3
    [6] Rainflow counting example: https://fatigue-life.com/rainflow-counting/
    [7] Rainflow counting for continuous data https://doi.org/10.1016/j.ijfatigue.2015.10.007

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

    def rainflow_c(series,residual=[],output="unique",plot=False):
        """Continuous rainflow counting implemented as four-point counting

        Four-point rainflow counting following [2,3,4,7]
        NB: Does not double count the residual! [7]

        Parameters
        ----------
        time_series :   list of float
            List of stress or load time series
        residual    :   list of float
            Previous residual for continuous evaluation
        output      :   str
            Choose between unique list or full list output
        plot        :   boolean
            Return plot data

        Outputs
        ----------
        Delta_stress    :   list of float
            List if stress ranges counted
        sigma_mean      :   list of float
            List of mean of the stress ranges
        n_count         :   list of float
            List of counts of each stress range (and associated stress mean)
        """               
        #Has a problem with short time series of 6 or less
        # if len(time_series) <= 6:
        #     raise  ValueError("Time series is too short")

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

    def rainflow(time_series,residual=[],output="unique"):
        """GENERAL rainflow counting implemented as four-point counting

        Four-point rainflow counting following [2,3,4,7]

        Parameters
        ----------
        time_series :   list of float
            List of stress or load time series
        residual    :   list of float
            Previous residual for continous evaluation
        output      :   str
            Choose between unique list or full list output

        Outputs
        ----------
        Delta_stress    :   list of float
            List if stress ranges counted
        sigma_mean      :   list of float
            List of mean of the stress ranges
        n_count         :   list of float
            List of counts of each stress range (and associated stress mean)
        """              
        #Has a problem with short time series of 6 or less

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

        if residual != []: #If residual is not empty
            time_series = residual+time_series #Add residual before time series

        if (max(time_series) == min(time_series)) or (len(time_series)<3): #Test to verify the time series is valid for rainflow counting
            raise Exception('Time series is either too short or flat')
        
        time_series = repeating_values(time_series) #Take care of repeated values before extremums are found
        time_series = extremes(time_series) #Reducing time_series to extreme points

        #Four-point rainflow counting
        result = {}
        stress_list = []
        mean_list = []
        n_list = []
        for m in range(2): #m is pass iteration, first pass = normal counting. Second pass is residual dublication and counting
            i = 0
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
                    
                else:
                    i +=1

            #if len(time_series) < 3: #Exrta stop criterium

            # Dublicate the residual before the last count
            if time_series[0] == time_series[-1]: 
                time_series = time_series[:-1] + time_series
                time_series = extremes(time_series)
            else:
                time_series = time_series + time_series
                time_series = extremes(time_series)
        
        stress_keys = list(result.keys())
        Delta_stress = [stress_keys[x][0] for x in range(len(stress_keys))] #Unpacking stress ranges from dictionary keys
        stress_mean = [stress_keys[x][1] for x in range(len(stress_keys))] #Unpacking stress ranges from dictionary keys
        n_count = list(result.values()) #unpacking counts from dictionary values

        if output == "unique":
            return Delta_stress, stress_mean, n_count
        else:
            return stress_list, mean_list, n_list

    def plot_rainflow(data,dt=1):
        
            fig, ax = plt.subplots()
            titles = ["Original","Removing repeating values","Removing intermediate values","Counting"]
            x_lim = len(data["0"])

            def line_intersection(line1, line2):
                xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
                ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

                def det(a, b):
                    return a[0] * b[1] - a[1] * b[0]

                div = det(xdiff, ydiff)
                if div == 0:
                    raise Exception('lines do not intersect')

                d = (det(*line1), det(*line2))
                x = det(d, xdiff) / div
                y = det(d, ydiff) / div
                return x, y

            for id,x in enumerate(data.keys()):
                #print(f"{x}:{[float(y) for y in data[x]]}")
                ax.clear()
                ax.plot(data[x], marker = "o", color="k", zorder=1)

                removed = []
                if id < len(data.keys())-1:
                    for id2 in range(len(data[str(id+1)])):
                        if data[str(id+1)][id2] != data[str(id)][id2]:
                            removed = [float(data[str(id)][id2]), float(data[str(id)][id2+1])]
                            removed_id = [id2,id2+1]
                            break
                    if removed != []:
                        if removed[0] > removed[1]:
                            xx = removed_id + [removed_id[1]+1]
                            y1 = removed + [removed[0]]
                            y2 = [max(removed)]*3

                            A = (xx[0],max(removed))
                            B = (xx[2],max(removed))
                            line1 = (A,B)

                            A = (xx[1],y1[1])
                            B = (xx[2],float(data[str(id)][removed_id[1]+1]))
                            line2 = (A,B)
                            x_c,y_c = line_intersection(line1,line2)

                            xx[2] = x_c
                            ax.plot(xx,y1,color="r",marker="o", zorder=2)
                            ax.plot(xx,y2,color="r", zorder=2)
                            ax.fill_between(xx,y1,y2,color="r", alpha=0.3)
                        else:
                            xx = [removed_id[0]-1] + removed_id
                            y1 = [removed[1]] + removed
                            y2 = [max(removed)]*3

                            A = (xx[0],max(removed))
                            B = (xx[2],max(removed))
                            line1 = (A,B)

                            A = (xx[1],y1[1])
                            B = (xx[0],float(data[str(id)][removed_id[0]-1]))
                            line2 = (A,B)
                            x_c,y_c = line_intersection(line1,line2)

                            xx[0] = x_c

                            ax.plot(xx,y1,color="r",marker="o", zorder=2)
                            ax.plot(xx,y2,color="r", zorder=2)
                            ax.fill_between(xx,y1,y2,color="r", alpha=0.3)
                else:
                    print(f"Residual: {[float(y) for y in data[x]]}")



                if id < 3:
                    ax.set_title(titles[id])
                    x_lim = len(data["0"])
                else:
                    ax.set_title(titles[3])
                    x_lim = len(data["3"])
                ax.grid()
                ax.set_xlim(0,x_lim)
                plt.pause(dt)

            plt.close(fig)

    def synthetic_SN(material,R_m,SF=1): 
        """Synthetic SN curve generator.
        Generates SN curves from material data and safety factors.
        Following [4]

        Parameters
        ----------
        material    :   Material to build SN curve for [4]
        R_M         :   Ultimate tenstile strength
        SF          :   Safety factor from k_reliab * k_mean * k_size * k_env * k_surf * n (n = notch support factor, comes from K_f and K_t)

        Outputs
        ------
        SN_curve    :   Dictionary consisting of SN curve parameters

        
        Definitions
        ----------
        cast_iron (GS)
        ductile_cast_iron (GJS)
        laminar_cast_iron (GJL)
        Mallable_cast_iron (GTS)

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
        
        SN_curve = { #Dictionary of SN-curves
            'DC': None,
            'N_D':[N_D],
            'C_mat':[C1_mat,C2_mat],
            'C':[C1,C2],
            'Delta_s_R_D_mat':[Delta_sigma_R_D_mat],
            'Delta_s_R_D':[Delta_sigma_R_D],
            'm':[m1,m2]}


        return SN_curve

    def eurocode_SN(DC,stress_type,SF=1,material="steel",**kwargs): #2007 version
        """Eurocode SN curves
        Generates SN curves from a given detail catagory, stress type and safety factor

        Parameters
        ----------
        DC          :   int
            Detail catagory
        stress_type :   str
            Either sigma (normal), tau (shear) or alternative sigma*.
        SF          :   int
            Safety factor from Eurocode
        material    :   str
            Steel or aluminium (al). For aluminium maximum principle stress should be used.
        **kwargs    :   signal_type, str
            CA (Constant amplitude) or VA (Variable amplitude) signal
        **kwargs    :   m1, int
            different slope override
        **kwargs    :   m2, int
            different slope override

        Outputs
        ----------
        SN_curve    :   dict
            Dictionary consisting of SN curve parameters

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
                SN_curve = { #Dictionary of SN-curve
                        'DC':DC,
                        'SF':SF,
                        'N_DC':N_DC,
                        'N_D':[N_D_CA,N_D_VA],
                        'C':[C1,C2],
                        'Delta_s_R_D':[Delta_sigma_R_D,Delta_sigma_R_L],
                        'm':[m1,m2,0]}
            else:
                SN_curve = { #Dictionary of SN-curve
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
                    SN_curve = { #Dictionary of SN-curve
                            'DC':DC,
                            'SF':SF,
                            'N_DC':N_DC,
                            'N_D':[N_D_CA,N_D_VA],
                            'C':[C1,C2],
                            'Delta_s_R_D':[Delta_sigma_R_D,Delta_sigma_R_L],
                            'm':[m1,m2,0]}
                else:
                    SN_curve = { #Dictionary of SN-curve
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
                
                SN_curve = { #Dictionary of SN-curve
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
                    SN_curve = { #Dictionary of SN-curve
                            'DC':DC,
                            'SF':SF,
                            'N_DC':N_DC,
                            'N_D':[N_D_CA,N_D_VA],
                            'C':[C1,C2],
                            'Delta_s_R_D':[Delta_sigma_R_D,Delta_sigma_R_L],
                            'm':[m1,m2,0]}
                else:
                    SN_curve = { #Dictionary of SN-curve
                            'DC':DC,
                            'SF':SF,
                            'N_DC':N_DC,
                            'N_D':[N_D_CA],
                            'C':[C1],
                            'Delta_s_R_D':[Delta_sigma_R_D],
                            'm':[m1,0]}
            else:
                raise ValueError('This is not a valid stress type. Try: "sigma", "tau" or "sigma*"')

        
        return SN_curve

    def IIW_SN(FAT,stress_type,SF=1,material="steel",**kwargs): #2024 version
        """International insitute of welding (IIW) fatigue SN curves
        Generates SN curves from a given FAT catagory, stress type and safety factor

        Parameters
        ----------
        FAT         :   Fatigue catagory
        stress_type :   Either sigma (normal) or tau (shear)
        SF          :   Safety factor from Eurocode
        Material    :   Steel or aluminium (al)
        **kwargs    :   signal_type :   CA (Constant amplitude) or VA (Variable amplitude) signal
                    :   m1          :   different slope override
                    :   m2          :   different slope override

        Outputs
        ----------
        SN_curve    :   Dictionary consisting of SN curve parameters

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

                SN_curve = { #Dictionary of SN-curve
                        'DC':FAT,
                        'SF':SF,
                        'N_DC':N_FAT,
                        'N_D':[N_D0,N_D],
                        'C':[Cmax,C1,C2],
                        'Delta_s_R_D':[Delta_sigma_R_U,Delta_sigma_R_D],
                        'm':[m0,m1,m2]}
            else:
                SN_curve = { #Dictionary of SN-curve
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
            
            SN_curve = { #Dictionary of SN-curve
                    'DC':FAT,
                    'SF':SF,
                    'N_DC':N_FAT,
                    'N_D':[N_D],
                    'C': [C1,C2],
                    'Delta_s_R_D':[Delta_tau_R_D],
                    'm':[m1,m2]}
        else:
            raise ValueError('This is not a valid stress type. Try: "sigma" or "tau"')

        return SN_curve

    def DNV_SN(joint_type,enviroment,**kwargs): #2016 version
        """DNV

        Parameters
        ----------
        joint_type  :   Type of joint, string
        enviroment  :   String of the enviroment type: air, seawater with cathodic protection and seawater with free corrosion
        **kwargs    :   Detail      :   SN curve detail, string
                    :   surf        :   Surface roughness, float/integer
                    :   stress_type :   for bolts either in shear or tension
                    :   DFF         :   Design fatigue factor
                    :   SF          :   Safety factor

        Outputs
        ------
        SN_curve    :   Dictionary consisting of SN curve parameters

        
        Definitions
        ----------


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

        SN_curve = { #Dictionary of SN-curve
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

        return SN_curve

    def cycles_SN(SN_curve,stress_list,n_count=[],mean_list=[]):
        """Finds the fatigue life associated with a given stress range from the given SN curve

        Parameters
        ----------
        SN_curve    :   dict
            SN curve parameters in a dictionary
        stress_list :   List of floats
            List of stress ranges that is to be iterated over
        n_count     :   List of floats
            List of counts
        mean_list   :   List of floats
            List of means

        Outputs
        ----------
        cycles      :   List of floats
            List of fatigue life cycles (N)
        n_cycles    :   List of floats
            List of of counts associated with the significant stress ranges
        res_stress  :   List of floats
            List of significant stress ranges 
        res_mean    :   List of floats
            List of mean stress associated to significant stress
        """ 
        
        if stress_list == [0]: #error handling if rainflow results in 0 counts
            return [0], [0], [0], [0]

        cycles = []
        n_cycles = [] #Cycle count list for significant stresses
        res_stress = [] #Stress list for significant stresses
        res_mean = [] #Mean stress list
        if n_count == []:
            n_count = [0]*len(stress_list)
        
        m = SN_curve['m']
        knee_stress = SN_curve['Delta_s_R_D'].copy()
        if m[-1] != 0: #If there are no cut-offs
            knee_stress.append(0) #This allows for cycle counting for all stress ranges.
        C = SN_curve['C']
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
        
        

        if np.sum(n_count) == 0: # If the stress list only consist of one stress range
            return cycles
        else:
            if res_mean == []:
                return cycles, n_cycles, res_stress
            else:
                return cycles, n_cycles, res_stress, res_mean

    def damage(N1,n1,N2=[],n2=[],**kwargs): #Palmgren-Miner damage
        """Calculate the Palmgren-Miner damage
        for both uni- and multiaxial stress ranges (sigma and tau). Multiaxial damage following Eurocode 3.
        IIW uses Gough-Pollard elipse to asses multiaxial stress state in welds. (Not implemented)

        Parameters
        ----------
        N1      :   List of flaot
            cycles
        n1      :   List of int
            counts
        N2      :   List of flaot
            cycles for second direction (Optional)
        n2      :   List of int
            counts (Optional)
        **kwargs:   list_D
            Gives a listed result enstead of totalted result (Optional)

        Outputs
        ----------
        D   :   Damage
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

    def eq_stress(sigma,n_count,SN_curve,n_eq):
        """Calculate damage equivalent stress at some equivalent cycle number.
        Here, run-out stress ranges are considered non-damaging.
        Inaccurate at very high cycle fatigue

        Parameters
        ----------
        sigma       :   Counted stress 
        n_count     :   Counts of stress
        SN_curve    :   SN curve dictionary)
        n_eq        :   Equivalent cycle

        Outputs
        ----------
        sigma_eq   :   Damage equivalent stress

        """  
        sum_res = 0
        sum_res2 = 0

        
        m = SN_curve['m']

        if len(m) >= 3: #If IIW curve with limit maximum curve, then assume bi-linear of the typical slopes
            if m[-1] != 0:
                m = m[1:]
                Delta_s_R_D = SN_curve['Delta_s_R_D'][1] #Knee-point stress range
            else:
                Delta_s_R_D = SN_curve['Delta_s_R_D'][0] #Knee-point stress range       
        else:
            Delta_s_R_D = SN_curve['Delta_s_R_D'][0] #Knee-point stress range        
        if len(m) > 1: #If bi-linear, two slopes
            for id, x in enumerate(sigma):
                if x >= Delta_s_R_D:
                    sum_res += x**m[0] * n_count[id]
                else:
                    sum_res2 += x**m[1] * n_count[id]
            sigma_eq = ((sum_res + sum_res2*Delta_s_R_D**(m[0]-m[1]))/n_eq)**(1/m[0])
            
        else: #If linear with one slope
            for id, x in enumerate(sigma):
                sum_res += x**m[0] * n_count[id]
            sigma_eq = (sum_res/n_eq)**(1/m[0])

        return sigma_eq
    
    def eq_stress_D(sigma,n_count,SN_curve,D,n_eq=[]):
        """Calculate damage equivalent stress at some equivalent cycle number.
        Here, run-out stress ranges are considered non-damaging.
        It does not work for shear stresses. IIW eq.4.18+19 and 4.21+22
        Inaccurate at very high cycle fatigue

        Parameters
        ----------
        sigma       :   Counted stress 
        n_count     :   Counts of stress
        SN_curve    :   SN curve dictionary)
        n_eq        :   Equivalent cycle

        Outputs
        ----------
        sigma_eq   :   Damage equivalent stress

        """  
        sum_res = 0
        sum_res2 = 0
        m = SN_curve['m']

        if len(m) >= 3: #If IIW curve with limit maximum curve, then assume bi-linear of the typical slopes
            if m[-1] != 0:
                m = m[1:]
                Delta_s_R_D = SN_curve["Delta_s_R_D"][-1]
            else:
                Delta_s_R_D = SN_curve['Delta_s_R_D'][0] #Knee-point stress range       
        else:
            Delta_s_R_D = SN_curve["Delta_s_R_D"][0]
        if len(m) > 1: #If bi-linear, two slopes
            for id, x in enumerate(sigma):
                if x >= Delta_s_R_D:
                    sum_res += x**m[0] * n_count[id]
                else:
                    sum_res2 += x**m[1] * n_count[id]
            if n_eq != []:
                sigma_eq = (1/D * (sum_res + sum_res2*Delta_s_R_D**(m[0]-m[1]))/n_eq)**(1/m[0])
            else:
                sigma_eq = (1/D * (sum_res + sum_res2*Delta_s_R_D**(m[0]-m[1]))/sum(n_count))**(1/m[0])
            if sigma_eq < Delta_s_R_D:
                for id, x in enumerate(sigma):
                    if x >= Delta_s_R_D:
                        sum_res += x**m[0] * n_count[id]
                    else:
                        sum_res2 += x**m[1] * n_count[id]
                    if n_eq != []:
                        sigma_eq = (1/D * (sum_res2 + sum_res*Delta_s_R_D**(m[1]-m[0]))/n_eq)**(1/m[1])
                    else:
                        sigma_eq = (1/D * (sum_res2 + sum_res*Delta_s_R_D**(m[1]-m[0]))/sum(n_count))**(1/m[1])
        else:
            raise ValueError("SN-curve is not bi-linear")    
        # else: #If linear with one slope
        #     for id, x in enumerate(sigma):
        #         sum_res += x**m[0] * n_count[id]
        #     sigma_eq = (sum_res/n_eq)**(1/m[0])

        return sigma_eq
    
    def eq_load(load,n_count,SN_curve,n_eq):
        """Calculate Damage Equivalent Load (DEL) at some equivalent cycle number.
        Only works for linear or bi-linear curves (one or two slopes)

        Parameters
        ----------
        load        :   Counted load gathered from stress counts via transfer function
        n_count     :   Counts of stress
        SN_curve    :   SN curve dictionary)
        n_eq        :   Equivalent cycle

        Outputs
        ----------
        load_eq   :   Damage equivalent load

        """  
        sum_res = 0

        m = SN_curve['m']
        if len(m) >= 3: #If IIW curve with limit maximum curve, then assume bi-linear of the typical slopes
            if m[-1] != 0:
                m = m[1:]
        if len(m) > 1:
            m1 = m[0]
            m2 = m[1]
            m_ = (m2+m1)/2 #Typical approach [4]
            for id, x in enumerate(load):
                sum_res += x**m_ * n_count[id]
            load_eq = (sum_res/n_eq)**(1/m_)
            
        else:
            m1 = m[0]
            for id, x in enumerate(load):
                sum_res += x**m1 * n_count[id]
            load_eq = (sum_res/n_eq)**(1/m1)

        return load_eq
        
    def UR(sigma_eq,SN_curve,n_eq): #Utilization ratio
        """Calculate utilization ratio.
        n_eq must be the same. Here run-out stress ranges are counted.

        Parameters
        ----------
        sigma_eq    :   Damage equivalent stress
        SN_curve    :   SN curve
        n_eq        :   Equivalent cycle

        Outputs
        ----------
        UR  :   Utilization ratio

        """
        m = SN_curve['m']
        C = SN_curve['C']
        N_D = SN_curve['N_D'][0]
        if len(m) >= 3: #If IIW curve with limit maximum curve, then assume bi-linear of the typical slopes
            if m[-1] != 0:
                m = m[1:]
        if len(m) > 1: #Bi-linear
            if n_eq < N_D:
                sigma_R_eq = (C[0]/n_eq)**(1/m[0])
            else:
                sigma_R_eq = (C[1]/n_eq)**(1/m[1])
        else: #Single slope
            sigma_R_eq = (C[0]/n_eq)**(1/m[0])

        UR = sigma_eq/sigma_R_eq

        return UR

    def plot_SN_curve(SN_curve,file_name="None",**kwargs):
        """Plot SN curve

        Parameters
        ----------
        SN_curve    :   dict
            Dictionary consisting of SN curve parameters
        file_name   :   str, optional
            String of file name
        **kwargs    :   hist_type, str
            "bar" (default), "line" or "stair"
        **kwargs    :   result, dict
            Dictionary of results from continous data stream
        **kwargs    :   stress_list, list of float
            stress list for histogram
        **kwargs    :   n_count, list of float
            count of stress for histogram
        **kwargs    :   title, str
            Title to plot
        **kwargs    :   bin_width, int
            Width of the bins default=10
        **kwargs    :   hist_data, dict
            Previous histogram data, should be applied together with stress_list and n_count, supply hist_data = {} if is not known
        **kwargs    :   bins, int
            Number of bins to use, not recomended for continuous updating histogram
        **kwargs    :   figure, object
            figure to redraw

        Outputs
        ----------
        fig     :   fig
            figure
        ax      :   ax
            axis
        file    :   png
            Saved figure (optional)
        """
        
        

        hist_type = kwargs.get("hist_type","bar")

        title_string = kwargs.get("title","SN-curve")

        try:
            result = kwargs["result"]
            result_data = True
        except:
            result_data = False

        if result_data == False:
            try: #If stress_list is given, i.e. histogram should be plotted with the SN-curve.
                #Then copy the stress_list and count all stresses as individual ranges, i.e. n_count is a list of only ones.
                stress_list = kwargs["stress_list"]
                stress_list_ = stress_list.copy()
                history = True
            except:
                history = False
        else:
            history = True
            stress_list_1 = result["stress_res"]
            stress_list_2 = result["stress_res_residual"]
            stress_list_ = stress_list_1+stress_list_2

        if history == True:
            if result_data == False:
                try:
                    n_count = kwargs["n_count"]
                    n_count_ = n_count.copy()
                except:
                    raise ValueError('No cycle count are given')

                if sum(n_count_) != len(n_count_): #Only duplicate counts if n_counts is not already a list only consisting of ones
                    for id, x in enumerate(n_count): #set all stress to 1 count, and add identical stresses to compensate
                        i = 1
                        while i < x:
                            n_count_[id] = 1
                            n_count_.append(1)
                            stress_list_.append(stress_list[id])
                            i += 1
            hist_tot, bin_edges = fatigue.bin_func(stress_list_,**kwargs) #For plotting with residual part together with previous hist

            if result_data == True:
                hist_next, bin_edges_next = fatigue.bin_func(stress_list_1,**kwargs) #For next plot, without residual data


        xlim2 = 10**9
        m = SN_curve['m'].copy()
        m = [m[0]] + m #Dubplicate first value
        N_D = SN_curve['N_D']
        C = SN_curve['C'].copy()
        C = [C[0]] + C #Dubplicate first value
        yy = []
        if N_D[0] == 0:
            xx = [1] + [xlim2]
        else:
            xx = [1] + N_D + [xlim2]
        for id,x in enumerate(xx):
            if m[id] == 0: #Run-off
                yy = yy + [yy[-1]] #Duplicate last point
            else:
                yy.append((C[id]/x)**(1/m[id])) #Calculate stress value

        x_lim = max(C[0]/(1000)**m[0],1) #Limit x-axis to either N at stress=1000 or N=1

        #Clear previous figure
        try:
            fig = kwargs["figure"]
            ax = fig.get_axes()[0]
            plt.figure(fig)
            ax.clear()
        except:
            fig, ax = plt.subplots(1,1,figsize=(6, 4), tight_layout=True)

        #Plotting SN-curve    
        ax.loglog(xx, yy,color=(0.1,0.1,0.1),linewidth=3,label="SN-curve")
        ax.grid(color=(0.4,0.4,0.4), linestyle='-', linewidth=0.5, which="major")
        ax.grid(color=(0.8,0.8,0.8), linestyle='-', linewidth=0.5, which="minor")

        #Plotting histgram
        if history == True:
            bin_edges = bin_edges.tolist()
            hist = hist_tot.tolist()
            if hist_type == "stair":
                hist.reverse()
                bin_edges.reverse()
                hist = [0] + hist #Start hist from 0
                hist = np.add.accumulate(hist) #Make an acummulated list of hist
                hist = hist.tolist()
                ax.stairs(bin_edges[0:-1],hist,fill=True,color=(0.05,0.03,0.53),label="Stress spectrum") #Stress spectrum or cumulative frequency distribution
            elif hist_type == "line":
                bin_edges = bin_edges[1:]
                hist = [1] + hist + [1]
                bin_edges = [1] + bin_edges + [bin_edges[-1]]    
                ax.loglog(hist,bin_edges,marker=".",color=(0.05,0.03,0.53),linewidth=2,label="Stress histogram") #Stress histogram as line
            else:
                #print(bin_edges)
                bin_edges_new = [val for val in bin_edges for _ in (0, 1)]
                hist_new = [val for val in hist for _ in (0, 1)]
                hist_new = [0.01] + hist_new + [0.01]
                ax.loglog(hist_new,bin_edges_new,color=(0.05,0.03,0.53),linewidth=2,label="Stress histogram") #Stress histogram
                y = [0.1]*len(hist_new)
                ax.fill_between(hist_new,y,bin_edges_new,color=(0.05,0.03,0.53))
                    
            ax.set(ylim = (1,max(max(bin_edges)*2,1000)), xlim=(1,xlim2))
            ax.set(ylim = (1,10000), xlim=(1,10**9))

            if result_data == True:
                D_t = result["D_t"]
                ax.text(3*10**7, 1.8, "$D_{\mathrm{tot}}$ = "+ f"{float(D_t):.3e}", size=13, rotation=0.,
                ha="center", va="center",
                bbox=dict(boxstyle="Square",
                        ec=(1., 0.5, 0.5),
                        fc=(1., 0.8, 0.8),
                        )
                )

        else:
            ax.set(ylim = (1,1000), xlim=(x_lim,xlim2))
        # ax.set(xlabel = "Fatigue life, N [cycles]", ylabel = r'Stress range, $\Delta\hat{\sigma}_R$ [MPa]')
        ax.set(xlabel = "Fatigue life [cycles]", ylabel = r'Stress range [MPa]')
        #ax.set_title(title_string)
        ax.legend()
        plt.subplots_adjust(bottom=0.15)
        if file_name != "None": #Save or show plot
            fig.savefig(file_name)

        #Savning data
        if history == True:
            if result_data == True:
                hist_data = {
                    "hist":hist_next,
                    "bin_edges":[bin_edges_next]
                }
                return fig, ax, hist_data
            else:
                hist_data = {
                    "hist":hist_tot,
                    "bin_edges":[bin_edges]
                }
                return fig, ax, hist_data
        else:
            return fig, ax
    
    def SN_curve_plotdata(SN_curve,result,hist_prev,**kwargs):
        """Plot SN curve

        Parameters
        ----------
        SN_curve    :   dict
            Dictionary consisting of SN curve parameters
        result      :   dict
            Dictionary of results from continous data stream
        hist_prev   :   list of float
            Previous histogram count, should be applied together with stress_list and n_count
        **kwargs    :   hist_type, str
            "histogram" (default) or "spectrum"
        **kwargs    :   bin_width, int
            Width of the bins default=10
        
        **kwargs    :   bins, int
            Number of bins to use, not recomended for continuous updating histogram

        Outputs
        ----------
        hist_data   :   list of float
            Data for next iteration
        """

        #SN-curve
        xlim2 = 10**9
        m = SN_curve['m'].copy()
        m = [m[0]] + m #Dubplicate first value
        N_D = SN_curve['N_D']
        C = SN_curve['C'].copy()
        C = [C[0]] + C #Dubplicate first value
        yy = []
        if N_D[0] == 0:
            xx = [1] + [xlim2]
        else:
            xx = [1] + N_D + [xlim2]
        for id,x in enumerate(xx):
            if m[id] == 0: #Run-off
                yy = yy + [yy[-1]] #Duplicate last point
            else:
                yy.append((C[id]/x)**(1/m[id])) #Calculate stress value
        x_curve = xx
        y_curve = yy

        #Histgram
        hist_type = kwargs.get("hist_type","bar")
        
        stress_list_1 = result["stress_res"]
        stress_list_2 = result["stress_res_residual"]
        stress_list_ = stress_list_1+stress_list_2
        
        hist_tot, bin_edges = fatigue.bin_func(stress_list_,hist_prev,**kwargs) #For plotting with residual part together with previous hist
        hist_next, bin_edges_next = fatigue.bin_func(stress_list_1,hist_prev,**kwargs) #For next plot, without residual data
        
        bin_edges = bin_edges.tolist()
        hist = hist_tot.tolist()
        if hist_type == "spectrum":
            hist.reverse()
            bin_edges.reverse()
            y_points = bin_edges
            hist = [0] + hist #Start hist from 0
            hist = np.add.accumulate(hist).tolist() #Make an acummulated list of hist

            y_points = [val for val in bin_edges for _ in (0, 1)]
            x_points = [val for val in hist for _ in (0, 1)]
            y_points.pop(-1)
            x_points.pop(0)
        else: #histogram
            y_points = [val for val in bin_edges for _ in (0, 1)]
            hist_new = [val for val in hist for _ in (0, 1)]
            x_points = [1] + hist_new + [1]
        hist_data = {
            "hist":hist_next,
            "bin_edges":[bin_edges_next]
        }

        return x_curve, y_curve, x_points, y_points, hist_data

    def plot_time_series(time_series,file_name="None",**kwargs):
        """Plot time series

        Parameters
        ----------
        time_series :   List of time series
        file_name   :   String of file name
        **kwargs    :   title_string    : title string

        Outputs
        ----------
        Saved figure
        """ 
        title_string = kwargs.get('title_string',"3D histogram")
        xpoints = list(range(0,len(time_series)))
        fig = plt.plot(xpoints, time_series,color="r",linewidth=1)
        plt.grid(color=(0.8,0.8,0.8), linestyle='-', linewidth=1, which="major")
        plt.title(title_string)
        plt.xlabel("Sample number")
        plt.ylabel('Load/Stress')
        if file_name !="None": #Save or show plot
            plt.savefig(file_name,dpi=200)

        return fig
    
    def plot_histogram(nbins=10,file_name="None",**kwargs):
        """Bin the given stress list
        Optionally save a histogram

        Parameters
        ----------
        nbins       :   int
            number of bins to use
        file_name   :   str
            file name
        **kwargs    :   result, dict
            Dictionary of results from continous data stream
        **kwargs    :   stress_list, List of floats
            List of stress ranges
        **kwargs    :   n_counts, list of int
            Counts of stress ranges
        **kwargs    :   s_mean, list of float
            List of stress means for 3D plot
        **kwargs    :   binwidth, int
            Use ad fixed width for bins
        **kwargs    :   title_string, str
            String for title name
        **kwargs    :   hist_data, dict
            Previous histogram data, should be applied together with stress_list and n_count
        **kwargs    :   figure, object
            figure to redraw
        **kwargs    :   colormap, str
            Name of a valid colormap, default=plasma


        Outputs
        ----------
        fig     :   object
            figure object
        ax      :   object
            axes object
        saved_plot  :   png
            Plot of histogram
        """

        #Get results if this is supplied (continuous data)
        try:
            result = kwargs["result"]
            result_data = True
        except:
            result_data = False
        
        #If not get data directly
        if result_data == False:
            try: #If stress_list is given, i.e. histogram should be plotted with the SN-curve.
                #Then copy the stress_list and count all stresses as individual ranges, i.e. n_count is a list of only ones.
                stress_list = kwargs["stress_list"]
                stress_list_ = stress_list.copy()
                stress_list_1 = stress_list_
            except:
                raise ValueError('No stress list is given')
            try:
                n_counts = kwargs["n_counts"]
                n_count_ = n_counts.copy()
            except:
                raise ValueError('No cycle counts are given')
            try:
                s_mean = kwargs["s_mean"]
                s_mean_ = s_mean.copy()
            except:
                raise ValueError('No mean stress list is given')
        else:
            stress_list_1 = result["stress"]
            n_count_1 = result["n_rain"]
            stress_list_2 = result["stress_residual"]
            n_count_2 = result["n_rain_residual"]
            stress_list_ = stress_list_1+stress_list_2

            s_mean_1 = result["mean_rain"]
            s_mean_2 = result["mean_rain_residual"]
            s_mean_ = s_mean_1 + s_mean_2

        #Clear old figure
        try:
            fig = kwargs["figure"]
            ax = fig.get_axes()[0]
            cax = fig.get_axes()[1]
            ax_histx = fig.get_axes()[2]
            ax_histy = fig.get_axes()[3]
            plt.figure(fig)
            ax.clear()
            cax.remove()
            ax_histx.remove()
            ax_histy.remove()
        except:
            fig, ax = plt.subplots()#(figsize=(5.5, 4.5))
        
        #Get 
        if result_data == False:
            n_count_ = n_counts.copy()
            if sum(n_count_) != len(n_count_): #Only dublicate counts if n_counts is not already a list only consisting of ones
                for id, x in enumerate(n_counts): #set all stress to 1 count, and add identical stresses to compensate
                    i = 1
                    while i < x:
                        n_count_[id] = 1
                        n_count_.append(1)
                        stress_list_.append(stress_list[id])
                        s_mean_.append(s_mean[id])
                        i += 1
        
        static_mean = kwargs.get("static_mean",0)
        #For this plot
        xx = stress_list_
        yy = [x + static_mean for x in s_mean_]
        #For next plot
        xx1 = stress_list_1
        yy1 = [x + static_mean for x in s_mean_1]

        #Histogram data and bins
        hist, x_edges, y_edges = fatigue.bin_func(xx,yy=yy,**kwargs) #For plotting with residual part together with previous hist
        hist_next, x_edges_next, y_edges_next = fatigue.bin_func(xx1,yy=yy1,**kwargs) #For next iteration
        
        #Save for next plot
        hist_data = {
            "hist":hist_next,
            "bin_edges":[x_edges_next,y_edges_next]
        }
        

        #Plotting heatmap
        map_user = kwargs.get("colormap","plasma") #plasma
        extent = [x_edges[0],x_edges[-1],y_edges[0],y_edges[-1]]
        im = ax.imshow(hist,extent=extent,cmap=map_user, aspect='auto')
        
        ax.set_xticks(x_edges[::2])
        ax.set_yticks(y_edges[::2])
        ax.tick_params(top=True, labeltop=True, bottom=False, labelbottom=False, labelsize=10)
        ax.tick_params(right=True, labelright=True, left=False, labelleft=False, labelsize=10)
        ax.set_xticklabels(ax.get_xticklabels(), rotation='vertical', ha='center')
        ax.set_yticklabels(ax.get_yticklabels())
        title_string = kwargs.get('title_string',"Heatmap")
        ax.set_title(title_string,x=0.5,y=-0.20)
        ax.grid()


        # create new Axes on the right and on the top of the current Axes
        divider = make_axes_locatable(ax)

        #Colorbar
        cax = divider.append_axes('left', size='5%', pad=0.05)
        fig.colorbar(im, cax=cax, orientation='vertical',location="left",label="Frequency")

        #Histogram plots
        char_x = len(str(max(x_edges)))
        char_y = max(len(str(min(y_edges))),len(str(max(y_edges))))
        ax_histx = divider.append_axes("top", 1.2, pad=0.08*char_x, sharex=ax)
        ax_histy = divider.append_axes("right", 1.2, pad=0.08*char_y, sharey=ax)
        # make some labels invisible
        ax_histx.xaxis.set_tick_params(labelbottom=False)
        ax_histy.yaxis.set_tick_params(labelleft=False)
        #Summing up
        x_hist = np.sum(hist,axis=0)
        y_hist = np.sum(hist,axis=1)
        #Histograms/stairs
        ax_histx.stairs(x_hist, x_edges,fill=True,color=(0.05,0.03,0.53))
        ax_histy.stairs(np.flip(y_hist), y_edges,fill=True, orientation='horizontal',color=(0.05,0.03,0.53))
        ax_histx.grid()
        ax_histy.grid()
        ax_histx.set_title("Stress range histogram")
        ax_histy.set_title("Mean stress histogram",x=1.2,y=0,rotation=270)
        ax_histy.set_xlabel("Frequency",rotation="horizontal")
        ax_histx.set_ylabel("Frequency",rotation="vertical")

        plt.subplots_adjust(bottom=0.15)
        
        if file_name !="None": #Save or show plot
            plt.savefig(file_name,dpi=200)

        return fig, ax, hist_data

    def heatmap_data(hist2D_prev,result,**kwargs):
        """Bin the given stress list
        Optionally save a histogram

        Parameters
        ----------
        hist2D_prev    :    2D list of flaot
            Previous histogram count, should be applied together with stress_list and n_count
        result  : dict
            Dictionary of results from continous data stream
        **kwargs    :   bin_width, int
            Width of the bins default=10
        **kwargs    :   xbin_width, int
            Override width of the x bins default (only if yy is present)
        **kwargs    :   ybin_width, int
            Override width of the y bins default (only if yy is present)
        **kwargs    :   xbins, int
            Override number of x bins to use, not recomended for continuous updating histogram (only if yy is present)
        **kwargs    :   ybins, int
            Override number of y bins to use, not recomended for continuous updating histogram (only if yy is present)
        **kwargs    :   bins, int
            Override number of x bins to use, not recomended for continuous updating histogram   
        


        Outputs
        ----------
        hist2D  :   2D list of float
            Heatmap z/height data
        x_edges :   list of float
            list of edges
        y_edges :   list of float
            list of edges
        hist2D_next :   2D list of float
            Heatmap z/height data for next iteration
        """
        stress_list_1 = result["stress"]
        stress_list_2 = result["stress_residual"]
        stress_list_ = stress_list_1+stress_list_2

        s_mean_1 = result["mean_rain"]
        s_mean_2 = result["mean_rain_residual"]
        s_mean_ = s_mean_1 + s_mean_2       

        #For this plot
        xx = stress_list_
        yy = s_mean_
        #For next plot
        xx1 = stress_list_1
        yy1 = s_mean_1

        #Histogram data and bins
        hist2D, x_edges, y_edges = fatigue.bin_func(xx,hist2D_prev,yy,**kwargs) #For plotting with residual part together with previous hist
        hist_next, x_edges_next, y_edges_next = fatigue.bin_func(xx1,hist2D_prev,yy1,**kwargs) #For next iteration
        
        x_hist_next = np.sum(hist2D,axis=0)
        y_hist_next = np.sum(hist2D,axis=1)

        #Save for next plot
        hist2D_next = {
            "hist":hist_next,
            "bin_edges":[x_edges_next,y_edges_next],
            "hist1D":[x_hist_next,y_hist_next]
        }

        return hist2D, x_edges, y_edges, hist2D_next

    def plot_damage(result,**kwargs):
        """Plot PM damage in a running graph

        Parameters
        ----------
        result    :   dict
            Dictionary of results from continous data stream
        **kwargs    :   title, str
            Title to plot
        **kwargs    :   figure, object
            figure to redraw
        **kwargs    :   y_max_lim, int
            How many samples for the running graph

        Outputs
        ----------
        fig     :   fig
            figure
        ax      :   ax
            axis
        """
        
        #Get plot data from previous figure
        try:
            fig = kwargs["figure"]
            first = False
            ax = fig.get_axes()[0]
            line1 = ax.get_lines()[0]
            line2 = ax.get_lines()[1]
            #line3 = ax.get_lines()[2]
            #line4 = ax.get_lines()[3]
            xdata = line1.get_xdata().tolist()
            ydata = line1.get_ydata().tolist()
            y2data = line2.get_ydata().tolist()
            #y3data = line3.get_ydata().tolist()
            #y4data = line4.get_ydata().tolist()
            plt.figure(fig)
            ax.clear()
        except:
            first = True  
        
        #Calculate damage
        D = result["D"]
        D_res = result["D_residual"]
        if first == True:
            x = [0]
            y1 = [D+D_res]
            y2 = [D]
            #y3 = [D_res]
            #y4 = [D]
            fig, ax = plt.subplots()
            box = ax.get_position()
            ax.set_position([box.x0, box.y0, box.width, box.height*0.87])
        else:
            x = xdata + [xdata[-1]+1]
            y1 = ydata + [result["D_t"]] #[sum(y2) + D_res]
            y2 = y2data + [D]
            #y3 = y3data + [D_res]
            #y4 = y4data + [result["D_accum"]] #[sum(y2)]

        #Plotting
        y_length = kwargs.get("y_max_lim",60)
        if x[-1] > y_length:
            x = x[-(y_length+1):]
            y1 = y1[-(y_length+1):]
            y2 = y2[-(y_length+1):]
            
        ax.plot(x,y1,label="Total damage",color="k",linewidth=2)
        ax.plot(x,y2,label="Instant damage",color='r')
        # ax.plot(x,y3,label="Residual damage",color="m")
        # ax.plot(x,y4,label="Accumulated damage",color="g")
        ax.set(xlabel="Sample",ylabel="PM damage",xlim=(max(max(x)-y_length,0) , max(max(x),y_length)),yscale="log")
        #ax.set_yticks([10**(-7),10**(-6),10**(-5), 10**(-4), 10**(-3), 10**(-2), 10**(-1), 10**(0), 10**(1)])
        #ax.set_yticklabels(["$10^{-7}$","$10^{-6}$","$10^{-5}$","$10^{-4}$","$10^{-3}$","$10^{-2}$","$10^{-1}$","$10^{-0}$","$10^1$"])
        ylim_min = min(y2) #min(y2[-y_length:])
        ax.set_ylim(ylim_min,10**1)
        ax.grid(color=(0.4,0.4,0.4), linestyle='-', linewidth=0.5, which="major")
        ax.grid(color=(0.8,0.8,0.8), linestyle='-', linewidth=0.5, which="minor")
        ax.get_xaxis().get_major_formatter().labelOnlyBase = False
        ax.legend(loc="upper center",bbox_to_anchor=(0.37, 1.2),ncol=2)
        title_string = kwargs.get("title","Palmgreen-Miner damage")
        ax.set_title(title_string, x=0.5, y=1.2)
        damage_text = ("$D_{tot}$ =" + f"{float(y1[-1]):.3e} \n"
                       "$D_{i}$ =" + f"{float(y2[-1]):.3e} ")
        
        ax.text(0.14, 0.89, damage_text, size=13,
                ha="center", va="center", transform = ax.transAxes,
                bbox=dict(boxstyle="Square",
                        ec=(1., 0.5, 0.5),
                        fc=(1., 0.8, 0.8),
                        )
                )

        return fig, ax
    
    def plot_haigh(SN_curve,S_y,S_u,**kwargs):
        """Plot Haigh diagram with Goodman line.
        Also called a constant life diagram (CLD)

        Parameters
        ----------
        S_d     :   int
            Fatigue strength at zero mean stress, R = -1, N=10**6
        S_y     :    int
            Yield strength
        S_u     :   int
            Ultimate tensile strength
        **kwargs    :   title, str
            Title to plot
        **kwargs    :   figure, object
            figure to redraw
        **kwargs    :   result, dict
            Dictionary of results from continous data stream
        **kwargs    :   points, int
            Maximum points to display
        Outputs
        ----------
        fig     :   fig
            figure
        ax      :   ax
            axis
        """

        #Get plot data from previous figure 
        try:
            fig = kwargs["figure"]
            ax = fig.get_axes()[0]
            line = ax.collections[0]
            prev_data = line.get_offsets()
            plt.figure(fig)
            ax.clear()
        except:
            fig, ax = plt.subplots()
        
        N_D = SN_curve["N_D"]
        C = SN_curve["C"]
        m = SN_curve["m"]
        S_d = (C[-1]/N_D[-1])**(1/m[-1])

        x_yield = [-S_y,0,S_y]
        y_yield = [0,S_y,0]

        x_intersect_R = (S_d*1.4)/np.tan((2*np.pi)/360*45)
        x_R = [-x_intersect_R,0,x_intersect_R]
        y_R = [S_d*1.4,0,S_d*1.4]

        x_R1 = [0, 0]
        y_R1 = [0, S_y*1.25]


        ax.plot(x_yield,y_yield,linewidth=0.6,color=(0.5,0.5,0.5))
        ax.plot(x_R,y_R,linewidth=1,color="k",linestyle='dashed')
        ax.plot(x_R1,y_R1,linewidth=1,color="k",linestyle='dashed')
        title_string = kwargs.get("title","Haigh diagram")
        ax.set(xlabel = u"Mean stress, $σ_m$ [MPa]", ylabel = u'Allowable stress amplitude, $σ_R$ [MPa]', title=title_string)
    
        x_intersect = (S_y-S_d)/np.tan((2*np.pi)/360*45)
        ax.plot([-x_intersect,0,S_u],[S_d,S_d,0],color=(0.55,0.4,0.2),linewidth=2,label="Modified Goodman")
        #ax.plot([-145,0,S_u],[S_d,S_d,0],color=(0.5,0.4,0.2),linewidth=2,label="Gerber")
        ax.text(S_y/2**(1/2)+10, S_y/2**(1/2)+10, "R=0", size=11, ha="center", va="center")
        ax.text(-S_y/2**(1/2)-10, S_y/2**(1/2)+10, "R=-∞", size=11, ha="center", va="center")
        ax.text(0, S_y*1.25+10, "R=-1", size=11, ha="center", va="center")
        
        try:
            result = kwargs["result"]
            result_data = True
        except:
            result_data = False
        
        if result_data == True:
            stress = result["stress"] #Stress range
            stress_amplitude = [x/2 for x in stress]
            mean = result["mean_rain"]
            try:
                data = prev_data
            except:
                data = []
            
            for id in range(len(data)):
                mean.append(data[id][0])
                stress_amplitude.append(data[id][1])
            
            points = kwargs.get("points",200)
            if len(mean) > points:
                mean = mean[:points]
                stress_amplitude = stress_amplitude[:points]
            
            ax.scatter(mean,stress_amplitude,color="b",label="Stresses",alpha=0.1)
        ax.legend()

        ax.set_xlim(min((-S_y*1.2),min(mean)),max((S_u*1.2),max(mean)))
        ax.set_ylim(0,max((S_y*1.5),max(stress_amplitude)))
        ax.set_aspect('equal', 'box')

        return fig

    def bin_func(xx,hist_data,yy=[],**kwargs):
            """Plot SN curve

            Parameters
            ----------
            xx :   list of float
                Stress list
            hist_data    :   hist, dict
                Previous histogram data. First iteration hist = {}
            yy  :   list of float
                mean stress list, default = []
            **kwargs    :   bin_width, int
                Width of the bins default=10
            **kwargs    :   xbin_width, int
                Override width of the x bins default (only if yy is present)
            **kwargs    :   ybin_width, int
                Override width of the y bins default (only if yy is present)
            **kwargs    :   xbins, int
                Override number of x bins to use, not recomended for continuous updating histogram (only if yy is present)
            **kwargs    :   ybins, int
                Override number of y bins to use, not recomended for continuous updating histogram (only if yy is present)
            **kwargs    :   bins, int
                Override number of x bins to use, not recomended for continuous updating histogram

            Outputs
            ----------
            hist    :   List of float
            x_edges :   List of float
            (y_edges :   List of float)
            """
            def align_hist2D(xx,yy,hist_prev,xbins_prev,ybins_prev,**kwargs):
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
                xbin_width = kwargs.get("xbin_width",bin_width) #Get bin width if supplied
                ybin_width = kwargs.get("ybin_width",bin_width) #Get bin width if supplied
                
                
                nbins_x = np.ceil(max(xx)/xbin_width) #Calculate number of bins
                nbins_x = kwargs.get("xbins",nbins_x) #Get number of bins if supplied, and override nbins
                nbins_y = (np.ceil(max(yy)/ybin_width)-np.floor(min(yy)/ybin_width)) #Calculate number of bins
                nbins_y = kwargs.get("ybins",nbins_y) #Get number of bins if supplied, and override nbins

                rem = max(xx) % xbin_width #Remainder
                rem2 = min(yy) % ybin_width #Remainder
                rem3 = max(yy) % ybin_width #Remainder
                
                #Find new histrogram
                hist_new, xbins_new, ybins_new = np.histogram2d(xx,yy,bins=(round(nbins_x),round(nbins_y)),range=((0,round(max(xx)+bin_width-rem)),(round(min(yy)-rem2),round(max(yy)+bin_width-rem3)))) #Histogram
                hist_new = np.transpose(hist_new)
                
                #If the previous histogram does not exist
                if np.sum(hist_prev) == [0]:
                    hist_prev = np.zeros((hist_new.shape))
                    xbins_prev = xbins_new
                    ybins_prev = ybins_new
                

                xbinwidth = round(xbins_new[1]-xbins_new[0])
                ybinwidth = round(ybins_new[1]-ybins_new[0])

                #Aligning by adding zeros around the matricies
                if min(xbins_new) > min(xbins_prev):
                    diff = round((min(xbins_new)-min(xbins_prev))/xbinwidth)
                    #if diff != 0:
                    hist_new = np.hstack((np.zeros((hist_new.shape[0],diff)),hist_new))
                elif min(xbins_new) < min(xbins_prev):
                    diff = round((min(xbins_prev)-min(xbins_new))/xbinwidth)
                    #if diff != 0:
                    hist_prev = np.hstack((np.zeros((hist_prev.shape[0],diff)),hist_prev))
                
                if min(ybins_new) > min(ybins_prev):
                    diff = round((min(ybins_new)-min(ybins_prev))/ybinwidth)
                    #if diff != 0:
                    hist_new = np.vstack((hist_new,np.zeros((diff,hist_new.shape[1]))))
                elif min(ybins_new) < min(ybins_prev):
                    diff = round((min(ybins_prev)-min(ybins_new))/ybinwidth)
                    #if diff != 0:
                    hist_prev = np.vstack((hist_prev,np.zeros((diff,hist_prev.shape[1]))))
                
                if max(xbins_new) < max(xbins_prev):
                    diff = round((max(xbins_prev)-max(xbins_new))/xbinwidth)
                    #if diff != 0:
                    hist_new = np.hstack((hist_new,np.zeros((hist_new.shape[0],diff))))
                elif max(xbins_new) > max(xbins_prev):
                    diff = round((max(xbins_new)-max(xbins_prev))/xbinwidth)
                    #if diff != 0:
                    hist_prev = np.hstack((hist_prev,np.zeros((hist_prev.shape[0],diff))))

                if max(ybins_new) < max(ybins_prev):
                    diff = round((max(ybins_prev)-max(ybins_new))/ybinwidth)
                    #if diff != 0:
                    hist_new = np.vstack((np.zeros((diff,hist_new.shape[1])),hist_new))
                elif max(ybins_new) > max(ybins_prev):
                    diff = round((max(ybins_new)-max(ybins_prev))/ybinwidth)
                    #if diff != 0:
                    hist_prev = np.vstack((np.zeros((diff,hist_prev.shape[1])),hist_prev))    
                
                #Added hisogram and bin edges
                hist = np.add(hist_new,hist_prev.astype(dtype=np.float64)) #Add hist counts together
                nbins_x = hist.shape[1]
                nbins_y = hist.shape[0]
                xbin_edges = np.linspace(0,max(max(xbins_new),max(xbins_prev)),round(nbins_x)+1)
                ybin_edges = np.linspace(min(min(ybins_new),min(ybins_prev)),max(max(ybins_new),max(ybins_prev)),round(nbins_y)+1)
                

                return hist.astype(dtype=np.int64), xbin_edges, ybin_edges

            def align_hist1D(xx,hist_prev,bins_prev,**kwargs):
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
                    # print("new_bin_func")
                    bin_width = kwargs.get("bin_width",10) #Get bin width if supplied
                    rem1 = max(xx) % bin_width #Remainder
                    rem2 = min(xx) % bin_width #Remainder
                    #nbins = ((max(xx)-min(xx))//bin_width)+1 #Calculate number of bins
                    nbins = ((max(xx)+bin_width-rem1-(min(xx)-rem2))//bin_width) #Calculate number of bins
                    nbins = kwargs.get("bins",nbins) #Get number of bins if supplied, and override nbins

                    
                    # if len(bins_prev) != 0:
                    #     bin_width = bins_prev[1]-bins_prev[0]
                    #     # print(bin_width)
                    #     # print(max(xx)+bin_width-rem1,min(xx)-rem2)
                    #     # print((max(xx)+bin_width-rem1-min(xx)-rem2))
                    #     nbins = ((max(xx)+bin_width-rem1-(min(xx)-rem2))//bin_width) #Calculate number of bins
                        

                    

                    #Find new histogram
                    # print(min(xx),max(xx))
                    # print(rem1,rem2)
                    # print(round(min(xx)-rem2),round(max(xx)+bin_width-rem1))
                    #print(nbins)
                    hist_new, bins_new = np.histogram(xx,bins=round(nbins),range=(round(min(xx)-rem2),round(max(xx)+bin_width-rem1))) #Histogram
                    if (bins_new[1]-bins_new[0]) != bin_width:
                        hist_new, bins_new = np.histogram(xx,bins=round(nbins+1),range=(round(min(xx)-rem2),round(max(xx)+bin_width-rem1))) #Histogram
                    
                    #print(hist_new)
                    #print(bin_width, nbins,round(nbins), bins_new,(round(min(xx)-rem2),round(max(xx)+bin_width-rem1)), min(xx), rem2 ,max(xx),rem1)
                    # print(bins_new)
    
                    #If the previous histogram does not exist
                    if np.sum(hist_prev) == [0]:
                        hist_prev = np.array([0]*len(hist_new))
                        bins_prev = bins_new

                    #Aligning by adding zeros around the arrays
                    binwidth = round(bins_new[1]-bins_new[0])
                    if min(bins_new) < min(bins_prev):
                        diff = round((min(bins_prev)-min(bins_new))/binwidth)
                        hist_prev = np.concatenate((np.zeros(diff),hist_prev))
                        # print(f"diff1 {diff}")
                    elif min(bins_new) > min(bins_prev):
                        diff = round((min(bins_new)-min(bins_prev))/binwidth)
                        hist_new = np.concatenate((np.zeros(diff),hist_new))
                        # print(f"diff2 {diff}")
                    
                    if max(bins_new) < max(bins_prev):
                        diff = round((max(bins_prev)-max(bins_new))/binwidth)
                        hist_new = np.concatenate((hist_new,np.zeros(diff)))
                        # print(f"diff3 {diff}")
                    elif max(bins_new) > max(bins_prev):
                        diff = round((max(bins_new)-max(bins_prev))/binwidth)
                        hist_prev = np.concatenate((hist_prev,np.zeros(diff)))
                        # print(f"diff4 {diff}")

                    #nbins = max(len(bins_new),len(bins_prev))
                    nbins = round((max(max(bins_new),max(bins_prev))-min(min(bins_new),min(bins_prev))) / (bins_new[1]-bins_new[0]) + 1)

                    bin_edges = np.linspace(min(min(bins_new),min(bins_prev)),max(max(bins_new),max(bins_prev)),round(nbins))
                    # print(round(nbins),min(min(bins_new),min(bins_prev)),max(max(bins_new),max(bins_prev)))
                    # print(bin_edges)

                    hist = np.add(hist_new,hist_prev) #Add hist counts together

                    return hist.astype(dtype=np.int64), bin_edges
                except:
                    print("binfunc Debug info")
                    print(hist_prev)
                    print(hist_new)
                    print(len(hist_new),len(hist_prev))
                    print(bins_prev)
                    print(bins_new)
                    print(len(bins_new),len(bins_prev))
                    print(binwidth)
                    print(diff)
            
            #Gather previous results
            # if hist_data == {}:
            #     hist_data = np.zeros((1,1))
            try:
                hist_prev = hist_data["hist"]
                bins_prev = hist_data["bin_edges"]
                
            except:
                hist_prev = np.zeros((1,1))
                bins_prev = [[],[]]

            #Align data
            if yy != []:
                hist, x_edges, y_edges = align_hist2D(xx,yy,hist_prev,bins_prev[0],bins_prev[1],**kwargs)
                return hist, x_edges, y_edges
            else:
                hist, edges = align_hist1D(xx,hist_prev,bins_prev[0],**kwargs)
                return hist, edges

    def damage_accum(result,prev_result):
        """Accumulate damage for a continuous data stream
        
        Parameters
        ----------
        result  :   dict
            Dictionary of results from continous data stream.
        prev_result  :   dict
            Dictionary of previous results from continous data stream.
        
        Output
        ----------
        result  :   dict
            Dictionary of results from continous data stream.
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

    def RUL(result,t_nom,damage_sum = 1):
        """Remaining useful life (RUL)
        
        Args:
            result (dict): Dictionary of results from continous data stream.
                - 'D_tot' (float): New damage applied
            t_nom (float): Nominal life of system
            damage_sum (float): Damage sum to failure
        
        Returns:
            - 'RUL' (float): Remaining useful life
        """

        D_tot = result["D_t"]
        RUL = t_nom * (damage_sum - D_tot)

        return RUL

    def EOF_RUL(result,time_passed,output_time_unit="hr",damage_sum = 1):
        """End of life (EOF) or endurable life and Remaining useful life (RUL)

        Example 1:
        time_passed = 24 hr
        D_tot = 0.1

        EOF = 240 hr #The end of life is at 240 hours
        RUL = (EOF - time_passed) = 226 hr #Remaining useful life (RUL) is then 226 hours

        Example 2:
        time_passed = 1,000,000 cycles
        D_tot = 0.2

        EOF = 5,000,000 cycles #The end of life is at 5 mio. cycles.
        RUL = (EOF - time_passed) = 4,000,000 cycles #Remaining useful life (RUL) is then 4 mio. cycles
        
        Args:
            result (dict): Dictionary of results from continous data stream.
                - 'D_tot' (float): New damage applied
            time_passed (int/datetime.timedelta): Specified cycles or time passed
            output_time_unit (int/datetime): Output unit for cycles or time       
        
        Returns:
            EOF (float): End of life (EOF) or endurable life
            RUL (float): Remaining useful life (RUL) 
        """

        D_tot = result["D_t"]

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
        
        EOF = time_elapsed / (D_tot/damage_sum)
        RUL = EOF - time_elapsed

        return EOF, RUL

    def plot_eol_rul(result,inital_time ,current_time,output_time_unit,damage_sum,x_length=None,**kwargs):
        import matplotlib.dates as mdates

        #Get plot data from previous figure
        fig = kwargs.get("figure",None)
        if fig is None:
            fig, ax1 = plt.subplots(1,1,figsize=(6, 4), tight_layout=True)
            xdata_eol = []
            ydata_eol = []
            xdata_rul = []
            ydata_rul = []
        else:
            ax1 = fig.get_axes()[0]
            line1 = ax1.lines[0]
            xdata_eol = line1.get_xdata().tolist()
            ydata_eol = line1.get_ydata().tolist()

            # ax2 = fig.get_axes()[0]
            line2 = ax1.lines[1]
            xdata_rul = line2.get_xdata().tolist()
            ydata_rul = line2.get_ydata().tolist()
            ax1.clear()

            if x_length is not None:
                xdata_eol = xdata_eol[-x_length:]
                ydata_eol = ydata_eol[-x_length:]
                xdata_rul = xdata_rul[-x_length:]
                ydata_rul = ydata_rul[-x_length:]
            # ax2.clear()

        time_passed = current_time - inital_time
        eol, rul = fatigue.EOF_RUL(result,time_passed,output_time_unit,damage_sum=damage_sum)

        xdata_eol = xdata_eol + [current_time]
        ydata_eol = ydata_eol + [eol]

        xdata_rul = xdata_rul + [current_time]
        ydata_rul = ydata_rul + [rul]

        
        ax1.plot(xdata_eol,ydata_eol,'*-',label="EOL",zorder=0)
        #ax1.set_title("End Of Life (EOF) and Remaining Useful Life (RUL)")
        ax1.set_ylabel("EOL ["+output_time_unit+"]")

        ax1.plot(xdata_rul,ydata_rul,c="r",label="RUL",zorder=3)
        #ax1.set_yscale('log')
        ax1.set_ylabel("EOL and RUL ["+output_time_unit+"]")

        # date.autoformatter.year     : %Y
        # date.autoformatter.month    : %Y-%m
        # date.autoformatter.day      : %Y-%m-%d
        # date.autoformatter.hour     : %m-%d %H
        # date.autoformatter.minute   : %d %H:%M
        # date.autoformatter.second   : %H:%M:%S
        # date.autoformatter.microsecond   : %M:%S.%f

        if output_time_unit == "years":
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            xlabel_string = "Time passed [YY:MM:DD]"
        elif output_time_unit == "days":
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
            xlabel_string = "Time passed [MM:DD HH:mm]"
        elif output_time_unit == "hrs":
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H-%M'))
            xlabel_string = "Time passed [HH:mm]"
        else:
            xlabel_string = "Time passed [cycles]"
        ax1.set_xlabel(xlabel_string)
        ax1.set_xlim(xdata_rul[0],current_time)
        fig.autofmt_xdate(rotation=90)
        plt.subplots_adjust(bottom=0.15)
        ax1.grid()
        ax1.legend(loc='lower center')
        fig.tight_layout()
        damage_text = "$D_{\mathrm{tot}}$ = " + f"{float(result['D_t']):.3e}"

        #0.1, 0.925
        ax1.text(0.18, 0.925, damage_text, size=13,
                ha="center", va="center", transform = ax1.transAxes,
                bbox={'boxstyle':"Square",
                        'ec':(1., 0.5, 0.5),
                        'fc':(1., 0.8, 0.8)
                        }
                )

        return fig

    def rainflow_validation(test):
        match test:
            case 1:
                print("RAINFLOW TEST: Single cyclic time series.") 
                time_series_test = [1,-1,1,-1,1,-1,1]
            case 2:
                print("RAINFLOW TEST: Double cyclic time series") 
                time_series_test = [500,300,500,-500,-300,-500,500,300,500,-500,-300,-500,500]
                time_series_test = [500,300,500,-500,-300,-500,500,300,500,-500,-300,-500,500,300,500,-500]
            case 3:
                print("RAINFLOW TEST: Time series from [3]")
                #time_series_test = [2,-1,3,-5,1,-3,4,-4,2] #from [3]
                time_series_test = [-5,1,-3,4,-4,2,-1,3,-5] #sorted from [3]
            case 4:
                print("RAINFLOW TEST: Time series from [6]")
                #time_series_test = [0,-150,100,0,130,-120,110,-50,80,0,150,-100,100,0,130,0] #from website https://fatigue-life.com/rainflow-counting/
                time_series_test = [150,-100,100,0,130,-150,100,0,130,-120,110,-50,80,0,150] #sorted from website
            case 5:
                print("RAINFLOW TEST: Time series from gaussian noise. ASTM will be different since data is not correctly ordered")
                l = 1
                time = np.linspace(0,l,num=20)
                mu = 100
                std_dev = 10
                np.random.seed(1)
                time_series_test = (mu + std_dev * np.random.randn(1, len(time)))[0]
            case _:
                print("TEST: Time series from [2]")
                #time_series_test = [4,7,1,10,5,9,3,4,2,12,5,11,1,4,3,10,6,12,4,8,1,9,4,6] #not sorted [2]
                time_series_test = [12,5,11,1,4,3,10,6,12,4,8,1,9,4,6,4,7,1,10,5,9,3,4,2,12] #sorted [2]
        #ASTM classic rainflow counting
        # try:
        #     print(f"ASTM: {rainflow_ASTM.count_cycles(time_series_test)}")
        # except:
        #     print("ASTM rainflow module is not imported")

        #4-point rainflow counting
        Delta_sigma,sigma_m,n_count = fatigue.rainflow(time_series_test)
        fatigue.plot_time_series(time_series_test,"time_series_validation.svg")
        print(f"Stress ranges (Delta_sigma):     {Delta_sigma}")
        print(f"Mean stress (sigma_m):           {sigma_m}")
        print(f"Counted (n_count):               {n_count}")

        return
    
    def example_eurocode3():
        #Example from [4,6] Appendix: welded lifting eye, following Eurocode 3 and the Danish regulation for safety factors.
        #Root-check
        print("\nExample from compendium [4,6]: Static calculations")
        # Static
        sigma = 193.9 #[MPa]
        tau = -30.16 #[MPa]
        
        # Load partial safety factor
        gamma_f = 1.3 #Partial safety factor for fatigue load, look up depending on load uncertainty

        # Design load stress
        sigma_ed = sigma*gamma_f
        tau_ed = tau*gamma_f

        # Check for yielding and ultimate stress for fillet welds
        sigma_per = sigma_ed / (2)**(1/2)
        tau_per = sigma_per
        tau_par = tau_ed
        stress_ref = (sigma_per**2 + 3*(tau_per**2 + tau_par**2))**0.5

        beta_w = 0.85 # Table 4.1
        beta_wl = 1 # long welds EC3-1-8 sec. 4.11
        gamma_3 = 0.95 # Normal/Expanded control class
        gamma_M2 = 1.35 * gamma_3 #Partial safety factor Dansih code
        f_y = 275 # [MPa] Yield strength
        f_u = 430 # [MPa] Ultimate strength
        stress_y = f_y / (gamma_M2 * beta_w)
        stress_u = f_u / (gamma_M2 * beta_w)

        #EC3-1-8 sec.4.5 or [5] p. 106
        print(f"Stress von mises criterium: {stress_ref <= stress_u}") 
        print(f"Sigma perpendicular criterium: {sigma_per <= 0.9*f_u / gamma_M2}")
        print(f"Tau parallel criterium yield: {tau_par <= f_u / ((3)**(1/2) * beta_w*gamma_M2) * beta_wl}")


        print("Fatigue calculations CA (constant amplitude)")
        # Stress ranges Constant amplitude
        Delta_sigma = [122]
        Delta_tau =  [26.8]

        # Fatigue yield check
        #EC3-1-9 sec. 8 or [5] p. 110
        print(f"Sigma criterium yield: {max(Delta_sigma) <= 1.5*f_y}")
        print(f"Tau criterium yield: {max(Delta_tau) <= 1.5*f_y / (3)**(1/2)}")
        
        # Fatigue safty factor
        gamma_Ff = 1.0 #Uncertainty of the stress range
        gamma_Mf = 1.54 #Safety factor for fatigue strength, Saffe Life method, Danish code, look up depending on weld fatigue safety
        SF = gamma_Mf*gamma_Ff

        Delta_sigma = Delta_sigma*2**(1/2) #[MPa] sqrt(Delta_sigma_per**2+Delta_tau_per**2)   Delta_sigma_per=Delta_tau_per
        Delta_tau = [26.8] #[MPa]

        SN_curve = fatigue.eurocode_SN(36,"sigma*",SF,signal_type="CA")
        N_s = fatigue.cycles_SN(SN_curve,Delta_sigma)

        SN_curve = fatigue.eurocode_SN(80,"tau",SF)
        N_t = fatigue.cycles_SN(SN_curve,Delta_tau)

        D = fatigue.damage(N_s,1,N_t,1)
        print(f"Cycle life at combined loading of root: {1/D}") # N = 1/D

        #Toe-check
        Delta_sigma = [138] #[MPa]
        Delta_tau = [21.4] #[MPa]
        Delta_sigma = [207] #[MPa]
        Delta_tau = [32] #[MPa]

        SN_curve = fatigue.eurocode_SN(71,"sigma",SF=SF,signal_type="VA")
        N_s = fatigue.cycles_SN(SN_curve,Delta_sigma)

        SN_curve = fatigue.eurocode_SN(80,"tau",SF=SF)
        N_t = fatigue.cycles_SN(SN_curve,Delta_tau)

        D = fatigue.damage(N_s,1,N_t,1)
        print(f"Cycle life at combined loading of toe: {1/D}") # N = 1/D

        print("Variable amplitude for root, since it is most critical")
        print("Eurocode 3-1-9 and [5]:")
        Delta_sigma = 172.5 #[MPa]
        Delta_tau = 26.8 #[MPa]
        transfer_function_sigma = Delta_sigma/80 #[MPa]/80 [kN]
        transfer_function_tau = Delta_tau/80 #[MPa]/80 [kN]

        load_list = [80,65,50,20,5]
        n_count_s = [10,2*10**2,5*10**2,8*10**3,3*10**4]
        Delta_sigma = [x * transfer_function_sigma for x in load_list]
        Delta_tau_par = [x * transfer_function_tau for x in load_list]
        n_count_t = [10,2*10**2,5*10**2,8*10**3,3*10**4]
        
        #Delta_sigma = Delta_sigma_per*sqrt(2) which yields the same fatigue results since: Delta_sigma_per = Delta_tau_per, so sqrt(Delta_sigma_per**2 + Delta_tau_per**2) = sqrt(Delta_sigma_per**2 + Delta_sigma_per**2) = Delta_sigma
        SN_curve = fatigue.eurocode_SN(36,"sigma*",SF,signal_type="VA")
        N_s, n_s, Delta_significant_sigma = fatigue.cycles_SN(SN_curve,Delta_sigma,n_count_s)
        fatigue.plot_SN_curve(SN_curve,hist_type="stair",stress_list=Delta_significant_sigma,n_count=n_s)

        SN_curve = fatigue.eurocode_SN(80,"tau",SF)
        N_t, n_t, Delta_significant_tau = fatigue.cycles_SN(SN_curve,Delta_tau_par,n_count_t)
        fatigue.plot_SN_curve(SN_curve,hist_type="stair",stress_list=Delta_significant_tau,n_count=n_t)

        D = fatigue.damage(N_s,n_s,N_t,n_t)
        print(f"Total damage for one year: {D}")
        print(f"Cycle life at root: {1/D}") # N = 1/D


        print(" --- Compendium [4]: ---")
        Delta_sigma = 172.5 #[MPa]
        Delta_tau = 26.8 #[MPa]

        transfer_function_sigma = Delta_sigma/80 #[MPa]/80 [kN]
        transfer_function_tau = Delta_sigma/80 #[MPa]/80 [kN]

        time = np.linspace(0,24,num=10*24) #10 samples pr. hour, for 24 hours
        mu = 100
        std_dev = 10
        np.random.seed(1)
        noise = mu + std_dev * np.random.randn(1, len(time))
        time_series = noise

        time_series_sigma = [x * transfer_function_sigma for x in time_series][0]
        time_series_tau = [x * transfer_function_tau for x in time_series][0]

        Delta_sigma,mean_stress,n_count_s = fatigue.rainflow(time_series_sigma)
        Delta_tau,_,n_count_t = fatigue.rainflow(time_series_tau)

        n_year_s = [x * 365.25 for x in n_count_s]
        
        SN_curve = fatigue.eurocode_SN(36,"sigma*",SF,signal_type="VA")
        N_s, n_s, Delta_significant_sigma = fatigue.cycles_SN(SN_curve,Delta_sigma,n_count_s)
        n_eq=2*10**6
        sigma_eq = fatigue.eq_stress(Delta_significant_sigma,n_s,SN_curve,n_eq)
        UR = fatigue.UR(sigma_eq,SN_curve,n_eq)
        
        SN_curve = fatigue.eurocode_SN(80,"tau",SF)
        N_t, n_t, Delta_significant_tau = fatigue.cycles_SN(SN_curve,Delta_tau,n_count_t)

        D = fatigue.damage(N_s,n_s,N_t,n_t)
        print(f"Total damage for one day: {D}")

        #Scaling from one day to a year
        n_year_s = [x * 365.25 for x in n_s]
        n_year_t = [x * 365.25 for x in n_t]
        
        D = fatigue.damage(N_s,n_year_s,N_t,n_year_t)
        print(f"Total damage for one year: {D}")
        print(f"Estimated total life: {1/D} years") # N = 1/D


        #This does not yield satisfying results:
        # print(f"Equivalent stress: {sigma_eq}")
        # SN_curve = fatigue.IIW_SN(40,"sigma",SF,signal_type="VA") #Instead of EC3 sigma* 36, where stress_eq is a run-out, then use IIW at 40
        # cycles_sigma, n_s, s_s_res = fatigue.cycles_SN(SN_curve,[sigma_eq],[n_eq])
        # D = fatigue.damage(cycles_sigma,n_s)
        # print(f"Damage from equivalent stress: {D}")

        print(f"\n")
        return 

    def example_IIW():
        """IIW fatigue example sec. 6.6"""
        print("Fatigue assesment example IIW sec. 6.6")
        print("SN-curve test FAT=80:")
        FAT = 80
        SF = 1.1
        SN_curve = fatigue.IIW_SN(FAT,"sigma",SF,signal_type="CA")
        stress_list = [140]
        cycles = fatigue.cycles_SN(SN_curve,stress_list)
        print(f"N, cycles: {cycles}")
        
        print("Load case for CA at 2*10**6 cycles:")
        print(f"Gough-Pollard criterion for multiaxial stress: {(40/(FAT/SF))**2 + (30/(FAT/SF))**2}. Should be less than 1")
        

        print("Load case for uniaxial VA, FAT=100:")
        FAT = 100
        SF = 1
        SN_curve = fatigue.IIW_SN(FAT,"sigma",SF,signal_type="VA")
        #fatigue.plot_SN_curve(SN_curve)
        stress_list = [140.44, 122.89, 105.33, 87.78, 70.22, 52.67, 35.11, 17.55]
        n_count = [10**1, 9*10**1, 9*10**2, 9*10**3, 9*10**4, 9*10**5, 9*10**6, 9*10**7]
        stress_list = [17.55]
        n_count = [9*10**7]
        stress_list = [140.44]
        n_count = [10**1]
        stress_list = [70.22]
        n_count = [9*10**4]
        stress_list = [52.67]
        n_count = [9*10**5]


        # fatigue.plot_SN_curve(SN_curve,hist_type="bar",stress_list=stress_list,n_count=n_count)
        # fatigue.plot_SN_curve(SN_curve,hist_type="stair",stress_list=stress_list,n_count=n_count)

        cycles_sigma, n_s, s_s_res = fatigue.cycles_SN(SN_curve,stress_list,n_count)

        D = fatigue.damage(cycles_sigma,n_s)
        print(f"Damage VA: {D:.3}")
        print(f"Life left (multiple of load sequence): {1/D:.3}")
        print(f"Life left to D = 0.5 (multiple of load sequence): {0.5/D:.3}")
        print(f"Cycles left to D = 0.5: {0.5/D * sum(n_count):.4E}")
        
        print("Find eq_stress at D=1")
        n_eq=sum(n_count)
        stress_eq = fatigue.eq_stress(s_s_res,n_count,SN_curve,n_eq)
        print(f"Equivalent stress: {stress_eq}")
        cycles_sigma, n_s, s_s_res = fatigue.cycles_SN(SN_curve,[stress_eq],[n_eq])
        D = fatigue.damage(cycles_sigma,n_s)
        print(f"Damage from equivalent stress: {D}")
        UR = fatigue.UR(stress_eq,SN_curve,n_eq)
        print(f"Utilization ratio: {UR}")

        stress_eq = fatigue.eq_stress_D(s_s_res,n_count,SN_curve,D=1,n_eq=n_eq)
        print(f"Equivalent stress: {stress_eq}")
        cycles_sigma, n_s, s_s_res = fatigue.cycles_SN(SN_curve,[stress_eq],[n_eq])
        D = fatigue.damage(cycles_sigma,n_s)
        print(f"Damage from equivalent stress: {D}")
        UR = fatigue.UR(stress_eq,SN_curve,n_eq)
        print(f"Utilization ratio: {UR}")

        print("Finding eq_stress is problematic because of many points under the knee-point")
        print("Find eq_stress at D=0.5")
        stress_list = [140.44, 122.89, 105.33, 87.78, 70.22, 52.67, 35.11, 17.55]
        stress_list = [x* 1.284 for x in stress_list]
        n_count = [10**1, 9*10**1, 9*10**2, 9*10**3, 9*10**4, 9*10**5, 9*10**6, 9*10**7]

        cycles_sigma, n_s, s_s_res = fatigue.cycles_SN(SN_curve,stress_list,n_count)
        D = fatigue.damage(cycles_sigma,n_s)
        print(f"Damage VA: {D:.3}")

        print("At least one error is apparant in the example.")
        print("With equivalent stress at 18.75 and 10**8, the example states a D = 0.5 is achieved.")
        cycles_sigma, n_s, s_s_res = fatigue.cycles_SN(SN_curve,[18.75],[10**8])
        D = fatigue.damage(cycles_sigma,n_s)
        print(f"Correct damage: {D}")
        print(f"\n")
        return

    def example_DNV():
        """Drum fatigue assessment from sec. F15"""
        print("Calculate life of drum")
        a = 1200 #mm
        P = 118.1 #kN load
        M = P*a/2 #Nm
        
        #Section modulus
        W = 5115*10**3 #mm^3
        #Stress concentration factor
        SCF = 1.34

        #Constant amplitude fatigue
        Delta_sigma = M*2 / W * SCF *1000 #MPa

        DFF = 2
        SF = 1

        print(f"Stress: {Delta_sigma}")
        SN_curve = fatigue.DNV_SN("plate","air",detail="E",SF=SF,DFF=DFF) #From table A-7
        fatigue.plot_SN_curve(SN_curve)

        cycles, n, stress = fatigue.cycles_SN(SN_curve,[Delta_sigma],[1])
        D = fatigue.damage(cycles,n)
        print(f"Damage: {D}")
        print(f"Fatigue life: {1/D}")
        return

class run_fatigue():
    """Fatigue analysis run
    Parameters
    ----------
    SN_curve    :   dict
        Dictionary of SN-curve
    """
    def __init__(self, SN_curve):
        self.SN_curve = SN_curve
        self.result = {}
        self.SN_hist = {}
        self.heatmap = {}
        self.histogram = {}

    def run(self,time_series,**kwargs):
        """Run fatigue analysis
        
        Parameters
        ----------
        time_series    :   list of float
            Data for rainflow counting
        result    :   dict
            Dictionary of results from continous data stream. Empty ={} for first instance.
        **kwargs    :   plot_rainflow:  Boolean
            Plot rainflow counting
        Output
        ----------
        result  :   dict
            Dictionary of results from continous data stream.
        """
        prev_result = self.result

        if 'residual_signal' in prev_result.keys():
            time_series = np.array(prev_result["residual_signal"] + time_series.tolist())

        
        result1 = self.calc(time_series,**kwargs)
        #Find residual result
        result2 = self.calc(result1["residual_signal"],result1["residual_signal"])
        result = {}
        key_list = list(result1.keys())
        for x in key_list:
            if x == 'stress':
                result[x] = result1[x]
                result['stress_residual'] = result2[x]
            elif x == 'mean_rain':
                result[x] = result1[x]
                result['mean_rain_residual'] = result2['mean_rain']
            elif x == 'n_rain':
                result[x] = result1[x]
                result['n_rain_residual'] = result2[x]
            elif x == 'residual_signal':
                result[x] = result2[x]    
            elif x == 'D':
                result[x] = result1[x]
                result['D_residual'] = result2[x]
            elif x == 'stress_res':
                result[x] = result1[x]
                result['stress_res_residual'] = result2[x]
            elif x == 'n':
                result[x] = result1[x]
                result['n_residual'] = result2[x]
            else:
                result[x] = result1[x] + result2[x]

        self.result = fatigue.damage_accum(result,prev_result)
        # self.result_update(result)

        return self

    def calc(self,time_series,residual=[],**kwargs):
        """Fatigue calculations
        
        Parameters
        ----------
        time_series    :   list of float
            Data for rainflow counting
        residual    :   list of float
            Data for previous residual
        **kwargs    :   plot_rainflow:  Boolean
            Plot rainflow counting
        
        Output
        ----------
        result  :   dict
            Dictionary of results from continous data stream.
        """
        plot_rainflow = kwargs.get("plot_rainflow",False)
        stress_list, mean_list, n_count, residual, plot_data = fatigue.rainflow_c(time_series,residual,output="list")
        if plot_rainflow == True:
            fatigue.plot_rainflow(plot_data)
        cycles, n, res_stress, res_mean = fatigue.cycles_SN(self.SN_curve,stress_list,n_count,mean_list)
        D = fatigue.damage(cycles,n)

        result = {
            "stress": stress_list,
            "mean_rain": mean_list,
            "n_rain": n_count,
            "residual_signal": residual,
            "cycles":cycles,
            "n":n,
            "stress_res": res_stress,
            "mean_res": res_mean,
            "D": D 
        }

        return result
    
    def plot_damage(self,**kwargs):
        """Damage plot data

        Parameters
        ----------
        self    :   self
            result: Dictionary of results from continous data stream

        Outputs
        ----------
        y_points     :   list of float
            y values of total damage
        y_points     :   list of float
            y values of instant damage
        """
        return self.result["D_t"], self.result["D"], self.result["D_accum"], self.result["D_residual"]
    
    def result_update(self,result_dict):
        for key in result_dict.keys():
            if type(result_dict[key]) == list:
                self.result[key] = result_dict[key].copy()
            else:
                self.result[key] = result_dict[key]
        return self
    
    def hist_update(self,hist):
        self.SN_hist = hist.copy()
        return self
    
    def heatmap_update(self,heatmap):
        self.heatmap = heatmap.copy()
        return self
    
    def histogram_update(self,hist_data):
        #print("update1",hist_data["bin_edges"])
        self.histogram[hist_data["name"]] = hist_data.copy()
        #print("update2",self.histogram[hist_data["name"]]["bin_edges"])
        return self

    def plot_SN_curve(self,**kwargs):
        """Histogram plot data

        Parameters
        ----------
        self    :   self
            result: Dictionary of results from continous data stream

        Outputs
        ----------
        x_curve     :   list of float
            x values of SN-curve
        y_curve     :   list of float
            y values of SN-curve
        x_points     :   list of float
            x values of histogram
        y_points     :   list of float
            y values of histogram
        """

        x_curve, y_curve, x_points, y_points, hist = fatigue.SN_curve_plotdata(self.SN_curve,self.result,self.SN_hist,**kwargs)
        self.hist_update(hist)
        
        for id,x in enumerate(x_points):
            if x < 1:
                x_points[id] = 1
        for id,x in enumerate(y_points):
            if x < 1:
                y_points[id] = 1

        return x_curve, y_curve, x_points, y_points
    
    def plot_histogram(self,dict_name,result_name1,result_name2,**kwargs):
        
        if dict_name in self.histogram.keys():
            prev_hist_data = self.histogram[dict_name]
        else:
            prev_hist_data = {}


        list_1 = self.result[result_name1]
        list_2 = self.result[result_name2]
        list_ = list_1+list_2
        
        
        hist_tot, bin_edges = fatigue.bin_func(list_,prev_hist_data,**kwargs) #For plotting with residual part together with previous hist
        hist_next, bin_edges_next = fatigue.bin_func(list_1,prev_hist_data,**kwargs) #For next plot, without residual data
        # if dict_name == "mean":
        #     print(min(list_1),max(list_1))
        #     print(min(list_2),max(list_2))
        #     print(prev_hist_data["bin_edges"])
        #     print(bin_edges)
        #     quit()

        hist_data = {
                "name":dict_name,
                "result_name": [result_name1,result_name2],
                "hist":hist_next,
                "bin_edges":[bin_edges_next],
            }

        self.histogram_update(hist_data)


        bin_width = bin_edges[2]-bin_edges[1]
        rem = bin_width*10 % 10
        labels = []
        for id, x in enumerate(bin_edges[:-1]):
            if rem == 0:
                labels.append("[" + str(int(x)) + ":" + str(int(x+bin_width)) + "[")
            else:
                labels.append("[" + str(round(x,3)) + ":" + str(round(x+bin_width,3)) + "[")
        # print(len(labels),len(hist_tot))
        # print(hist_tot)
        # print(bin_edges)
        # print(labels)
        # if len(labels) != len(hist_tot):
        #     print(hist_tot)
        #     print(bin_edges)
        #     print(labels)

        bin_width = bin_edges_next[2]-bin_edges_next[1]
        labels_next = []
        for id, x in enumerate(bin_edges_next[:-1]):
            if rem == 0:
                labels_next.append("[" + str(int(x)) + ":" + str(int(x+bin_width)) + "[")
            else:
                labels_next.append("[" + str(round(x,3)) + ":" + str(round(x+bin_width,3)) + "[")


        return hist_tot, labels, hist_next, labels_next


    def plot_heatmap(self,**kwargs):
        try:
            self.heatmap
        except:
            self.heatmap = {}

        
        hist2D, x_edges, y_edges, self.heatmap = fatigue.heatmap_data(self.heatmap,self.result,**kwargs)
        print(self.heatmap)
        
        bin_width = x_edges[2]-x_edges[1]
        rem = bin_width*10 % 10
        x_labels = []
        for id, x in enumerate(x_edges):
            if rem == 0:
                x_labels.append("[" + str(int(x)) + ":" + str(int(x+bin_width)) + "[")
            else:
                x_labels.append("[" + str(x) + ":" + str(x+bin_width) + "[")

        bin_width = y_edges[1]-y_edges[0]
        rem = bin_width*10 % 10
        y_labels = []
        for id, x in enumerate(y_edges):
            if rem == 0:
                y_labels.append("[" + str(int(x)) + ":" + str(int(x+bin_width)) + "[")
            else:
                y_labels.append("[" + str(x) + ":" + str(x+bin_width) + "[")

        return hist2D, x_labels[:-1], y_labels[:-1]

    def stress_data(self,**kwargs):
        stress = self.result['stress']
        mean_stress = self.result['mean_rain']
        stress_R = self.result['stress_residual']
        mean_stress_R = self.result['mean_rain_residual']

        return stress, mean_stress, stress_R, mean_stress_R

        
