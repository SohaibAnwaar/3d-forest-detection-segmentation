import sys
sys.path.insert(0, '../')
from forest3D import lidar_IO,stemSegmenter,processLidar

import numpy as np
import json
import os

# read data
directory = '/home/lloyd/Documents/datasets/lidar/forestry_usyd/labelled_data/stem_segmentation/hovermap/labelled_pcds/'
data_list,f_list = lidar_IO.readFromDirectory(directory,type='asc',output_fileList=True,delimiter=' ',x=0,y=1,z=2,label=4,returns=3)

# separate into xyz, intensities and labels
MAX_RETURN_INTENSITY = 77.0
numTrees = len(data_list)#len(data_list)
xyz_list=[]
label_list=[]
intensity_list=[]
for i in range(numTrees):
    xyz_list.append(data_list[i][:,:3]) # x,y,z  remove offset to make calcs more stable
    label_list.append((data_list[i][:,4]).astype(int)) # label
    intensity_list.append((data_list[i][:,3])/MAX_RETURN_INTENSITY) # return intensity



# set training and validation indexes
train_idx = [0,1,2,3]
val_idx = [0,1,2,3]


# configure training parameters
model_dict = {
    'input_dims': [150, 150, 100],
    'res': [0.1, 0.1, 0.4],
    'isReturns' : True,
    'nClasses' : 3  # stem, foliage, background
}
train_op_dict = {
    'opt_method': 'Adam',
    'lr': 1e-4,
    'decay_rate': None,
    'decay_steps': None,
    'piecewise_bounds': None,
    'piecewise_values': None
}
train_model_dict = {
    'nEpochs': 3000,
    'train_bs': 4,#3
    'val_bs' : 4,#5
    'augment': True,
    'numAugs':2,#3
    'keep_prob': 0.8,
    'save_epochs': [2000],
    'save_addr': '../../models/stem_segmentation/prototype',
    'save_figure': 1
}

# save config file
config = {}
config['model_dict'] = model_dict
config['train_op_dict'] = train_op_dict
config['train_model_dict'] = train_model_dict
with open(os.path.join(train_model_dict['save_addr'], 'net_config.json'), 'w') as outfile:
    json.dump(config, outfile)


# create iterator objects
train_iter = processLidar.iterator_binaryVoxels_pointlabels([xyz_list[i] for i in train_idx],[label_list[i] for i in train_idx],
                                                           returns=[intensity_list[i] for i in train_idx],
                                                           res=model_dict['res'], gridSize=model_dict['input_dims'],
                                                           numClasses=model_dict['nClasses']-1, batchsize=train_model_dict['train_bs'])

val_iter = processLidar.iterator_binaryVoxels_pointlabels([xyz_list[i] for i in val_idx],[label_list[i] for i in val_idx],
                                                           returns=[intensity_list[i] for i in val_idx],
                                                           res=model_dict['res'], gridSize=model_dict['input_dims'],
                                                           numClasses=model_dict['nClasses']-1, batchsize=train_model_dict['val_bs'])


# build model and training nodes
stem_model = stemSegmenter.VoxelStemSeg(**model_dict)
stem_model.train_op(**train_op_dict)

# train model with iterators
stem_model.train_model(train_iter, val_iter, **train_model_dict)


