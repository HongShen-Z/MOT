#!/bin/bash
#BSUB -J eval
#BSUB -o %J.out
#BSUB -e %J.err
#BSUB -q gpu_v100
#BSUB -gpu "num=1:mode=exclusive_process:aff=yes"

module load anaconda3
source activate
conda deactivate
conda activate torch1.10
echo '1...'
set +e
echo '2...'
exp_name='deepsort-0.3'


mkdir -p MOT16_eval/TrackEval/data/MOT16-train/$exp_name/data/
echo '3...'