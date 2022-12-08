import torch
import torch.nn as nn
import torch.nn.functional as F

import cv2

class GRconvNet(nn.Module):
    def __init__(self):
        super(GRconvNet, self).__init__() 
        
        self.conv1 = nn.Conv2d(4, 32, kernel_size=9, stride=1, padding=4)
        self.bn1 = nn.BatchNorm2d(32)
        
        self.conv2 = nn.Conv2d(32,64,kernel_size=4, stride=2, padding=1)
        self.bn2 = nn.BatchNorm2d(64)

        self.conv3 = nn.Conv2d(64,128,kernel_size=4, stride=2, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        
        # 5 Residual blocks
        self.res1 = ResidualBlock( 32*4, 32*4)
        self.res2 = ResidualBlock( 32*4, 32*4)
        self.res3 = ResidualBlock( 32*4, 32*4)
        self.res4 = ResidualBlock( 32*4, 32*4)
        self.res5 = ResidualBlock( 32*4, 32*4)
        
        # Upsampling blocks
        self.conv4 = nn.ConvTranspose2d(128, 64, kernel_size=4, stride=2, padding=1, output_padding=1)
        self.bn4 = nn.BatchNorm2d(64)

        self.conv5 = nn.ConvTranspose2d(64, 32, kernel_size=4, stride=2, padding=2,output_padding=1)
        self.bn5 = nn.BatchNorm2d(32)

        self.conv6 = nn.ConvTranspose2d(32, 32, kernel_size=9, stride=1, padding=4)

        #outputs
        self.position = nn.Conv2d(in_channels=32, out_channels=1, kernel_size=2)
        self.cosine   = nn.Conv2d(in_channels=32, out_channels=1, kernel_size=2)
        self.sine     = nn.Conv2d(in_channels=32, out_channels=1, kernel_size=2)
        self.width    = nn.Conv2d(in_channels=32, out_channels=1, kernel_size=2)
        
    def forward(self, x):
        
        x=self.bn1(self.conv1(x))
        x=F.relu(x)
        x=self.bn2(self.conv2(x))
        x=F.relu(x)
        x=self.bn3(self.conv3(x))
        x=F.relu(x)
        x = self.res1(x)
        x = self.res2(x)
        x = self.res3(x)
        x = self.res4(x)
        x = self.res5(x)
        x=self.bn4(self.conv4(x))
        x=F.relu(x)
        x=self.bn5(self.conv5(x))
        x=F.relu(x)
        x=self.conv6(x)

        position = self.position(x)
        cosine = self.cosine(x)
        sine = self.sine(x)
        width = self.width(x)

        return position, cosine, sine, width

    def compute_loss(self, xc, yc):
        y_pos, y_cos, y_sin, y_width = yc
        pos_pred, cos_pred, sin_pred, width_pred = self(xc)

        p_loss = F.smooth_l1_loss(pos_pred, y_pos)
        cos_loss = F.smooth_l1_loss(cos_pred, y_cos)
        sin_loss = F.smooth_l1_loss(sin_pred, y_sin)
        width_loss = F.smooth_l1_loss(width_pred, y_width)

        return {
            'loss': p_loss + cos_loss + sin_loss + width_loss,
            'losses': {
                'p_loss': p_loss,
                'cos_loss': cos_loss,
                'sin_loss': sin_loss,
                'width_loss': width_loss
            },
            'pred': {
                'pos': pos_pred,
                'cos': cos_pred,
                'sin': sin_pred,
                'width': width_pred
            }
        }

    def predict(self, xc):
        pos_pred, cos_pred, sin_pred, width_pred = self(xc)
        return {
            'pos': pos_pred,
            'cos': cos_pred,
            'sin': sin_pred,
            'width': width_pred
        }
        

class ResidualBlock(nn.Module):
    
    # Residual block class
    def __init__(self, in_channels, out_channels, kernel_size=3):
        super(ResidualBlock, self).__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size, padding=1)
        self.bn1 = nn.BatchNorm2d(in_channels)
        self.conv2 = nn.Conv2d(in_channels, out_channels, kernel_size, padding=1)
        self.bn2 = nn.BatchNorm2d(in_channels)

    def forward(self, x_in):
        x = self.conv1(x_in)
        x = self.bn1(x)
        x = F.relu(x)
        x = self.conv2(x)
        x = self.bn2(x)
        x = x+x_in
        return x

net = GRconvNet()
#resnet=ResidualBlock(4,12)
