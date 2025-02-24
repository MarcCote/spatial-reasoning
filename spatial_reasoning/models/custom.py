import math, torch, torch.nn.functional as F, pdb
from torch.autograd import Variable
from torch.nn.parameter import Parameter

from torch.nn.modules.module import Module
from torch.nn.modules.utils import _single, _pair, _triple
from torch.nn.modules.conv import _ConvNd

class _ConvNdKernel(Module):

    def __init__(self, in_channels, out_channels, kernel_size, stride,
                 padding, dilation, transposed, output_padding, groups, bias):
        super(_ConvNdKernel, self).__init__()
        if in_channels % groups != 0:
            raise ValueError('in_channels must be divisible by groups')
        if out_channels % groups != 0:
            raise ValueError('out_channels must be divisible by groups')
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.stride = stride
        self.padding = padding
        self.dilation = dilation
        self.transposed = transposed
        self.output_padding = output_padding
        self.groups = groups
        # if transposed:
        #     self.weight = Parameter(torch.Tensor(
        #         in_channels, out_channels // groups, *kernel_size))
        # else:
        #     self.weight = Parameter(torch.Tensor(
        #         out_channels, in_channels // groups, *kernel_size))
        if bias:
            self.bias = Parameter(torch.Tensor(out_channels))
        else:
            self.register_parameter('bias', None)
        self.reset_parameters()

    def reset_parameters(self):
        n = self.in_channels
        for k in self.kernel_size:
            n *= k
        stdv = 1. / math.sqrt(n)
        # self.weight.data.uniform_(-stdv, stdv)
        if self.bias is not None:
            self.bias.data.uniform_(-stdv, stdv)

    def __repr__(self):
        s = ('{name}({in_channels}, {out_channels}, kernel_size={kernel_size}'
             ', stride={stride}')
        if self.padding != (0,) * len(self.padding):
            s += ', padding={padding}'
        if self.dilation != (1,) * len(self.dilation):
            s += ', dilation={dilation}'
        if self.output_padding != (0,) * len(self.output_padding):
            s += ', output_padding={output_padding}'
        if self.groups != 1:
            s += ', groups={groups}'
        if self.bias is None:
            s += ', bias=False'
        s += ')'
        return s.format(name=self.__class__.__name__, **self.__dict__)


class ConvKernel(_ConvNdKernel):
    def __init__(self, in_channels, out_channels, kernel_size, stride=1,
                 padding=0, dilation=1, groups=1, bias=True):
        kernel_size = _pair(kernel_size)
        stride = _pair(stride)
        padding = _pair(padding)
        dilation = _pair(dilation)
        super(ConvKernel, self).__init__(
            in_channels, out_channels, kernel_size, stride, padding, dilation,
            False, _pair(0), groups, bias)

    def forward(self, input, kernel):
        self.weight = Parameter(kernel.data)
        # print('weight: ', self.weight.size())
        # print('bias: ', self.bias.size())
        # print('forward:', type(input.data), type(self.weight.data))
        # print('forward: ', input.size(), self.weight.size())
        return F.conv2d(input, kernel, self.bias, self.stride,
                        self.padding, self.dilation, self.groups)



