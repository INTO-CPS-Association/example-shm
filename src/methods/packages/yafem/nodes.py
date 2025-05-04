import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
import matplotlib.patches as patches

class nodes:
#%% object constructor
    def __init__(self, pars):

        # extract parameters and assign default values
        self.extract_pars(pars)

        if self.nodal_coords.shape[0] == 1:
            self.model_size = 1
        else:    
            self.model_size = np.max(sp.spatial.distance.pdist(self.nodal_coords, 'euclidean'))
        
        # compute model center
        self.model_center = np.mean(self.nodal_coords,axis=0)

#%% extract nodal coordinates
    def find_coords(self, nodal_labels_sel):
        nodal_labels_sel = np.array(nodal_labels_sel).flatten()
        
        # Get the indices of each label in nodal_labels_sel
        indices = np.argsort(self.nodal_labels)
        sorted_labels = np.searchsorted(self.nodal_labels[indices], nodal_labels_sel)
        row_indices = indices[sorted_labels]

        # Extract the corresponding coordinates
        nodal_coords_subset = self.nodal_coords[row_indices]
        
        return nodal_coords_subset

#%% extract parameters and assign default values
    def extract_pars(self,pars):
        
        # storage of input for packing/unpacking
        self.my_pars = pars

        if 'nodal_data' in pars:

            # purging repeated nodal data
            pars['nodal_data'] = np.unique(pars['nodal_data'], axis=0)

            # checking for inconsistency in repeated nodal data
            check_labels = np.unique(pars['nodal_data'][:,0], axis=0,return_index=True,return_counts=True)
            check_coords = np.unique(pars['nodal_data'][:,1:], axis=0,return_index=True,return_counts=True)

            # number of inconsistent repeated labels and coords
            repeated_labels = check_labels[1][check_labels[2]>1]
            repeated_coords = check_coords[1][check_coords[2]>1]

            if (len(repeated_labels) != 0) or (len(repeated_coords) != 0):

                # Obtaining labels with repeated inconsistencies
                cases = pars['nodal_data'][repeated_coords,1:]
                cases_set = set(map(tuple, cases)) # Conversion to set for faster loop in list comprehension
                idx_bool = [tuple(i) in cases_set for i in pars['nodal_data'][:,1:]]
                labels_for_repeated_coords = pars['nodal_data'][idx_bool,0]
                labels_for_repeated_labels = pars['nodal_data'][repeated_labels,0]

                # if either inconsistent repeated labels or repeated coords
                if (len(repeated_labels) != 0) != (len(repeated_coords) != 0):
                   
                    if (len(repeated_labels) != 0) == True:
                        raise Exception("Warning! Repeated nodal label(s): " + str(set(map(int, labels_for_repeated_labels))))
                    
                    elif (len(repeated_coords) != 0) == True:
                        raise Exception("Warning! Repeated nodal coordinates at label: " + str(set(map(int, labels_for_repeated_coords))))
     
                else: # if both inconsistent repeated labels and coords
                    raise Exception("Warning! Inconsistent repeated nodal label(s): " + str(set(map(int, labels_for_repeated_labels))) + 
                                      " and repeated nodal coordinates at label(s): " + str(set(map(int, labels_for_repeated_coords))))

            # extract nodal labels into 1d array
            self.nodal_labels = pars['nodal_data'][:,0].squeeze().astype(np.int32)
            
            # extract nodal coordinates into 2d array
            self.nodal_coords = pars['nodal_data'][:,1:].astype(np.float64)
            
        else:
            self.nodal_labels = np.array([1],dtype=np.int32)
            self.nodal_coords = np.array([[0.0,0.0,0.0]],dtype=np.float64)

        # here we set the missing dimensions to zero so that we can plot the nodes in 3D
        if self.nodal_coords.shape[1] < 3:
            self.nodal_coords = np.hstack((self.nodal_coords,np.zeros((self.nodal_coords.shape[0],3-self.nodal_coords.shape[1]),dtype=np.float64)))

#%% plot the nodes
    def plot(self, labels=True, rotate=(30,30), figsize=8, zoom=1.0, axis='on'):

        # Extracting data from the object
        nodal_coords = self.nodal_coords
        nodal_labels = self.nodal_labels
        model_center = self.model_center
        model_size   = self.model_size

        # Calculate initial limits
        xlim = [model_center[0] - model_size, model_center[0] + model_size]
        ylim = [model_center[1] - model_size, model_center[1] + model_size]
        zlim = [model_center[2] - model_size, model_center[2] + model_size]

        # Apply zoom factor
        x_range = xlim[1] - xlim[0]
        y_range = ylim[1] - ylim[0]
        z_range = zlim[1] - zlim[0]

        # Apply zoom
        zoom_factor = 1/zoom
        x_range_zoomed = x_range * zoom_factor
        y_range_zoomed = y_range * zoom_factor
        z_range_zoomed = z_range * zoom_factor

        # Create a 3D plot
        fig = plt.figure(figsize=(figsize, figsize))  # Adjust the size as needed       
        ax  = fig.add_subplot(111, projection='3d')

        # Switch for axis
        plt.axis(axis)
        
        # Plotting nodes
        ax.scatter(nodal_coords[:, 0], nodal_coords[:, 1], nodal_coords[:, 2], c='k', marker='.', depthshade=False)

        # Center the axes at the model center with zoom applied
        ax.set_xlim([model_center[0] - x_range_zoomed * 0.5, model_center[0] + x_range_zoomed * 0.5])
        ax.set_ylim([model_center[1] - y_range_zoomed * 0.5, model_center[1] + y_range_zoomed * 0.5])
        ax.set_zlim([model_center[2] - z_range_zoomed * 0.5, model_center[2] + z_range_zoomed * 0.5])

        # Setting labels
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_zlabel('z')

        ax.view_init(elev=rotate[0], azim=rotate[1])  # Adjust these values as needed

         # Plot nodal numbers if labels are enabled
        if labels == True and type(labels) == bool or type(labels) == int or type(labels) == float:
            # Setting fontsize
            if labels == True and type(labels) == bool:
                fontsize = 12
            else:
                fontsize = labels
         
            for i in range(len(nodal_coords)):
                x, y, z = nodal_coords[i]
                label = nodal_labels[i]  # Adjust for 1D array
                ax.text(x, y, z,str(label), fontsize=fontsize, fontweight='bold')

                # if nodal_labels[i] >= 42 and nodal_labels[i] <= 46:
                #     x, y, z = nodal_coords[i]
                #     label = nodal_labels[i]  # Adjust for 1D array
                #     ax.plot(nodal_coords[i, 0], nodal_coords[i, 1], nodal_coords[i, 2], c='r', marker='.',markersize=20)
                #     ax.text(x, y, z,str(label), fontsize=fontsize, fontweight='bold')

        return ax
        
    def dump_to_paraview(self):
        pass
