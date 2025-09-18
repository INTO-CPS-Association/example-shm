from typing import Dict, Any, Optional, List, Self
from methods.packages.fatigue_block import fatigue
from functions.fatigue_plots import plot_rainflow

class RunFatigue():
    """Fatigue analysis run
    Args:
        sn_curve (dict): Dictionary consisting of SN curve parameters.
            - 'SF' (float): Safty factor.
            - 'N_DC' (int): Fatigue life at detail catagoy.
            - 'N_D' (List(int)): Fatigue life at knee points.
            - 'C' (List(float)): Fatigue capacity.
            - 'Delta_s_R_D' (List(float)): Fatigue limit at knee point(s).
            - 'm' List(int): SN-curve slope(s).
    """
    def __init__(self, sn_curve: Dict[str,Any]):
        self.sn_curve = sn_curve
        self.result = {}
        self.sn_hist = {}
        self.heatmap = {}
        self.histogram = {}

    def run(self,time_series: List[float],**kwargs: Optional[Any]) -> Self:
        """Run fatigue analysis
        
        Args:
            time_series (List(float)): Data for rainflow counting
            **kwargs (any):
                - plot_rainflow (Boolean): Plot rainflow counting
        
        Returns:
            result (dict): Dictionary of results from continous data stream.
                - 'stress' (List(float)): counts of stress ranges
                - 'stress_residual' (List(float)): counts of residual stress ranges
                - 'mean_rain' (List(float)): counts of mean stress
                - 'mean_rain_residual' (List(float)): counts of residual mean stress
                - 'n_rain' (List(int)): counts
                - 'n_rain_residual' (List(int)): counts of residual
                - 'residual_signal' (List(float)): residual signal
                - 'cycles' (List(float)): cycles from sn-curve
                - 'stress_res' (List(float)): Stress that is above the run-off knee point
                - 'stress_res_residual' (List(float)): Stress from the residual signal
                                                    that is above the run-off knee point
                - 'n' (List(int)): counts that is above the run-off knee point
                - 'n_residual' (List(int)): residual counts that is above the run-off knee point
                - 'D' (float): Damage from batch
                - 'D_residual' (float): Damage from residual signal
                - 'D_accum' (float): Accumulated damage without residual damage
                - 'D_t' (float): Accumulated damage total with residual damage (D_accum + D_res)
        """
        prev_result = self.result

        if 'residual_signal' in prev_result:
            time_series = prev_result["residual_signal"] + time_series

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
        return self

    def calc(self,time_series: List[float],residual: Optional[List[float]] = None,
             **kwargs: Optional[Any]):
        """Fatigue calculations
        
        Args:
            time_series (List(float)): Data for rainflow counting
            residual (List(float)): Data for previous residual
            **kwargs (any): 
                - plot_rainflow (Boolean): Plot rainflow counting
        
        Returns:
            result (dict): Dictionary of results from continous data stream.
                - 'stress' (List(float)): counts of stress ranges
                - 'mean_rain' (List(float)): counts of mean stress
                - 'n_rain' (List(int)): counts
                - 'residual_signal' (List(float)): residual signal
                - 'cycles' (List(float)): cycles from sn-curve
                - 'stress_res' (List(float)): Stress that is above the run-off knee point
                - 'n' (List(int)): counts that is above the run-off knee point
                - 'D' (float): Damage from batch
        """
        plot_rf = kwargs.get("plot_rainflow",False)
        if residual is None:
            residual = []
        stress_list, mean_list, n_count, residual, plot_data = fatigue.rainflow_c(time_series,residual,output="list")
        if plot_rf is True:
            plot_rainflow(plot_data)

        cycles, n, res_stress, res_mean = fatigue.cycles_SN(self.sn_curve,
                                                            stress_list,n_count,mean_list)

        damage = fatigue.damage(cycles,n)

        result = {
            "stress": stress_list,
            "mean_rain": mean_list,
            "n_rain": n_count,
            "residual_signal": residual,
            "cycles":cycles,
            "n":n,
            "stress_res": res_stress,
            "mean_res": res_mean,
            "D": damage 
        }
        return result
