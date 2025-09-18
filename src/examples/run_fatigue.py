from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from methods.packages.fatigue_block import fatigue as fat
from methods.fatigue import RunFatigue
from functions.fatigue_plots import (
    plot_sn_curve,
    plot_damage,
    plot_histogram,
    plot_cld,
    plot_eol_rul
    )

def run_damage_print():
    batch = [10, 2, 7, 9, 4, 9, 6, 5, 2, 9, 4, 9, 3, 7, 5, 0, 2, 8, 1, 5]


    # a = datetime.fromisoformat('2024-01-01 00:00:23.000')
    # b = datetime.fromisoformat('2025-01-01 01:00:23.001')

    # time_passed = b-a
    # result = {'D_t':0.2}
    # EOF, RUL = fat.EOF_RUL(result,time_passed,output_time_unit="years",damage_sum = 1)
    # print(EOF)
    # print(RUL)

    # time_passed = 1000000
    # EOF, RUL = fat.EOF_RUL(result,time_passed,output_time_unit="cycles",damage_sum = 1)
    # print(EOF)
    # print(RUL)

    sn_curve = fat.IIW_SN(140,"sigma",SF=1,signal_type="VA")
    joint1 = RunFatigue(sn_curve)
    joint1.run(batch)
    print(joint1.result['D_t'])

def run_fatigue_and_plot():
    counter = -1
    sn_curve = fat.IIW_SN(140,"sigma",SF=1,signal_type="VA")
    joint1 = RunFatigue(sn_curve)
    damage_sum = 0.5

    t1 = datetime.now()
    while counter < 100:
        counter = counter+1

        time = np.linspace(0,1,num=10000)
        mu = 300
        std_dev = 50
        batch = list((mu + std_dev * np.random.randn(1, len(time)))[0])

        if counter < 0:
            joint1.run(batch,plot_rainflow=True)
        else:
            joint1.run(batch)

        t2 = datetime.now()

        if counter == 0:
            fig1, hist1 = plot_sn_curve(sn_curve,result=joint1.result,hist_data={},bin_width=10)
            fig2 = plot_damage(result=joint1.result)
            fig3, hist3 = plot_histogram(result=joint1.result,bin_width=10,hist_data={},static_mean=0)
            fig4 = plot_cld(sn_curve,200,300,result=joint1.result,points=500)
            fig5 = plot_eol_rul(result=joint1.result,inital_time=t1,current_time=t2)
        else:
            _, hist1 = plot_sn_curve(sn_curve,result=joint1.result,
                                     bin_width=10,hist_data=hist1,figure=fig1)
            _ = plot_damage(result=joint1.result,figure=fig2)
            _, hist3 = plot_histogram(result=joint1.result,bin_width=10,figure=fig3,hist_data=hist3,static_mean=0)
            _ = plot_cld(sn_curve,235,300,result=joint1.result,figure=fig4,points=500)
            _ = plot_eol_rul(result=joint1.result,inital_time=t1,current_time=t2,output_time_unit="years",damage_sum=damage_sum,figure=fig5)
        plt.pause(1)
    print(f"Damage 10 minutes: {joint1.result["D_t"]}")
