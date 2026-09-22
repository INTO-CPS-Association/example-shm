Code to replicate results in the paper "A digital twin platform for structural health monitoring" [1].
The python version should be 3.11 and the pyOMA-2 (v.1.1.2) folder should be placed in the enviroment folder "venv\Lib\site-packages". This contains sufficient changes to pyOMA-2 version 1.1.2. (Beware this version of pyOMA-2 calculates the standard deviation of the damping ratio wrong)
The data behind the results is created by running Cantileverbeam_full.py.
By un-commenting line 14-16, the plots from the paper will be shown.

At first the scripts estimates the length l4 of the beam. Afterwards the model update estimates the rotational stiffness of the constraint and the top mass.

## Background
The beam is a cantilever beam (steel ruler) with 4 accelerometers [1][2]. The beam is fixed vertically to a table, and a turning fan is pushing air onto the beam exciting it. The experiment consist of two differet mass perturbations at 10 grams and 20 grams at the tip. These perturbations appears 1 hour and 2 hours in.
The beam have a length of 530mm and is fixtated at 58.9mm and 128.9mm, the accelemerometers is placed at 297.5mm, 365mm, 432.5mm,  500mm. [2]

## Technical information
The JSONL data file is to be used with the structural health monitoring python package [2]
Sample frequency: 256 Hz
Data type: float
Samples pr. message: 16.

[1] "A digital twin platform for structural health monitoring"
Prasad Talasila, Dmitri Tcherniak, Anders M.D. Jensen, Swarup Mahato, Jakob V. Medom, Martin D. Ulriksen, Giuseppe Abbiati, A. Schörghofer-Queiroz, Peter G. Larsen, Lars Damkilde
Computer-Aided Civil and Infrastructure Engineering, 2026
https://doi.org/10.1016/j.cacaie.2026.100086
