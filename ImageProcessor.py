from datetime import datetime
from os import path, remove
import os
import re
try:
    from PIL.Image import ANTIALIAS, fromarray, new
    from PIL import ImageFile, Image
except ModuleNotFoundError:
    print("Could not find PIL")
from numpy import array, uint8


class ImageProcessor(object):
    """
    A class to handle all the imageprocessing done on the screenshots.
    Deals with blending (finding transparency), cropping, and stitching.
    """

    def __init__(self, y_rotations, x_rotations):
        self.target_dimension = 280
        self.target_size = 512 * 1024  # 512 KB
        self.cropping = {'left': [], 'top': [], 'right': [], 'bottom': []}
        self.images = []
        self.y_rotations = y_rotations
        self.x_rotations = 2*x_rotations+1  # Total vertical rotations

    def blend(self, file):
        """
        Blends the two images into an alpha image using percieved luminescence.
        https://en.wikipedia.org/wiki/Luma_(video)#Use_of_relative_luminance
        Then, finds the closest-cropped lines that are all white.
        Uses numpy because traversing python arrays is very slow.
        """
        print(file)
        blended_arr = Image.open(file)
        blended_arr = array(blended_arr)
        # Calculate crop lines
        horizontal = blended_arr[:, :, 3].any(axis=0).nonzero()[0]
        vertical = blended_arr[:, :, 3].any(axis=1).nonzero()[0]
        self.cropping['left'].append(horizontal[0])
        self.cropping['top'].append(vertical[0])
        self.cropping['right'].append(horizontal[-1])
        self.cropping['bottom'].append(vertical[-1])
        # This needs to be a uint8 to render correctly.
        blended_image = fromarray(blended_arr.astype(uint8), mode='RGBA')
        blended_image = blended_image.crop((
            horizontal[0],
            vertical[0],
            horizontal[-1],
            vertical[-1]
        ))
        self.images.append(blended_image)

    def stitch_and_upload(self, directory, file_format="PNG"):
        """
        Crops the images to a shared size, then pastes them together.
        Prompts for login and uploads to the wiki when done.
        """
        # Determining crop bounds
        min_cropping = (
            min(self.cropping['left']),
            min(self.cropping['top']),
            max(self.cropping['right']),
            max(self.cropping['bottom'])
        )
        print('Min cropping: ' + str(min_cropping))
        max_frame_size = (
            min_cropping[2] - min_cropping[0],
            min_cropping[3] - min_cropping[1]
        )
        print('Max frame size: ' + str(max_frame_size))
        target_ratio = self.target_dimension / max(max_frame_size)
        # target_ratio = 1
        print('Target scaling ratio: %f' % target_ratio)
        max_frame_size = (
            int(target_ratio * max_frame_size[0]),
            int(target_ratio * max_frame_size[1])
        )
        print('Scaled max frame size: ' + str(max_frame_size))

        # Pasting together
        full_image = new(mode='RGBA', color=(255, 255, 255, 0), size=((
            (max_frame_size[0]+1)*self.y_rotations*self.x_rotations,
            max_frame_size[1]
        )))
        curr_offset = 0
        offset_map = []
        for i, image in enumerate(self.images):
            image = image.resize((
                int(image.width*target_ratio),
                int(image.height*target_ratio),
            ), ANTIALIAS)
            left_crop = int(
                target_ratio*(self.cropping['left'][i]-min_cropping[0]))
            top_crop = int(
                target_ratio*(self.cropping['top'][i]-min_cropping[1]))
            full_image.paste(image, (curr_offset, top_crop), image)
            # Offset map adds 1 manually for some reason
            offset_map += [curr_offset-i, image.height, left_crop]
            # Increase by 1 each time to add a 1px gap
            curr_offset += image.width+1
        full_image = full_image.crop((
            0,
            0,
            curr_offset,
            max_frame_size[1],
        ))
        output_file = 'weapon.' + file_format.lower()
        output_file = os.path.join(directory, output_file)
        if path.exists(output_file):
            remove(output_file)

        # Ensure there is enough allocated space to save the image as progressive
        ImageFile.MAXBLOCK = full_image.height * full_image.width * 16

        if file_format == "JPEG":
            full_image = full_image.convert("RGB")
        full_image.save(output_file, format=file_format)

        description = '''{{#switch: {{{1|}}}
  | url = <nowiki>%s?%s</nowiki>
  | map = \n%d, %d, %d, %d, %s
  | height = %d
  | startframe = 16
  }}<noinclude>{{3D viewer}}[[Category:3D model images]]''' % (
            "url",
            datetime.strftime(datetime.utcnow(), '%Y%m%d%H%M%S'),
            curr_offset,
            max_frame_size[0],
            max_frame_size[1],
            self.x_rotations,
            ', '.join([str(o) for o in offset_map]),
            self.target_dimension
        )
        with open(os.path.join(directory, "weaponoffsets.txt"), "w+") as f:
            f.write(description)


if __name__ == "__main__":

    directory = os.path.join(os.path.dirname(__file__), 'Booth')
    files = os.listdir(directory)
    files.sort(key=lambda f: int(re.sub('\D', '', f)))
    WIDTH = 197
    HEIGHT = 152
    NUM = len(files)
    Y_ROTATIONS = int(NUM/3)
    X_ROTATIONS = 3
    print(Y_ROTATIONS, X_ROTATIONS)

    p = ImageProcessor(Y_ROTATIONS, 1)
    for i, filename in enumerate(files):
        print(filename)
        p.blend(os.path.join(directory, filename))
    p.stitch_and_upload()
