import argparse
import textwrap
from pathlib import Path
import f90nml


def mkdir(dir):
    """Make a directory if it does not exist"""
    if not dir.exists():
        dir.mkdir()


def get_input_filepath(run_dir):
    """Return the path to an input file ending with `.in` in a directory
    if it exists; if not, return None."""
    for file in run_dir.iterdir():
        if file.suffix == ".in":
            return file
    return None


def read_from_nml(nml, param, input_file):
    """Reads and returns the value of `param` from a Fortran namelist
    `input_file`"""
    try:
        f = f90nml.read(input_file)
        value = f[nml][param]
        return value
    except KeyError:
        print(f"Error: '{param}' in namelist '{nml}' not found in '{input_file}'")


def format_time(time):
    """Formats a time interval given in seconds into `DD-HH:MM:SS` format."""
    days, remainder = divmod(time, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    return f"{days:02d}-{hours:02d}:{minutes:02d}:{seconds:02d}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generates Slurm submission scripts for use on Viking2."
    )
    parser.add_argument(
        "run_dir", type=str, help="Path to run directory (relative or absolute)."
    )
    parser.add_argument(
            "--job-name", type=str, help="Slurm job name. Defaults to basename of 'run_dir'."
    )
    parser.add_argument(
        "-n", "--nprocs", type=int, default=1, help="Number of processors to request. Defaults to 1 (serial)."
    )
    parser.add_argument(
        "--mem-per-cpu", type=int, default=5200, help="Memory per cpu to request (in megabytes). Defaults to 5.2 GB."
    )
    parser.add_argument(
        "--gs2-exec", type=str, default="/users/bc1264/scratch/gs2-transfer/bin/gs2", help="Path to GS2 executable."
    )
    # TODO add reminder to run `ingen`

    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    job_name = args.job_name if args.job_name else run_dir.stem
    nprocs = args.nprocs
    mem_per_cpu = args.mem_per_cpu
    GS2_exec = Path(args.gs2_exec)


    if not run_dir.is_dir():
        raise ValueError(f"Directory does not exist: {run_dir}")

    if not GS2_exec.is_file():
        raise ValueError(f"GS2 executable does not exist: {GS2_exec}")

    input_filepath = get_input_filepath(run_dir)
    if input_filepath is None:
        raise FileNotFoundError(f"No input file (.in) found in {run_dir}")

    mkdir(run_dir / "restart_dir")

    avail_cpu_time = read_from_nml("knobs", "avail_cpu_time", input_filepath)
    margin_cpu_time = read_from_nml("knobs", "margin_cpu_time", input_filepath)
    requested_time = avail_cpu_time + margin_cpu_time
    formatted_time = format_time(requested_time)

    if requested_time > 172800:  # 48 hours = 172800 seconds
        raise ValueError(f"Invalid requested time: {formatted_time}. \n Must be < 48 h.")

    script_content = textwrap.dedent(f"""
        #!/usr/bin/env bash
        #SBATCH --job-name={job_name}
        #SBATCH --partition=nodes
        #SBATCH --time={formatted_time}
        #SBATCH --ntasks={nprocs}
        #SBATCH --cpus-per-task=1
        #SBATCH --mem-per-cpu={mem_per_cpu}
        #SBATCH --account=pet-gspt-2019
        #SBATCH --mail-type=END,FAIL
        #SBATCH --mail-user=bc1264@york.ac.uk
        #SBATCH --output=%x-%j.log
        #SBATCH --error=%x-%j.err

        # Abort if any command fails
        set -e

        # Load required modules
        module purge
        module load gompi/2022b OpenMPI/4.1.4-GCC-12.2.0     # requirements
        module load netCDF-Fortran/4.6.0-gompi-2022          # netCDF
        module load FFTW/3.3.10-GCC-12.2.0                   # FFTW
        module load OpenBLAS/0.3.21-GCC-12.2.0               # Lapack/BLAS
        module load Python/3.10.8-GCCcore-12.2.0             # testing

        # Set GS2 executable, input file and screen output
        GS2_exec="{GS2_exec}"
        input_file="{input_filepath}"
        screen_output="screen_output.txt"

        # Run command
        srun ${{GS2_exec}} ${{run_dir}}/${{input_filepath}} | tee ${{run_dir}}/$screen_output
    """)
    
    with open(run_dir / "job.slurm", "w") as f:
        f.write(script_content)

    print(f"Submission script generated here: {run_dir.resolve()}/job.slurm")

    ingen_exec = GS2_exec.parent / 'ingen'
    print("Remember to run 'ingen' to check for sweetspots! Here's the command: ")
    print(f"  {ingen_exec} {input_filepath.resolve()}")
