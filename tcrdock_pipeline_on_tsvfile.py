
'''

Provides a nicer interface to run the TCRdock pipeline on a TSV file containing the input data.
Also provides nice interface with slurm.

'''

import os
import argparse


SLURM_SETUP = "#!/bin/bash\n\
#SBATCH --job-name={system_identifier}__tcrdock\n\
#SBATCH --account={account}\n\
#SBATCH --partition={partition}\n{gpu_text}\
#SBATCH --nodes=1\n\
#SBATCH --ntasks-per-node={num_cores}\n\
#SBATCH --time={walltime}\n\
#SBATCH --mem={memory}\n{email_text}\
#SBATCH -e {errfile}\n\
#SBATCH -o {outfile}"


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i',  '--tcrdock_input_tsv_file', type=str, required=True)
    parser.add_argument('-o',  '--output_dir_for_pdbs', type=str, required=True)
    parser.add_argument('-o2', '--output_dir_for_pae_file', type=str, default=None, help='Defaults to the output_dir_for_pdbs')
    parser.add_argument('-A',  '--account', type=str, default='spe')
    parser.add_argument('-P',  '--partition', type=str, default='gpu-a40')
    parser.add_argument('-G',  '--use_gpu', type=int, default=1, choices=[0, 1])
    parser.add_argument('-C',  '--num_cores', type=int, default=1)
    parser.add_argument('-W',  '--walltime', type=str, default='16:00:00')
    parser.add_argument('-M',  '--memory', type=str, default='96G')
    parser.add_argument('-E',  '--send_emails', type=int, default=1, choices=[0, 1])
    parser.add_argument('-EA', '--email_address', type=str, default=None)
    parser.add_argument('-T',  '--tcrdock_path', type=str, default='/gscratch/spe/gvisan01/TCRdock-copy/')
    args = parser.parse_args()

    if args.output_dir_for_pae_file is None:
        args.output_dir_for_pae_file = args.output_dir_for_pdbs
    
    os.makedirs(args.output_dir_for_pdbs, exist_ok=True)
    os.makedirs(args.output_dir_for_pae_file, exist_ok=True)
    logs_path = os.path.join(args.tcrdock_path, 'slurm_logs')
    os.makedirs(logs_path, exist_ok=True)
    
    if args.use_gpu:
        gpu_text = '#SBATCH --gres=gpu:1\n'
    else:
        gpu_text = ''
    
    if args.send_emails:
        email_text = f'#SBATCH --mail-type=ALL\n#SBATCH --mail-user={args.email_address}\n#SBATCH --export=all\n'
    else:
        email_text = ''

    # get basename of the input file
    system_identifier = os.path.splitext(os.path.basename(args.tcrdock_input_tsv_file))[0]

    command_setup = f"python {os.path.join(args.tcrdock_path, 'setup_for_alphafold.py')} \
                                --targets_tsvfile {args.tcrdock_input_tsv_file} \
                                --output_dir {args.output_dir_for_pdbs} \
                                --new_docking"

    command_run = f"python -u {os.path.join(args.tcrdock_path, 'run_prediction.py')} \
                                --verbose \
                                --targets {os.path.join(args.output_dir_for_pdbs, 'targets.tsv')} \
                                --outfile_prefix {os.path.join(args.output_dir_for_pdbs, system_identifier)} \
                                --model_names model_2_ptm_ft4 \
                                --data_dir {os.path.join(args.tcrdock_path, 'alphafold_params/')} \
                                --model_params_files {os.path.join(args.tcrdock_path, 'alphafold_params/params/tcrpmhc_run4_af_mhc_params_891.pkl')}"

    command_pae = f"python {os.path.join(args.tcrdock_path, 'add_pmhc_tcr_pae_to_tsvfile.py')} \
                                --infile {os.path.join(args.output_dir_for_pdbs, system_identifier + '_final.tsv')} \
                                --outfile {os.path.join(args.output_dir_for_pae_file, system_identifier + '_w_pae.tsv')}\
                                --clobber"

    slurm_text = SLURM_SETUP.format(system_identifier=system_identifier,
                                    account=args.account,
                                    partition=args.partition,
                                    gpu_text=gpu_text,
                                    num_cores=args.num_cores,
                                    walltime=args.walltime,
                                    memory=args.memory,
                                    email_text=email_text,
                                    errfile=os.path.join(logs_path, f"{system_identifier}.err"),
                                    outfile=os.path.join(logs_path, f"{system_identifier}.out"))
    
    slurm_text += '\n\n' + command_setup + '\n\n' + command_run + '\n\n' + command_pae

    slurm_file = 'job.slurm'
    with open(slurm_file, 'w') as f:
        f.write(slurm_text)

    os.system(f"sbatch {slurm_file}")

