from typing import Optional, Any
import numpy as np

def dnv_sn(joint_type: str,enviroment: str,**kwargs: Optional[Any])-> dict[str, Any]: #2016 version
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
    

            elif enviroment.lower() == "seawater_cp":
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
        else:
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