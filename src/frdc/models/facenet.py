import torch
from torch import nn
from torchvision.models import Inception_V3_Weights, inception_v3


class FaceNet(nn.Module):
    INCEPTION_OUT_DIMS = 2048
    INCEPTION_AUX_DIMS = 1000
    INCEPTION_IN_CHANNELS = 3
    MIN_SIZE = 299

    def __init__(self,
                 n_in_channels: int = 8,
                 n_out_classes: int = 10):
        """ Initialize the FaceNet model.

        Args:
            n_in_channels: The number of input channels (bands)
            n_out_classes: The number of output classes

        Notes:
            - Min input size: 299 x 299.
            - Batch size: >= 2.

            Retrieve these constants in class attributes MIN_SIZE and CHANNELS.
        """
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels=n_in_channels,
                               out_channels=10, kernel_size=3,
                               padding=1)
        self.relu1 = nn.ReLU()
        self.conv2 = nn.Conv2d(in_channels=10, out_channels=7, kernel_size=3,
                               padding=1)
        self.relu2 = nn.ReLU()
        self.conv3 = nn.Conv2d(in_channels=7,
                               out_channels=self.INCEPTION_IN_CHANNELS,
                               kernel_size=1)
        self.relu3 = nn.ReLU()

        self.inception = inception_v3(
            weights=Inception_V3_Weights.IMAGENET1K_V1,
        )
        self.inception.fc = nn.Identity()

        # Freeze base model
        for param in self.inception.parameters():
            param.requires_grad = False

        self.fc = nn.Linear(self.INCEPTION_OUT_DIMS, n_out_classes)

        self.feature_extraction = nn.Sequential(
            self.conv1, self.relu1,
            self.conv2, self.relu2,
            self.conv3, self.relu3,
        )

    def forward(self, x: torch.Tensor):
        """ Forward pass.

        Notes:
            - Min input size: 299 x 299.
            - Batch size: >= 2.

        Args:
            x: Input tensor of shape (batch_size, channels, height, width).
        """

        if (
                x.shape[0] < 2 or
                x.shape[2] < self.MIN_SIZE or
                x.shape[3] < self.MIN_SIZE
        ):
            raise RuntimeError(
                f'Input shape {x.shape} must adhere to the following:\n'
                f' - Batch size >= 2\n'
                f' - Height >= {self.MIN_SIZE}\n'
            )
        x = self.feature_extraction(x)

        # During training, the auxiliary outputs are used for auxiliary loss,
        # but during testing, only the main output is used.
        if self.training:
            logits, *_ = self.inception(x)
        else:
            logits = self.inception(x)

        return self.fc(logits)
