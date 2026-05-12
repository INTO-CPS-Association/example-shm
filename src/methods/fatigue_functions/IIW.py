from typing import Optional, Any

def iiw_sn(FAT: int, stress_type: str,SF: Optional[float] = 1,
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