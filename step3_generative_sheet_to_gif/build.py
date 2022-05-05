from glob import glob
import subprocess
from PIL import Image
import os, sys
import imageio

# In order to import utils/file.py we need to add this path.append
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.file import (
    get_png_file_name,
    setup_directory,
    sort_function,
    parse_global_config,
)

OUTPUT_GIFS_DIRECTORY = "./build/gifs"
OUTPUT_IMAGES_DIRECTORY = "./build/images"
INPUT_DIRECTORY = "./step2_spritesheet_to_generative_sheet/output/images"
TEMP_DIRECTORY = "./step3_generative_sheet_to_gif/temp"

global_config = parse_global_config()
fps = global_config["framesPerSecond"]
height = global_config["height"]
width = global_config["width"]
height = global_config["height"]
quality = global_config["quality"]
gif_tool = global_config["gifTool"]
use_batches = global_config["useBatches"]
num_frames_per_batch = global_config["numFramesPerBatch"]
loop_gif = global_config["loopGif"]
save_individual_frames = global_config["saveIndividualFrames"]


class GifTool:
    GIFSKI = "gifski"
    IMAGEIO = "imageio"


def get_temp_directory(file_name: str):
    temp_directory = os.path.join(TEMP_DIRECTORY, get_png_file_name(file_name))
    setup_directory(temp_directory, delete_if_exists=False)
    return temp_directory


def crop_and_save(file_name: str, batch_number: int, width: int, height: int) -> None:
    """
    Crops image into squares and saves them into temp folder

    :param file_name: name of file
    :param height: height of each frame
    :param width: width of each frame
    :returns: int - duration for each frame in milliseconds
    """
    file = os.path.join(INPUT_DIRECTORY, file_name)
    im = Image.open(file)
    if use_batches:
        k = batch_number * num_frames_per_batch
    else:
        k = 0
    imgwidth, imgheight = im.size
    temp_folder_path = get_temp_directory(file_name)

    for i in range(0, imgheight, height):
        for j in range(0, imgwidth, width):
            box = (j, i, j + width, i + height)
            a = im.crop(box)
            file_path = os.path.join(temp_folder_path, f"{k}.png")
            a.save(file_path, quality=95)
            k += 1


def convert_pngs_to_gif(
    file_name: str,
    fps: int,
    output_gif_directory: str,
    is_resize: bool,
    width: int,
    height: int,
):
    images_directory = os.path.join(
        OUTPUT_IMAGES_DIRECTORY, get_png_file_name(file_name)
    )
    if save_individual_frames and not is_resize:
        setup_directory(images_directory)

    temp_img_folder = get_temp_directory(file_name)
    images = []
    for filename in sorted(
        os.listdir(temp_img_folder), key=lambda img: int(get_png_file_name(img))
    ):
        if filename.endswith(".png"):
            temp_img_path = os.path.join(temp_img_folder, filename)
            new_frame = Image.open(temp_img_path)
            if save_individual_frames and not is_resize:
                new_frame.save(os.path.join(images_directory, filename), quality=95)
            images.append(imageio.imread(temp_img_path))

    gif_name = get_png_file_name(file_name) + ".gif"
    if gif_tool == GifTool.IMAGEIO:
        with imageio.get_writer(
            os.path.join(output_gif_directory, gif_name),
            fps=fps,
            mode="I",
            quantizer=0,
            palettesize=256,
            loop=0 if loop_gif else 1,
        ) as writer:
            for image in images:
                writer.append_data(image)
    elif gif_tool == GifTool.GIFSKI:
        subprocess.run(
            f"gifski -o {os.path.join(output_gif_directory, gif_name)} {temp_img_folder}/*.png --fps={fps} --quality={quality} -W={width} -H={height} --repeat={0 if loop_gif else -1}",
            shell=True,
        )
    else:
        raise Exception(
            f"Passed in invalid gif_tool {gif_tool}, only options are gifski and imageio"
        )


def fps_to_ms_duration(fps: int) -> int:
    """
    Converts frames per second to millisecond duration.
    PIL library takes in millisecond duration per frame
    which is unintuitive from an animation perspective.

    NOTE - this will not always be exact given the library
    takes in an integer for number of milliseconds.
    Ex. 12fps = 83.33ms per frame, but the code will convert
    it to 83. Not noticeable by the human eye but still
    worth calling out.

    :param file: fps - frames per second
    :returns: int - duration for each frame in milliseconds
    """
    return int(1000 / fps)


def main(
    batch_number: int = 0,
    generate_gifs: bool = True,
    output_gif_directory=None,
    is_resize=False,
    output_width=None,
    output_height=None,
):
    print("Starting step 3: Converting sprite sheets to gifs")

    if not output_gif_directory:
        output_gif_directory = OUTPUT_GIFS_DIRECTORY

    if not output_width:
        output_width = width

    if not output_height:
        output_height = height

    if use_batches:
        print(f"Starting {batch_number} with generating_gifs flag {generate_gifs}")

    # Only set up folders if its the first batch
    if not use_batches or batch_number == 0:
        for folder in [output_gif_directory, OUTPUT_IMAGES_DIRECTORY, TEMP_DIRECTORY]:
            setup_directory(folder)

    for filename in sorted(os.listdir(INPUT_DIRECTORY), key=sort_function):
        if filename.endswith(".png"):
            print(f"Converting spritesheet to gif for {filename}")
            # Use global_config here from step2, not the override width/height
            crop_and_save(filename, batch_number, width, height)
            if not use_batches or generate_gifs:
                convert_pngs_to_gif(
                    filename,
                    fps,
                    output_gif_directory,
                    is_resize,
                    output_width,
                    output_height,
                )


if __name__ == "__main__":
    main()
