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

echo '3...'
# create folder to place tracking results for this method
mkdir -p MOT16_eval/TrackEval/data/MOT16-train/$exp_name/data/

# inference on 4 MOT16 video sequences at the same time
# suits a 4GB GRAM GPU, feel free to increase if you have more memory
N=1

# generate tracking results for each sequence
echo 'Generating tracking results for each sequence...'
 for i in MOT16-02 MOT16-04 MOT16-05 MOT16-09 MOT16-10 MOT16-11 MOT16-13
 do
 	(
 		# change name to inference source so that each thread write to its own .txt file
 		if [ ! -d ~/datasets/MOT/MOT16/train/$i/$i ]
 		then
 			mv ~/datasets/MOT/MOT16/train/$i/img1/ ~/datasets/MOT/MOT16/train/$i/$i
 		fi
 		# run inference on sequence frames
 		python3 track.py --name $exp_name --conf-thres 0.3 --imgsz 1280 --aspect-ratio 0.8 --source ~/datasets/MOT/MOT16/train/$i/$i --save-txt --yolo_model ~/.cache/torch/checkpoints/crowdhuman_yolov5m.pt --deep_sort_model ~/.cache/torch/checkpoints/osnet_x0_25_msmt17.pth --classes 0 --exist-ok --device $CUDA_VISIBLE_DEVICES
 	    # move generated results to evaluation repo
 	) &
 	# https://unix.stackexchange.com/questions/103920/parallelize-a-bash-for-loop
 	# allow to execute up to $N jobs in parallel
     if [[ $(jobs -r -p | wc -l) -ge $N ]]
 	then
         # now there are $N jobs already running, so wait here for any job
         # to be finished so there is a place to start next one.
         wait
     fi
 done

# no more jobs to be started but wait for pending jobs
# (all need to be finished)
wait
echo "Inference on all MOT16 sequences DONE"

echo "Moving data from experiment folder to MOT16"
mv runs/track/$exp_name/tracks_txt/* \
   MOT16_eval/TrackEval/data/MOT16-train/$exp_name/data/

# run the evaluation
python MOT16_eval/TrackEval/scripts/run_mot_challenge.py --BENCHMARK MOT16 \
  --TRACKERS_TO_EVAL $exp_name --SPLIT_TO_EVAL train --METRICS CLEAR Identity \
  --USE_PARALLEL False --NUM_PARALLEL_CORES 4 --GT_FOLDER ~/datasets/MOT/data/gt/mot_challenge/ \
  --TRACKERS_FOLDER MOT16_eval/TrackEval/data/
