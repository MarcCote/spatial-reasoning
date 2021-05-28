## predicts entire value map
## rather than a single value

import torch
import math, torch.nn as nn, pdb
import torch.nn.functional as F
from torch.autograd import Variable
import spatial_reasoning.models as models
import spatial_reasoning.utils as utils

class MultiNoBases(nn.Module):
    def __init__(self, state_model, object_model, heatmap_model, args, map_dim = 10):
        super(MultiNoBases, self).__init__()

        self.state_model = state_model
        self.object_model = object_model
        self.heatmap_model = heatmap_model
        self.simple_conv = models.SimpleConv(2).cuda()
        self.rbf = Variable( utils.meta_rbf(map_dim).cuda() )
        self.positions = Variable( self.__init_positions(map_dim).cuda() )

        self.map_dim = map_dim
        self.batch_size = args.batch_size
        self.rbf_batch = self.rbf.repeat(self.batch_size,1,1,1)
        self.positions_batch = self.positions.repeat(self.batch_size,1,1,1)


    def __init_positions(self, map_dim):
        row = torch.arange(0,map_dim).unsqueeze(1).repeat(1,map_dim)
        col = torch.arange(0,map_dim).repeat(map_dim,1)
        positions = torch.stack( (row, col) )
        return positions


    def forward(self, inp):
        (state, obj, text) = inp
        batch_size = state.size(0)
        if batch_size != self.batch_size:
            self.batch_size = batch_size
            self.rbf_batch = self.rbf.repeat(self.batch_size,1,1,1)
            self.positions_batch = self.positions.repeat(self.batch_size,1,1,1)

        ## get state map
        state_out = self.state_model(state)
        obj_out = self.object_model.forward(obj)

        # print('state_out: ', state_out.size())
        # print('obj_out: ', obj_out.size())

        ## get object map
        heatmap = self.heatmap_model((obj_out, text))

        ## repeat heatmap for multiplication by rbf batch
        # heatmap_batch = heatmap.view(self.batch_size,self.map_dim**2,1,1).repeat(1,1,self.map_dim,self.map_dim)

        ## multiply object map by pre-computed manhattan rbf
        ## < batch x size^2 x size x size >
        # obj_local = heatmap_batch * self.rbf_batch
        ## sum contributions from rbf from every source
        ## < batch x 1 x size x size >
        # obj_local = obj_local.sum(1)
        # print('obj_out:', obj_out.size())

        obj_local = heatmap

        # print(obj_local.size())

        # obj_global = self._global(global_coeffs)

        # pdb.set_trace()

        # obj_out = obj_local + obj_global

        map_pred = torch.cat( (state_out, obj_local), 1 )
        # pdb.set_trace()
        map_pred = self.simple_conv(map_pred)
        # map_pred = state_out + obj_out

        return map_pred













