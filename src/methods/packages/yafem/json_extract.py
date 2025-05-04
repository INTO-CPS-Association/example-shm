import json
import numpy as np

#%%
def to_json(model,name):

    # Function to convert np.array to list
    def convert_np_arrays(obj):
        if isinstance(obj, dict):
            return {k: convert_np_arrays(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_np_arrays(i) for i in obj]
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj

    # Convert np.array objects to lists
    model_serialized = convert_np_arrays(model)

    # Save the cantilever_beam_model to a JSON file
    with open(name + '.json', 'w') as fid:
        json.dump(model_serialized, fid)

#%%

def load_json(json_file):

    # Load the cantilever_beam_model from the JSON file
    with open(json_file, 'r') as fid:
        model = json.load(fid)

    # Convert lists to numpy arrays in the nested dictionaries
    for pars in model.keys():
        if isinstance(model[pars], list) and len(model[pars]) > 0 and isinstance(model[pars][0], dict):
            # Handle list of dictionaries
            for item in model[pars]:
                for key, value in item.items():
                    if isinstance(value, list):
                        item[key] = np.array(value)
        elif isinstance(model[pars], dict):
            # Handle dictionary
            for key, value in model[pars].items():
                if isinstance(value, list):
                    model[pars][key] = np.array(value)
    
    return model