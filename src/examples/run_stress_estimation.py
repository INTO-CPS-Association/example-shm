from methods.virtual_sensing import virtual_sensing
from methods.stress_estimation import stress_estimation_for_beam

def run_stress_and_strain_estimation(config_path):
    number_of_minutes = 0.2
    displacement, _ = virtual_sensing(config_path, number_of_minutes)
    stress, strain = stress_estimation_for_beam(displacement)
    print("Max stress",max(stress[3,1]),"MPa. Min stress",min(stress[3,1]),"MPa")
