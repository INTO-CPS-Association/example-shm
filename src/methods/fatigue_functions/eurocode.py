from typing import Optional, Any
# pylint: disable=C0103, C0301, R0912, R0914, R0915

def eurocode_sn(DC: int, stress_type: str, SF: Optional[float]=1,
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
            if signal_type not in ('VA', 'CA'):
                raise ValueError('Unknown signal type, use eg. signal_type = "VA" or "CA"')
        except ValueError as e:
            print("Problem:",e)

        if DC >= 71: #For large DC the slope is defined
            m1 = 7
            m2 = 7
            N_DC = 2*10**6 #Cycles at Detail Catagory
            N_D_CA = 2*10**6 #Cycles at constant amplitude
            N_D_VA = 10**8 #Cycles from knee-point to cut-off when the signal have variable amplitude
        else: #At other DC the slopes vary
            try:
                m1 = kwargs["m1"]
            except KeyError as exc:
                raise KeyError("m1-slope must be provided") from exc
            m2 = kwargs.get("m2",m1+2)

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
                if signal_type not in ('VA', 'CA'):
                    raise ValueError('Unknown signal type, use eg. signal_type = "VA" or "CA"')
            except ValueError as e:
                print("problem:", e)

            #For override of slope
            m1 = kwargs.get("m1",3)
            m2 = kwargs.get("m2",5)

            N_DC = 2*10**6 #Cycles at Detail Catagory
            N_D_CA = 5*10**6 #Cycles at constant amplitude
            N_D_VA = 10**8 #Cycles from knee-point to cut-off
                            # when the signal have variable amplitude

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
            #For override of slope
            m1 = kwargs.get("m1",5)
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
                if signal_type not in ('VA', 'CA'):
                    raise ValueError('Unknown signal type, use eg. signal_type = "VA" or "CA"')
            except ValueError as e:
                print("Error:", e)

            # Find the nearest DC above the given DC*
            DC_old = DC*SF

            result = next(k for k, value in enumerate(DC_list) if value > DC_old)
            DC_new = DC_list[result]/SF

            #For override of slope
            m1 = kwargs.get("m1",3)
            m2 = kwargs.get("m2",5)

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
