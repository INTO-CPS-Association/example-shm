from typing import Optional, Any

def synthetic_sn(material: str, R_m: float, SF: Optional[float] = 1) -> dict[str, Any]: 
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