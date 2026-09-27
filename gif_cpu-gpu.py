import time
import numpy as np
import torch

WIDTH = 1920
HEIGHT = 1080
FRAMES = 100

print(f"{WIDTH}x{HEIGHT} RGB x {FRAMES} frames")

# 100フレーム分の疑似画像
images = np.random.randint(
    0, 256,
    (FRAMES, HEIGHT, WIDTH, 3),
    dtype=np.uint8
)

# ========================================
# CPU (NumPy)
# ========================================

start = time.perf_counter()

cpu = images.astype(np.float32)

# 明るさ変更
cpu *= 1.15

# 簡単なガンマ補正的な処理
cpu /= 255.0
cpu = np.sqrt(cpu)
cpu *= 255.0

# 0～255へ収める
cpu = np.clip(cpu, 0, 255).astype(np.uint8)

cpu_time = time.perf_counter() - start

print(f"CPU (NumPy): {cpu_time:.4f} sec")


# ========================================
# GPU (MPS)
# ========================================

start = time.perf_counter()

device = torch.device("mps")

gpu = torch.from_numpy(images).to(device)

torch.mps.synchronize()


gpu = gpu.float()

# CPUと同じ処理
gpu *= 1.15
gpu /= 255.0
gpu = torch.sqrt(gpu)
gpu *= 255.0
gpu = torch.clamp(gpu, 0, 255).to(torch.uint8)

torch.mps.synchronize()
gpu_time = time.perf_counter() - start

print(f"GPU (MPS):   {gpu_time:.4f} sec")

print()
print(f"CPU / GPU = {cpu_time / gpu_time:.2f}x")
