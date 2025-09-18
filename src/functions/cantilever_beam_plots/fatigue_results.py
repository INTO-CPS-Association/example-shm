import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from methods.packages.fatigue_block import fatigue as fat
from methods.fatigue import RunFatigue


def fatigue_plots(data):
    start_time = datetime(2025, 6, 24, 14, 0, 0)
    end_time = datetime(2025, 6, 24, 14, 0, 0)
    passed_time = end_time - start_time

    t = 2
    k_thick = 1 #(25/t)**(0.1) #Base material. k_thick = 1 for t under 25mm
    R = -120/160 # sigma_min / sigma_max
    k_rs = -0.4*R + 1.2 #Low residual stress
    mean_stress = 25 #To be adjusted
    R_m = 360 #MPa #Ultimate tensile strength Low value for s235
    k_mean = 1# 1 - mean_stress/R_m #Modified Goodman
    SaftyFactor = 1 * 1/k_thick * 1/k_rs * 1/k_mean
    print(f"SF: {SaftyFactor}")
    SN_curve = fat.IIW_SN(140,"sigma",SF=SaftyFactor,signal_type="VA")
    damage_sum = 0.5
    #SN_curve = fat.eurocode_SN(140,"sigma",SF=1,signal_type="VA")
    beam = RunFatigue(SN_curve)

    for counter, batch in enumerate(data):
        if max(batch) > 300:#counter in [29,30,59,60,90,91,92,93,120,121,122,123,124,125,149,150,151,152,153,154,155,156]:#[29,30,62,63]: #Ignore datasets with immense stress/vibrations from mass perturbations by hand
            pass
        else:
            print(f"count: {counter}")
            beam.run(batch)
            
            # if counter > 0:
            #     ax7.clear()
            # else:
            #     fig7, ax7 = plt.subplots(1,1)
            # ax7.plot(beam.result['residual_signal'])
            
            end_time = end_time + timedelta(minutes=2)
            print(f"time: {end_time}")

            if counter == 0:
                #fig1, ax1, hist1 = fat.plot_SN_curve(SN_curve,result=beam.result,hist_data={},bin_width=10)
                #fig2, ax2 = fat.plot_damage(result=beam.result)
                #fig3, ax3, hist3 = fat.plot_histogram(result=beam.result,bin_width=10,hist_data={},static_mean=0) #flag
                #fig4, ax4, hist4 = fat.plot_SN_curve(SN_curve,result=beam.result,bin_width=10,hist_type="stair")
                #fig5 = fat.plot_haigh(SN_curve,200,300,result=beam.result,points=500)
                fig6 = fat.plot_eol_rul(beam.result,start_time,end_time,output_time_unit="days",damage_sum = damage_sum)
                #fig7, ax7, _ = fat.plot_histogram(result=beam.result,bin_width=10,hist_data={},static_mean=0) #flag
            else:
                #_, ax1, hist1 = fat.plot_SN_curve(SN_curve,result=beam.result,hist_data=hist1,bin_width=10,figure=fig1)
                #_, ax2 = fat.plot_damage(result=beam.result,figure=fig2)
                #_, ax3, hist3 = fat.plot_histogram(result=beam.result,bin_width=10,hist_data=hist3,static_mean=0,figure=fig3) #flag
                #_, ax4, hist4 = fat.plot_SN_curve(SN_curve,result=beam.result,bin_width=10,hist_type="stair",figure=fig4)
                #_ = fat.plot_haigh(SN_curve,200,300,result=beam.result,points=500,figure=fig5)
                _ = fat.plot_eol_rul(beam.result,start_time,end_time,output_time_unit="days",damage_sum = damage_sum,figure=fig6)
                #fig7, ax7, _ = fat.plot_histogram(result=beam.result,bin_width=10,hist_data={},static_mean=0,figure=fig7) #flag
            plt.pause(0.1)

            D_t = beam.result['D_t']
            print(f"Damage: {D_t}")
            print(f"Endurable (days): {2*counter/D_t / 60 / 24}")

            passed = end_time - start_time
            print(f"EOF and RUL: {fat.EOF_RUL(beam.result,time_passed=passed,output_time_unit='days',damage_sum = damage_sum)}")

    plt.show(block=True)

    # x_hist = np.sum(hist3['hist'],axis=1)
    # bins = hist3['bin_edges'][1]
    # print(x_hist)

    # print(bins)
    # added=0
    # for ii,x in enumerate(bins[1:]):
    #     added = added+x * x_hist[ii]

    # print(f"mean: {added/sum(x_hist)}")

    return