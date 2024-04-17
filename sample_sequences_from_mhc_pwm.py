

import os, sys
import numpy as np
import pandas as pd

from protein_holography_pytorch.utils.protein_naming import ol_to_ind_size, ind_to_ol_size


if __name__ == '__main__':

    mhc_sequences_file = '/gscratch/spe/gvisan01/peptide_mhc/mhc_motif_atlas/data_classI_all_peptides.txt'

    with open(mhc_sequences_file, 'r') as f:
        A0201_9mer_started = False
        A0201_9mer_done = False
        sequences = []
        for line in f:
            allele, peptide = line.strip().split()
            if allele == 'A0201' and len(peptide) == 9:
                A0201_9mer_started = True
            
            if A0201_9mer_started:
                if allele != 'A0201' or len(peptide) != 9:
                    A0201_9mer_done = True
                    break
                else:
                    sequences.append(peptide)
    
    print(len(sequences))
    
    # make PWM
    pwm = np.zeros((9, 20))
    for seq in sequences:
        for i, aa in enumerate(seq):
            pwm[i, ol_to_ind_size[aa]] += 1
    pwm = pwm / np.sum(pwm, axis=1)[:, np.newaxis]

    samples = []
    for i in range(9):
        sampled_indices = np.random.multinomial(1, pwm[i, :], size=200)
        characters = [ind_to_ol_size[np.argmax(sample)] for sample in sampled_indices]
        samples.append(characters)
    sequences = list(zip(*samples))
    sequences = [''.join(seq) for seq in sequences]

    ## sanity check: compute pwn with sampled sequences make sure it's similar enough to the original pwm
    pwm_2 = np.zeros((9, 20))
    for seq in sequences:
        for i, aa in enumerate(seq):
            pwm_2[i, ol_to_ind_size[aa]] += 1
    pwm_2 = pwm_2 / np.sum(pwm_2, axis=1)[:, np.newaxis]
    
    print(pwm[1, :])
    print(pwm_2[1, :])

    ## now put these sequences in a tsv file for tcrdock to use
    header = 'organism	mhc_class	mhc	peptide	va	ja	cdr3a	vb	jb	cdr3b	pdbid	hcnn_model	-log10(Kd)	hamming_distance_from_WT	hcnn_pnE	pnE'
    template_row = 'human	1	A*02:01	{seq}	TRAV21*01	TRAJ6*01	CAVRPTSGGSYIPTF	TRBV6-5*01	TRBJ2-2*01	CASSYVGNTGELFF	from_kd_data	from_kd_data	-0.69284691927723	1	inf	'
    
    with open('sample_sequences_from_mhc_pwm.tsv', 'w+') as f:
        f.write(header + '\n')
        for seq in sequences:
            f.write(template_row.format(seq=seq) + '\n')

    ## test the tsv file is read successfully
    df = pd.read_csv('sample_sequences_from_mhc_pwm.tsv', sep='\t')
    print(df.head())


