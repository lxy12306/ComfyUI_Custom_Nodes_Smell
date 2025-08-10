import torch
import unittest
import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from ImageFunctionNode import ImagePad

class TestImagePad(unittest.TestCase):

    def setUp(self):
        self.image_pad = ImagePad()

    def test_pad_with_color(self):
        image = torch.rand((1, 64, 64, 3))  # Random image with shape [B, H, W, C]
        mask = torch.rand((1, 64, 64))      # Random mask with shape [B, H, W]
        left, right, top, bottom = 10, 10, 20, 20
        extra_padding = 5
        color = "255, 0, 0"  # Red color
        pad_mode = "color"

        padded_image, padded_mask = self.image_pad.pad(
            image=image,
            left=left,
            right=right,
            top=top,
            bottom=bottom,
            extra_padding=extra_padding,
            color=color,
            pad_mode=pad_mode,
            mask=mask
        )

        self.assertEqual(padded_image.shape[1], 64 + top + bottom + 2 * extra_padding)
        self.assertEqual(padded_image.shape[2], 64 + left + right + 2 * extra_padding)
        self.assertEqual(padded_mask.shape[1], 64 + top + bottom + 2 * extra_padding)
        self.assertEqual(padded_mask.shape[2], 64 + left + right + 2 * extra_padding)

    def test_pad_with_edge(self):
        image = torch.rand((1, 64, 64, 3))  # Random image with shape [B, H, W, C]
        left, right, top, bottom = 5, 5, 10, 10
        extra_padding = 0
        color = "0, 0, 0"  # Black color (not used in edge mode)
        pad_mode = "edge"

        padded_image, _ = self.image_pad.pad(
            image=image,
            left=left,
            right=right,
            top=top,
            bottom=bottom,
            extra_padding=extra_padding,
            color=color,
            pad_mode=pad_mode
        )

        self.assertEqual(padded_image.shape[1], 64 + top + bottom)
        self.assertEqual(padded_image.shape[2], 64 + left + right)

    def test_pad_with_target_size(self):
        image = torch.rand((1, 64, 64, 3))  # Random image with shape [B, H, W, C]
        target_width, target_height = 128, 128
        color = "0, 255, 0"  # Green color
        pad_mode = "color"

        padded_image, _ = self.image_pad.pad(
            image=image,
            left=0,
            right=0,
            top=0,
            bottom=0,
            extra_padding=0,
            color=color,
            pad_mode=pad_mode,
            target_width=target_width,
            target_height=target_height
        )

        self.assertEqual(padded_image.shape[1], target_height)
        self.assertEqual(padded_image.shape[2], target_width)

if __name__ == "__main__":
    unittest.main()