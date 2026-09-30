import numpy as np
from methods.sysid_functions.sysid import sysid
from methods.sysid_functions.plot_sysid import plot_stabilization_diagram
from methods.mode_clustering_functions.mode_clustering import (cluster_sysid_output, cluster_plots)
from methods.mode_tracking_functions.mode_tracking import (track_clusters,tracked_cluster_plots)
from methods.model_update_functions.model_update import (estimate_updated_model, model_update_plots)
from settings import PARAMS, MODEL_PARAMETERS

# This script runs function blocks directly from data files without a MQTT broker.
# Algorithm parameters are stored in settings.py
# .txt, .csv and .npy (as 2D array) files work for data input

FILEPATH = "record/play_back/beam/beam_data.npy"
DELIMETER = ","
SKIP_HEADER = False
SKIP_COLOUMNS = 0 #Skip coloumns up to X.
SAMPLES_DATASET = 2560 # Number of samples pr. dataset




# Script:
file_format = FILEPATH[-3:]
if (file_format == "txt") or (file_format == "csv"):
    data = np.genfromtxt(FILEPATH,dtype=np.float64,delimiter=DELIMETER,skip_header=SKIP_HEADER)
    data = data[:,SKIP_COLOUMNS:]
elif file_format == "npy":
    data = np.load(FILEPATH)
else:
    raise ValueError("File format not supported. .csv, .txt and .npy is allowed.")

n_sensors = data.shape[1]
datasets = int(np.floor(data.shape[0]/SAMPLES_DATASET))
print("Number of sensors:",n_sensors)
print("Length of data:",data.shape[0])
print("Datasets",data.shape[0]/SAMPLES_DATASET)

model_parameters = MODEL_PARAMETERS
fig_ax1 = None
fig_ax2 = (None,None,None)
fig_ax3 = (None,None)
fig_axes4 = (None,None)
tracked_clusters = {}
for ii in range(datasets):
    print(f"=== Running dataset {ii}/{datasets} ===")
    data_package = data[SAMPLES_DATASET*(ii):SAMPLES_DATASET*(1+ii),:]

    sysid_results = sysid(data_package,PARAMS)
    fig_ax1 = plot_stabilization_diagram(sysid_results,PARAMS,fig_ax=fig_ax1)

    clusters, median_frequencies = cluster_sysid_output(sysid_results,PARAMS)
    fig_ax2 = cluster_plots([0,0,1],clusters,sysid_results,PARAMS,fig_axes=fig_ax2)

    tracked_clusters = track_clusters(clusters,tracked_clusters,PARAMS)
    fig_ax3 = tracked_cluster_plots([0,1],tracked_clusters,clusters,sysid_results,PARAMS,fig_axes=fig_ax3)

    (updated_parameters, omega_model, model_parameters) = estimate_updated_model(clusters,model_parameters,PARAMS)
    if updated_parameters is not None:
        fig_axes4 = model_update_plots([1,1],model_parameters,PARAMS['pars_to_update'],omega_model,fig_axes=fig_axes4)
