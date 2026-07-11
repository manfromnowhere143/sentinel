# iter45 environment shim (recorded in SETUP_LOG.md). NO client/model code is modified.
# The uniad:latest image ships torch 1.9.1+cu111; CUDA 11.1's cuSOLVER cannot initialize on
# the L4 (sm_89): cusolverDnCreate -> CUSOLVER_STATUS_INTERNAL_ERROR (proven in isolation).
# This shim routes the cuSOLVER-backed dense linalg ops through CPU and returns results on
# the original device. Same math, different execution provider.
import torch

def _cpu_fallback(fn):
    def wrapped(input, *args, **kwargs):
        if isinstance(input, torch.Tensor) and input.is_cuda:
            out = fn(input.cpu(), *args, **kwargs)
            if isinstance(out, torch.Tensor):
                return out.to(input.device)
            if isinstance(out, tuple):
                return type(out)(o.to(input.device) if isinstance(o, torch.Tensor) else o for o in out)
            return out
        return fn(input, *args, **kwargs)
    return wrapped

torch.inverse = _cpu_fallback(torch.inverse)
torch.linalg.inv = _cpu_fallback(torch.linalg.inv)
torch.cholesky = _cpu_fallback(torch.cholesky)
torch.linalg.cholesky = _cpu_fallback(torch.linalg.cholesky)
torch.svd = _cpu_fallback(torch.svd)
torch.linalg.svd = _cpu_fallback(torch.linalg.svd)
torch.linalg.eigh = _cpu_fallback(torch.linalg.eigh)
torch.symeig = _cpu_fallback(torch.symeig)
Tensor = torch.Tensor
Tensor.inverse = _cpu_fallback(Tensor.inverse)
print('[iter45-shim] cuSOLVER-backed linalg ops routed via CPU (torch', torch.__version__, ')')
