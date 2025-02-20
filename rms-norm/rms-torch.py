import torch

def rms_layer_norm_3(x, gamma, epsilon=1e-8):
    # x and gamma are expected to be torch.Tensors
    return (x / torch.sqrt((x ** 2).mean() + epsilon)) * gamma

x = torch.tensor([3.0, 4.0, 5.0])
gamma = torch.tensor([0.1, 0.2, 0.3])
out = rms_layer_norm_3(x, gamma)
print(x)
print(out)
