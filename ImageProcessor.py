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
    def __init__(self, y_rotations, x_rotations, final_counter, context):
        self.target_dimension = 280
        self.target_size = 512 * 1024  # 512 KB
        self.cropping = {'left': [], 'top': [], 'right': [], 'bottom': []}
        self.images = []
        self.y_rotations = y_rotations
        self.x_rotations = 2 * x_rotations + 1  # Total vertical rotations
        self.final_counter = final_counter
        self.context = context

    def blend(self, file):
        print(file)
        blended_arr = Image.open(file)
        blended_arr = array(blended_arr)
        horizontal = blended_arr[:, :, 3].any(axis=0).nonzero()[0]
        vertical = blended_arr[:, :, 3].any(axis=1).nonzero()[0]
        self.cropping['left'].append(horizontal[0])
        self.cropping['top'].append(vertical[0])
        self.cropping['right'].append(horizontal[-1])
        self.cropping['bottom'].append(vertical[-1])
        blended_image = fromarray(blended_arr.astype(uint8), mode='RGBA')
        blended_image = blended_image.crop((
            horizontal[0],
            vertical[0],
            horizontal[-1],
            vertical[-1]
        ))
        self.images.append(blended_image)

    def stitch_and_upload(self, directory, file_format="PNG"):
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
        print('Target scaling ratio: %f' % target_ratio)
        max_frame_size = (
            int(target_ratio * max_frame_size[0]),
            int(target_ratio * max_frame_size[1])
        )
        print('Scaled max frame size: ' + str(max_frame_size))

        full_image = new(mode='RGBA', color=(255, 255, 255, 0), size=((
            (max_frame_size[0] + 1) * self.y_rotations * self.x_rotations,
            max_frame_size[1]
        )))
        curr_offset = 0
        offset_map = []
        for i, image in enumerate(self.images):
            image = image.resize((
                int(image.width * target_ratio),
                int(image.height * target_ratio),
            ), ANTIALIAS)
            left_crop = int(
                target_ratio * (self.cropping['left'][i] - min_cropping[0]))
            top_crop = int(
                target_ratio * (self.cropping['top'][i] - min_cropping[1]))
            full_image.paste(image, (curr_offset, top_crop), image)
            offset_map += [curr_offset - i, image.height, left_crop]
            curr_offset += image.width + 1

        full_image = full_image.crop((
            0,
            0,
            curr_offset,
            max_frame_size[1],
        ))
        output_file = f'rendered{self.final_counter}.' + file_format.lower()
        output_file = os.path.join(directory, output_file)
        if path.exists(output_file):
            remove(output_file)

        ImageFile.MAXBLOCK = full_image.height * full_image.width * 16

        if file_format == "JPEG":
            full_image = full_image.convert("RGB")
        full_image.save(output_file, format=file_format)

        lang_category = "3D model images"
        if self.context.window_manager.wiki_language == 'es':
            lang_category = "Imágenes de modelos 3D"
        
        description = f'''{{{{#switch: {{{{{{1|}}}}}}
  | url = <nowiki>%s?%s</nowiki>
  | map = \n%d, %d, %d, %d, %s
  | height = %d
  | startframe = 16
  }}<noinclude>{{{{3D viewer}}[[Category:{lang_category}]]''' % (
            "url",
            datetime.strftime(datetime.utcnow(), '%Y%m%d%H%M%S'),
            curr_offset,
            max_frame_size[0],
            max_frame_size[1],
            self.x_rotations,
            ', '.join([str(o) for o in offset_map]),
            self.target_dimension
        )
        with open(os.path.join(directory, f"renderedoffsets{self.final_counter}.txt"), "w+") as f:
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