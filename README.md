# gs2utils
Useful scripts for working with the gyrokinetic code GS2. 
## Installation

### Cloning the project
To clone the project, run the following command:
```
  git clone https://github.com/baiway/gs2utils.git
  cd gs2utils
```

### Setting up
You probably want to create a virtual environment before installing dependencies:
```
  virtualenv .venv
  source .venv/bin/activate
```
Then install the dependencies:
```
  pip install -r requirements.txt
```
Consider changing the default GS2 executable in `write-slurm-viking.py`. Also ensure the project account and email address are correctly set. 

### Generating submission scripts
To write a submission script `job.slurm` for a GS2 input file `input.in` in the directory `path/to/run_dir`, run the following command:
```
  python write-slurm-viking.py path/to/run_dir
```
The path can be a relative or absolute path. For additional information, run `pythin write-slurm-viking.py --help`.
The run can then be submitted for scheduling using
```
  sbatch path/to/job.slurm
```
