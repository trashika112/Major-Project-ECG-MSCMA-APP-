import torch
ckpt = torch.load("weights/best_model.pt", map_location="cpu", weights_only=False)
print(ckpt.keys())
print("thresholds" in ckpt, "lead_mean" in ckpt, "lead_std" in ckpt)