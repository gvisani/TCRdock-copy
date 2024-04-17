

import os, sys

PARAMS_URLS = ['https://www.dropbox.com/s/e3uz9mwxkmmv35z/params_model_2_ptm.npz',
               'https://www.dropbox.com/s/jph8v1mfni1q4y8/tcrpmhc_run4_af_mhc_params_891.pkl']

PARAMS_DIR = './alphafold_params/params'


os.makedirs(PARAMS_DIR, exist_ok=True)

for URL in PARAMS_URLS:
    PARAMS_PATH = os.path.join(PARAMS_DIR, os.path.basename(URL))
    os.system(f'wget -O "{PARAMS_PATH}" "{URL}"')

