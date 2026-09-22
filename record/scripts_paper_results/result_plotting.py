import os
from functions.results_plot import cantilever_beam_plots
from functions.fatigue_results import fatigue_plots

dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, 'data')
# cantilever_beam_plots(path=filename,all_at_once=True)
fatigue_plots(path=filename)
