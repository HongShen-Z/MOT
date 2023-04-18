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
# exp_name='cd_v5m_osnet_x0_25'

# # clone evaluation repo if it does not exist
# if [ ! -d MOT16_eval/TrackEval ]
# then
# 	echo 'Cloning official MOT16 evaluation repo'
# 	git clone https://github.com/JonathonLuiten/TrackEval TrackEval
# 	# download quick start data folder if it does not exist
# 	if [ ! -d ~/datasets/MOT/data ]
# 	then
# 		# download data
# 		echo 'Downloading TrackEval data...'
# 		wget -nc https://omnomnom.vision.rwth-aachen.de/data/TrackEval/data.zip -O ~/datasets/MOT/data.zip
# 		# unzip
# 		unzip -q ~/datasets/MOT/data.zip
# 		echo 'Done.'
# 		# delete zip
# 		rm ~/datasets/MOT/data.zip
# 	fi
# fi
#
#
# # if MOT16 data not unziped, then download, unzip and lastly remove zip MOT16 data
# if [[ ! -d ~/datasets/MOT/MOT16/train ]] && [[ ! -d ~/datasets/MOT/MOT16/test ]]
# then
# 	# download data
# 	echo 'Downloading MOT16 data...'
# 	wget -nc https://motchallenge.net/data/MOT16.zip -O ~/datasets/MOT/MOT16.zip
# 	# unzip
#     unzip -q ~/datasets/MOT/MOT16.zip
#     echo 'Done.'
# 	# delete zip
# 	rm ~/datasets/MOT/MOT16.zip
# fi

echo '3...'
# create folder to place tracking results for this method
mkdir -p MOT16_eval/TrackEval/data/MOT16-train/$exp_name/data/

# inference on 4 MOT16 video sequences at the same time
# suits a 4GB GRAM GPU, feel free to increase if you have more memory
N=4

# generate tracking results for each sequence
echo 'Generating tracking results for each sequence...'

# function to process a sequence
function process_sequence() {
    # change name to inference source so that each process write to its own .txt file
    if [ ! -d "~/datasets/MOT/MOT16/train/$1/$1" ]; then
        mv "~/datasets/MOT/MOT16/train/$1/img1" "~/datasets/MOT/MOT16/train/$1/$1"
    fi
    # run inference on sequence frames
    python3 track.py --name $exp_name --conf-thres 0.3 --imgsz 1280 --aspect-ratio 0.8 --source ~/datasets/MOT/MOT16/train/$i/$i --save-txt --yolo_model ~/.cache/torch/checkpoints/crowdhuman_yolov5m.pt --deep_sort_model ~/.cache/torch/checkpoints/osnet_x0_25_msmt17.pth --classes 0 --exist-ok --device $CUDA_VISIBLE_DEVICES
}

# list of sequences to process
sequences=("MOT16-02" "MOT16-04" "MOT16-05" "MOT16-09" "MOT16-10" "MOT16-11" "MOT16-13")
# create a lock file
lock_file=~/tmp/mylockfile.lock
exec 200>$lock_file

# loop over sequences and start processes
for sequence in "${sequences[@]}"; do
    # acquire lock
    flock -n 200 || { echo "could not acquire lock"; exit 1; }

    # start process in background
    process_sequence "$sequence" &

    # wait for any process to complete before starting the next one
    while read -u 200 -t 1 && [[ $? -eq 0 ]]; do
        :
    done
done

# wait for all processes to complete
wait
#
# for i in MOT16-02 MOT16-04 MOT16-05 MOT16-09 MOT16-10 MOT16-11 MOT16-13
# do
# 	(
# 		# change name to inference source so that each thread write to its own .txt file
# 		if [ ! -d ~/datasets/MOT/MOT16/train/$i/$i ]
# 		then
# 			mv ~/datasets/MOT/MOT16/train/$i/img1/ ~/datasets/MOT/MOT16/train/$i/$i
# 		fi
# 		# run inference on sequence frames
# 		python3 track.py --name $exp_name --conf-thres 0.3 --imgsz 1280 --aspect-ratio 0.8 --source ~/datasets/MOT/MOT16/train/$i/$i --save-txt --yolo_model ~/.cache/torch/checkpoints/crowdhuman_yolov5m.pt --deep_sort_model ~/.cache/torch/checkpoints/osnet_x0_25_msmt17.pth --classes 0 --exist-ok --device $CUDA_VISIBLE_DEVICES
# 	    # move generated results to evaluation repo
# 	) &
# 	# https://unix.stackexchange.com/questions/103920/parallelize-a-bash-for-loop
# 	# allow to execute up to $N jobs in parallel
#     if [[ $(jobs -r -p | wc -l) -ge $N ]]
# 	then
#         # now there are $N jobs already running, so wait here for any job
#         # to be finished so there is a place to start next one.
#         wait
#     fi
# done

#for i in MOT16-01 MOT16-03 MOT16-06 MOT16-07 MOT16-08 MOT16-12 MOT16-14
#do
#	(
#		# change name to inference source so that each thread write to its own .txt file
#		if [ ! -d ~/datasets/MOT/MOT16/test/$i/$i ]
#		then
#			mv ~/datasets/MOT/MOT16/test/$i/img1/ ~/datasets/MOT/MOT16/test/$i/$i
#		fi
#		# run inference on sequence frames
#		python3 track.py --name $exp_name --conf-thres 0.2 --imgsz 1280 --aspect-ratio 0.8 --source ~/datasets/MOT/MOT16/test/$i/$i --save-txt --save-vid --yolo_model ~/.cache/torch/checkpoints/crowdhuman_yolov5m.pt --deep_sort_model ~/.cache/torch/checkpoints/osnet_x0_25_msmt17.pth --classes 0 --exist-ok --device $CUDA_VISIBLE_DEVICES
#	    # move generated results to evaluation repo
#	) &
#	# https://unix.stackexchange.com/questions/103920/parallelize-a-bash-for-loop
#	# allow to execute up to $N jobs in parallel
#    if [[ $(jobs -r -p | wc -l) -ge $N ]]
#	then
#        # now there are $N jobs already running, so wait here for any job
#        # to be finished so there is a place to start next one.
#        wait
#    fi
#done

# no more jobs to be started but wait for pending jobs
# (all need to be finished)
#wait
echo "Inference on all MOT16 sequences DONE"

# echo "Moving data from experiment folder to MOT16"
# mv runs/track/$exp_name/tracks_txt/* \
#    MOT16_eval/TrackEval/data/MOT16-train/$exp_name/data/
#
# # run the evaluation
# python MOT16_eval/TrackEval/scripts/run_mot_challenge.py --BENCHMARK MOT16 \
#  --TRACKERS_TO_EVAL $exp_name --SPLIT_TO_EVAL train --METRICS CLEAR Identity \
#  --USE_PARALLEL False --NUM_PARALLEL_CORES 7 --GT_FOLDER ~/datasets/MOT/data/gt/mot_challenge/ \
#  --TRACKERS_FOLDER MOT16_eval/TrackEval/data/
