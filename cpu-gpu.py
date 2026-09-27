import time
import numpy as np
import torch

# 行列サイズ
N = 12000

print(f"Matrix size: {N} x {N}")

# ========================================
# CPU : NumPy
# ========================================

a_np = np.random.rand(N, N).astype(np.float32)
b_np = np.random.rand(N, N).astype(np.float32)

start = time.perf_counter()

c_np = a_np @ b_np

end = time.perf_counter()

cpu_time = end - start

print(f"CPU (NumPy): {cpu_time:.4f} sec")


# ========================================
# GPU : Apple M1 GPU (MPS)
# ========================================

device = torch.device("mps")

a_gpu = torch.from_numpy(a_np).to(device)
b_gpu = torch.from_numpy(b_np).to(device)

# GPUは非同期実行なので同期してから計測開始
torch.mps.synchronize()

start = time.perf_counter()

c_gpu = a_gpu @ b_gpu

# 計算完了を待つ
torch.mps.synchronize()

end = time.perf_counter()

gpu_time = end - start

print(f"GPU (MPS):   {gpu_time:.4f} sec")


# ========================================
# 比較
# ========================================

print()
print(f"CPU / GPU = {cpu_time / gpu_time:.2f}x")
