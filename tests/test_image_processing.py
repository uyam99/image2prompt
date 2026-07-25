import tempfile
import unittest
from pathlib import Path

from PIL import Image, features

from image2prompt.image_processing import ImageInputError, prepare_image


class ImageProcessingTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_standard_formats(self):
        self.assertTrue(features.check("webp"), "Pillow must include WebP support")
        formats = {
            "JPEG": "jpg",
            "PNG": "png",
            "WEBP": "webp",
            "BMP": "bmp",
            "TIFF": "tif",
            "GIF": "gif",
        }
        for image_format, extension in formats.items():
            with self.subTest(image_format=image_format):
                path = self.root / f"sample.{extension}"
                Image.new("RGB", (32, 16), "red").save(path, format=image_format)
                result = prepare_image(path, size=64)
                self.assertEqual(result.source_format, image_format)
                self.assertEqual(result.image.mode, "RGB")
                self.assertEqual(result.image.size, (64, 64))

    def test_exif_orientation(self):
        path = self.root / "rotated.jpg"
        exif = Image.Exif()
        exif[274] = 6
        Image.new("RGB", (12, 6), "blue").save(path, exif=exif)
        result = prepare_image(path, size=24)
        self.assertEqual(result.original_size, (12, 6))
        self.assertEqual(result.oriented_size, (6, 12))

    def test_transparency_is_composited_on_white(self):
        path = self.root / "transparent.png"
        image = Image.new("RGBA", (4, 4), (0, 0, 0, 0))
        image.putpixel((2, 2), (255, 0, 0, 255))
        image.save(path)
        result = prepare_image(path, size=4)
        self.assertEqual(result.image.getpixel((0, 0)), (255, 255, 255))
        self.assertEqual(result.image.getpixel((2, 2)), (255, 0, 0))

    def test_animated_image_uses_first_frame(self):
        path = self.root / "animated.gif"
        frames = [Image.new("RGB", (4, 4), color) for color in ("red", "blue")]
        frames[0].save(path, save_all=True, append_images=frames[1:])
        result = prepare_image(path, size=4)
        red, _, blue = result.image.getpixel((2, 2))
        self.assertGreater(red, blue)

    def test_invalid_and_oversized_images_are_rejected(self):
        broken = self.root / "broken.png"
        broken.write_bytes(b"not an image")
        with self.assertRaises(ImageInputError):
            prepare_image(broken)

        large = self.root / "large.png"
        Image.new("RGB", (10, 10), "black").save(large)
        with self.assertRaises(ImageInputError):
            prepare_image(large, max_pixels=99)


if __name__ == "__main__":
    unittest.main()
