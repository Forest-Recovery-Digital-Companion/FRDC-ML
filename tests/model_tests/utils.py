from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
from sklearn.preprocessing import OrdinalEncoder, StandardScaler
from torchvision.transforms import RandomVerticalFlip
from torchvision.transforms.v2 import (
    Compose,
    ToImage,
    ToDtype,
    RandomVerticalFlip,
    RandomCrop,
    CenterCrop,
    RandomRotation,
    RandomApply,
    Resize,
)
from torchvision.transforms.v2 import RandomHorizontalFlip

from frdc.load.dataset import FRDCDataset

THIS_DIR = Path(__file__).parent

BANDS = ["NB", "NG", "NR", "RE", "NIR"]


class FRDCDatasetFlipped(FRDCDataset):
    def __len__(self):
        """Assume that the dataset is 4x larger than it actually is.

        For example, for index 0, we return the original image. For index 1, we
        return the horizontally flipped image and so on, until index 3.
        Then, return the next image for index 4, and so on.
        """
        return super().__len__() * 4

    def __getitem__(self, idx):
        """Alter the getitem method to implement the logic above."""
        x, y = super().__getitem__(int(idx // 4))
        if idx % 4 == 0:
            return x, y
        elif idx % 4 == 1:
            return RandomHorizontalFlip(p=1)(x), y
        elif idx % 4 == 2:
            return RandomVerticalFlip(p=1)(x), y
        elif idx % 4 == 3:
            return RandomHorizontalFlip(p=1)(RandomVerticalFlip(p=1)(x)), y


def val_preprocess(size: int):
    return lambda x: Compose(
        [
            ToImage(),
            ToDtype(torch.float32, scale=True),
            Resize(size, antialias=True),
            CenterCrop(size),
        ]
    )(x)


def n_weak_aug(size, n_aug: int = 2):
    return lambda x: (
        [weak_aug(size)(x) for _ in range(n_aug)] if n_aug > 0 else None
    )


def n_strong_aug(size, n_aug: int = 2):
    return lambda x: (
        [strong_aug(size)(x) for _ in range(n_aug)] if n_aug > 0 else None
    )


def n_weak_strong_aug(size, n_aug: int = 2):
    def f(x):
        x_weak = n_weak_aug(size, n_aug)(x)
        x_strong = n_strong_aug(size, n_aug)(x)
        return list(zip(*[x_weak, x_strong])) if n_aug > 0 else None

    return f


def weak_aug(size: int):
    return lambda x: Compose(
        [
            ToImage(),
            ToDtype(torch.float32, scale=True),
            Resize(size, antialias=True),
            CenterCrop(size),
            RandomHorizontalFlip(),
            RandomVerticalFlip(),
            RandomApply([RandomRotation((90, 90))], p=0.5),
        ]
    )(x)


def strong_aug(size: int):
    return lambda x: Compose(
        [
            ToImage(),
            ToDtype(torch.float32, scale=True),
            Resize(size, antialias=True),
            RandomCrop(size, pad_if_needed=False),  # Strong
            RandomHorizontalFlip(),
            RandomVerticalFlip(),
            RandomApply([RandomRotation((90, 90))], p=0.5),
        ]
    )(x)


def get_y_encoder(targets):
    oe = OrdinalEncoder(
        handle_unknown="use_encoded_value",
        unknown_value=np.nan,
    )
    oe.fit(np.array(targets).reshape(-1, 1))
    return oe


def get_x_scaler(segments):
    ss = StandardScaler()
    ss.fit(
        np.concatenate([segm.reshape(-1, segm.shape[-1]) for segm in segments])
    )
    return ss
