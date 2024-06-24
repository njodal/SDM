from PIL import Image

import SDM


class ImageSDM:
    def __init__(self, initial_images, number_of_hard_locations=20, radius=30, learning_rate=1.0):
        self.images = initial_images
        h, w        = self.images.image_size()
        address_len = h * w
        content_len = address_len

        self.sdm = SDM.ArithmeticSDM(address_len, content_len, number_of_hard_locations, radius,
                                     learning_rate=learning_rate,
                                     hard_location_creation=SDM.HardLocationCreation.OnDemand)
        for image in self.images.images:
            self.sdm.write(image, image)

    def read(self, image):
        return self.sdm.read(image)


class Images:
    """
    Keeps a list of images
    """
    def __init__(self):
        self.images = []
        self.names  = []

    def load_from_files(self, file_names):
        for file_name in file_names:
            self.images.append(open_image(file_name))
            self.names.append(file_name)

    def image_size(self):
        return [self.images[0].height, self.images[0].width] if len(self.images) > 0 else [0, 0]

    def normalize_images(self, inc=30, min_gray=20):
        """
        In order to be stored in an SDM a normalization process is needed to assure all images have the same size
        :param inc:
        :param min_gray:
        :return:
        """
        self.center( inc=inc, min_gray=min_gray)
        self.force_equal_size()

    def force_equal_size(self):
        """
        Crop each image so all have the same size (equal the size of the min values of images)
        :return:
        """
        max_width  = min([image.width for image in self.images])
        max_height = min([image.height for image in self.images])
        for i, image in enumerate(self.images):
            box = (int(image.width / 2 - max_width / 2), int(image.height / 2 - max_height / 2),
                   int(image.width / 2 + max_width / 2), int(image.height / 2 + max_height / 2))
            self.images[i] = image.crop(box=box)

    def center(self, inc=30, min_gray=20):
        """
        Crop each image taking out all white pixel in the surroundings
        :param inc: pixels to add around
        :param min_gray: any gray value less than this is considered white
        :return:
        """
        for i, image in enumerate(self.images):
            min_width  = image.width
            max_width  = 0
            min_height = image.height
            max_height = 0
            for x in range(image.width):
                for y in range(image.height):
                    if image.getpixel((x, y)) > min_gray:
                        continue
                    min_width  = min(x, min_width)
                    max_width  = max(x, max_width)
                    min_height = min(y, min_height)
                    max_height = max(y, max_height)
            self.images[i] = image.crop(box=(min_width-inc, min_height-inc, max_width+inc, max_height+inc))

    def show(self):
        for image in self.images:
            image.show()

    def print(self):
        for i, image in enumerate(self.images):
            print('   %s: %s' % (self.names[i], image.size))


def open_images(image_list):
    return [Image.open(name) for name in image_list]


def open_image(image_path):
    image = Image.open(image_path)
    return image


if __name__ == "__main__":
    images = Images()
    letters     = ['A', 'B', 'C', 'D', 'E', 'F']
    image_list1 = ['Samples/Letters/letter%s.pgm' % letter for letter in letters]
    images.load_from_files(image_list1)
    images.normalize_images()
    # images.show()
    # images.print()
    sdm = ImageSDM(images)
    image_read = sdm.read(images.images[0])
    image_read.show()



