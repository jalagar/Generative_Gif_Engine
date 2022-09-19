from step1_layers_to_spritesheet.build import main as step1_main
from step3_generative_sheet_to_output.build import main as step3_main
import subprocess
from utils.file import parse_global_config
import multiprocessing
import time

global_config_json = parse_global_config()
num_total_frames = global_config_json["numberOfFrames"]
use_batching = global_config_json["useBatches"]
num_frames_per_batch = global_config_json["numFramesPerBatch"] if use_batching else num_total_frames
total_supply = global_config_json["totalSupply"]
use_multiprocessing = global_config_json["useMultiprocessing"]
processor_count = global_config_json["processorCount"]
start_index = global_config_json["startIndex"]
height = global_config_json["height"]
width = global_config_json["width"]


def create_from_dna(edition):
    subprocess.run(
        f"cd step2_spritesheet_to_generative_sheet && npm run create_from_dna {edition}",
        shell=True,
    )


def create_all_from_dna():
    if use_multiprocessing:
        if processor_count > multiprocessing.cpu_count():
            raise Exception(
                f"You are trying to use too many processors, you passed in {processor_count} "
                f"but your computer can only handle {multiprocessing.cpu_count()}. Change this value and run make step3 again."
            )

        args = [
            (edition,) for edition in range(start_index, start_index + total_supply)
        ]
        with multiprocessing.Pool(processor_count) as pool:
            pool.starmap(
                create_from_dna,
                args,
            )
    else:
        # Then recreate DNA from the editions
        for edition in range(start_index, start_index + total_supply):
            create_from_dna(edition)


def main():
    start_time = time.time()

    # run step 1 with one pixel dimensions to speed up JSON processing and generate hashes
    step1_main(0, height=1, width=1)
    subprocess.run(
        f"cd step2_spritesheet_to_generative_sheet && npm run generate 10 10 && cd ..",
        shell=True,
    )
    for i in range(num_total_frames // num_frames_per_batch):
        print(f"*******Starting Batch {i}*******")
        step1_main(i)
        create_all_from_dna()
        # Only generate gif if its the last batch
        step3_main(
            i,
            should_generate_output=i == (num_total_frames // num_frames_per_batch - 1),
        )
    print("--- %s seconds ---" % (time.time() - start_time))


if __name__ == "__main__":
    main()
