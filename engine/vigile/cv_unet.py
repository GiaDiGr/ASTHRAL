"""Small U-Net matching the published OCT checkpoint's tensor layout.

Architecture is reimplemented from the MIT-licensed reference project; see
docs/asthral/THIRD_PARTY_NOTICES.md for attribution and license text.
"""
from __future__ import annotations


def _torch():
    try:
        import torch
        return torch
    except ImportError as exc:
        raise RuntimeError("PYTORCH_DEPENDENCY_MISSING") from exc


class _DoubleConv:
    def __new__(cls, in_channels: int, out_channels: int):
        torch = _torch()
        class DoubleConv(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.block = torch.nn.Sequential(
                    torch.nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
                    torch.nn.BatchNorm2d(out_channels), torch.nn.ReLU(inplace=True),
                    torch.nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
                    torch.nn.BatchNorm2d(out_channels), torch.nn.ReLU(inplace=True),
                )

            def forward(self, x):
                return self.block(x)
        return DoubleConv()


class _DownBlock:
    def __new__(cls, in_channels: int, out_channels: int):
        torch = _torch()
        class Down(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.block = torch.nn.Sequential(torch.nn.MaxPool2d(2, 2), _DoubleConv(in_channels, out_channels))

            def forward(self, x):
                return self.block(x)
        return Down()


class _UpBlock:
    def __new__(cls, in_channels: int, out_channels: int):
        torch = _torch()
        class Up(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.up = torch.nn.ConvTranspose2d(in_channels, in_channels // 2, kernel_size=2, stride=2)
                self.conv = _DoubleConv(in_channels, out_channels)

            def forward(self, x, skip):
                x = self.up(x)
                diff_y = skip.size(2) - x.size(2)
                diff_x = skip.size(3) - x.size(3)
                x = torch.nn.functional.pad(x, [diff_x // 2, diff_x - diff_x // 2, diff_y // 2, diff_y - diff_y // 2])
                return self.conv(torch.cat([skip, x], dim=1))
        return Up()


class RetinalRegionUNet:
    """U-Net with 1 grayscale channel and 8 output classes."""

    def __new__(cls):
        torch = _torch()
        class Network(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.inc = _DoubleConv(1, 32)
                self.down1 = _DownBlock(32, 64)
                self.down2 = _DownBlock(64, 128)
                self.down3 = _DownBlock(128, 256)
                self.down4 = _DownBlock(256, 512)
                self.up1 = _UpBlock(512, 256)
                self.up2 = _UpBlock(256, 128)
                self.up3 = _UpBlock(128, 64)
                self.up4 = _UpBlock(64, 32)
                self.outc = torch.nn.Conv2d(32, 8, kernel_size=1)

            def forward(self, x):
                x1 = self.inc(x)
                x2 = self.down1(x1)
                x3 = self.down2(x2)
                x4 = self.down3(x3)
                x5 = self.down4(x4)
                x = self.up1(x5, x4)
                x = self.up2(x, x3)
                x = self.up3(x, x2)
                x = self.up4(x, x1)
                return self.outc(x)
        return Network()
