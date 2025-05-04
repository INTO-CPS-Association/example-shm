# def function_save(FileName,functions_to_save,module):
#     import inspect
#     import ast

#     #%% Importing module (Switch to include e.g., jax or numpy)
#     if module == 'jax':
#         exec('import ' + module + '.numpy') 
#         module = module + '.numpy'
#     else:
#         exec('import ' + module) 

#     #%% Importing module
#     with open(FileName, "w") as file:
#         file.write('import ' + module + " \n\n")

#     #%% Extracting source code adding prefix (e.g., numpy.cos or jax.numpy.sin)
#     functions = {}
    
#     # Looping though each function
#     for name, func in functions_to_save.items():
#         Module_attribute = set()

#         # Obtaining the source code along with it's abtract syntax tree (ast)
#         source_code = inspect.getsource(func) 
#         tree = ast.parse(source_code) 

#         # Input parameters
#         input_params = list(inspect.signature(func).parameters.keys()) 

#         # Looping through the ast
#         for node in ast.walk(tree):
            
#             # Check if instance contain a "Name" e.g., "Name(id='x')" or "Name(id='cos')" AND check if "id" within said "Name" exists in the module
#             if isinstance(node, ast.Name) and node.id in dir(eval(module)): 
#                 if node.id in input_params: # Warning if input parameter(s) clash with detected attribute
#                     print('Warning! Input parameter {' + node.id +  '} share attribute with {' + module + '}. Ignoring prefix for {' + node.id + '}.')
#                 else:
#                     if module + '.' + node.id in source_code: # Case with repeated attributes
#                         continue
#                     else: 
#                         Module_attribute.add(node.id) # set of detected attributes
#                         source_code = source_code.replace(node.id, f'{module}.{node.id}') # Applying prefix to detected attributes

#         # Adding modified source_code with prefix and renaming the function
#         functions[name] = source_code
#         functions[name] = functions[name].replace('_lambdifygenerated', name)

#         #%% Adding function the file
#         with open(FileName, "a") as file:
#             file.write(functions[name] + '\n')

#         #%% Printing attribute(s) and function(s) for quick validation
#         print('------------------------------------------------------------------------------------------')
#         print('Detected attributes: ' + str(Module_attribute))
#         print(' ')
#         print(functions[name])


def function_save(FileName, functions_to_save, module):
    import inspect
    import ast
    import importlib

    #%% Importing module (Switch to include e.g., jax or numpy)
    if module == "jax":
        module = "jax.numpy"
    # Import the module dynamically
    try:
        mod = importlib.import_module(module)
    except ImportError:
        print(f"Error: Module '{module}' could not be imported.")
        return

    # Write module import statement at the beginning of the file
    with open(FileName, "w") as file:
        file.write(f"import {module}\n\n")

    #%% Extracting source code adding prefix (e.g., numpy.cos or jax.numpy.sin)
    functions = {}

    # Looping though each function
    for name, func in functions_to_save.items():
        Module_attribute = set()

        # Obtaining the source code along with it's abtract syntax tree (ast)
        source_code = inspect.getsource(func) 
        tree = ast.parse(source_code) 
        input_params = list(inspect.signature(func).parameters.keys())

        # Walk through the AST to detect module attributes
        for node in ast.walk(tree):
            # Check if instance contain a "Name" e.g., "Name(id='x')" or "Name(id='cos')" AND check if "id" within said "Name" exists in the module
            if isinstance(node, ast.Name) and hasattr(node, "id") and node.id in dir(mod):
                if node.id in input_params:  # Avoid prefixing input parameters
                    print(f"Warning! Input parameter '{node.id}' conflicts with '{module}'. Ignoring prefix.")
                elif f"{module}.{node.id}" not in source_code:  # Avoid duplicate prefixing
                    Module_attribute.add(node.id)
                    source_code = source_code.replace(node.id, f"{module}.{node.id}")

        # Store modified function source and rename it
        functions[name] = source_code.replace('_lambdifygenerated', name)

        # Append modified function to the file
        with open(FileName, "a") as file:
            file.write(functions[name] + "\n")

        # Print detected attributes and final function source for debugging
        print('-' * 90)
        print(f"Detected attributes in function '{name}': {Module_attribute}\n")
        print(functions[name])
