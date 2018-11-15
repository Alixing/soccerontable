import argparse
import soccer3d
import json
from os.path import join
import utils.camera as cam_utils
import numpy as np
import cv2


parser = argparse.ArgumentParser(description='Calibrate a soccer video')
parser.add_argument('--path_to_data', default='/home/krematas/Mountpoints/grail/data/barcelona', help='path')
parser.add_argument('--out', default='/home/krematas/Mountpoints/grail/data/barcelona/texture.png', help='path')
parser.add_argument('--height', type=int, default=2160, help='Margin around the pose')
parser.add_argument('--width', type=int, default=3840, help='Margin around the pose')
parser.add_argument('--frame', type=int, default=0, help='Frame to extract texture')


opt, _ = parser.parse_known_args()


with open(join(opt.path_to_data, 'players', 'metadata', 'position.json')) as f:
    data = json.load(f)


db = soccer3d.YoutubeVideo(opt.path_to_data, height=opt.height, width=opt.width)
db.digest_metadata()


img = db.get_frame(opt.frame)
mask = db.get_mask_from_detectron(opt.frame)
cam_npy = db.calib[db.frame_basenames[opt.frame]]

cam = cam_utils.Camera('tmp', cam_npy['A'], cam_npy['R'], cam_npy['T'], db.shape[0], db.shape[1])

mask = cv2.dilate(mask, np.ones((9, 9), np.int8), iterations=1)

img = cv2.inpaint((img[:, :, (2, 1, 0)]*255).astype(np.uint8), (mask*255).astype(np.uint8), 3, cv2.INPAINT_TELEA)[:, :, (2, 1, 0)]/255.

W, H = 104.73, 67.74

#   a X-------------------------X b
#     |                         |
#     |                         |
#   d X-------------------------X c

# Whole field
p3 = np.array([[-W/2., 0, H/2], [W/2., 0, H/2], [W/2., 0, -H/2] , [-W/2., 0, -H/2]])
p2, _ = cam.project(p3)

pp2 = np.array([[0, 0], [db.shape[1]-1, 0], [db.shape[1], db.shape[0]], [0, db.shape[0]-1]])

filled = (img*255).astype(np.uint8)

M = cv2.getPerspectiveTransform(p2.astype(np.float32), pp2.astype(np.float32))
dst = cv2.warpPerspective(filled, M, (db.shape[1], db.shape[0]), )
cv2.imwrite(opt.out, dst[::-1, ::-1, (2, 1, 0)])
