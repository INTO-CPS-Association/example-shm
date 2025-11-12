def check_mode_shapes(cluster_dict,dofs=None):
    print("Check mode shapes")

    for key in cluster_dict.keys():
        cluster = cluster_dict[key]
        print("\nCluster",key,cluster['median_f'])
        mode_shape = cluster['mode_shapes'][0]
        print("Mode shape")
        if dofs is not None:
            for ii, dof in enumerate(dofs):
                print(dof,mode_shape[ii])
        else:
            print(mode_shape)
        print('Press enter to continue')
        x = input()
    print("Mode shape check done")
