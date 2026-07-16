"""
MSCMA-Net architecture — copied EXACTLY from the training notebook
(main_model_mscma_net_final.ipynb) so that a checkpoint saved during training
loads here with zero key mismatches. Do not change layer names/shapes unless
you also retrain, or state_dict loading will fail.
"""
import math
import torch
import torch.nn as nn
import torch.nn.functional as F


class SEBlock(nn.Module):
    """Squeeze-and-Excitation channel attention."""
    def __init__(self, channels, reduction=8):
        super().__init__()
        self.avg_pool = nn.AdaptiveAvgPool1d(1)
        hidden = max(channels // reduction, 4)
        self.fc = nn.Sequential(
            nn.Linear(channels, hidden), nn.GELU(),
            nn.Linear(hidden, channels), nn.Sigmoid(),
        )

    def forward(self, x):
        w = self.avg_pool(x).squeeze(-1)
        w = self.fc(w).unsqueeze(-1)
        return x * w


class MultiScaleConvBlock(nn.Module):
    def __init__(self, in_ch, out_ch, kernel_sizes=(3, 7, 15, 31)):
        super().__init__()
        assert out_ch % len(kernel_sizes) == 0
        branch_ch = out_ch // len(kernel_sizes)
        self.branches = nn.ModuleList([
            nn.Sequential(
                nn.Conv1d(in_ch, branch_ch, k, padding=k // 2),
                nn.BatchNorm1d(branch_ch),
                nn.GELU(),
            ) for k in kernel_sizes
        ])
        self.proj = nn.Conv1d(branch_ch * len(kernel_sizes), out_ch, 1)
        self.bn = nn.BatchNorm1d(out_ch)
        self.se = SEBlock(out_ch)
        self.act = nn.GELU()
        self.residual = nn.Conv1d(in_ch, out_ch, 1) if in_ch != out_ch else nn.Identity()

    def forward(self, x):
        out = torch.cat([b(x) for b in self.branches], dim=1)
        out = self.se(self.bn(self.proj(out)))
        return self.act(out + self.residual(x))


class MambaBlock(nn.Module):
    """Selective State Space (S6) block, pure PyTorch, pre-norm residual."""
    def __init__(self, d_model, d_state=16, d_conv=4, expand=2, dt_rank=None, dropout=0.1):
        super().__init__()
        self.d_model = d_model
        self.d_inner = expand * d_model
        self.d_state = d_state
        self.dt_rank = dt_rank or math.ceil(d_model / 16)

        self.norm = nn.LayerNorm(d_model)
        self.in_proj = nn.Linear(d_model, self.d_inner * 2, bias=False)
        self.conv1d = nn.Conv1d(self.d_inner, self.d_inner, kernel_size=d_conv,
                                 groups=self.d_inner, padding=d_conv - 1, bias=True)
        self.x_proj = nn.Linear(self.d_inner, self.dt_rank + 2 * self.d_state, bias=False)
        self.dt_proj = nn.Linear(self.dt_rank, self.d_inner, bias=True)

        A = torch.arange(1, self.d_state + 1, dtype=torch.float32).repeat(self.d_inner, 1)
        self.A_log = nn.Parameter(torch.log(A))
        self.D = nn.Parameter(torch.ones(self.d_inner))
        self.out_proj = nn.Linear(self.d_inner, d_model, bias=False)
        self.drop = nn.Dropout(dropout)

    def forward(self, x):
        residual = x
        x = self.norm(x)
        x_in, z = self.in_proj(x).chunk(2, dim=-1)

        x_conv = self.conv1d(x_in.transpose(1, 2))[:, :, :x_in.shape[1]]
        x_conv = F.silu(x_conv.transpose(1, 2))

        x_dbl = self.x_proj(x_conv)
        delta, B_ssm, C_ssm = torch.split(
            x_dbl, [self.dt_rank, self.d_state, self.d_state], dim=-1)
        delta = F.softplus(self.dt_proj(delta))

        A = -torch.exp(self.A_log)
        y = self.selective_scan(x_conv, delta, A, B_ssm, C_ssm, self.D)
        y = y * F.silu(z)
        return residual + self.drop(self.out_proj(y))

    @staticmethod
    def selective_scan(u, delta, A, B, C, D):
        b, l, d_in = u.shape
        n = A.shape[1]
        a_t = torch.exp(delta.unsqueeze(-1) * A)
        b_t = delta.unsqueeze(-1) * B.unsqueeze(2) * u.unsqueeze(-1)

        A_scan, B_scan = a_t, b_t
        d = 1
        while d < l:
            A_shift = torch.ones_like(A_scan)
            B_shift = torch.zeros_like(B_scan)
            A_shift[:, d:] = A_scan[:, :l - d]
            B_shift[:, d:] = B_scan[:, :l - d]
            B_scan = A_scan * B_shift + B_scan
            A_scan = A_shift * A_scan
            d *= 2

        state = B_scan
        y = torch.einsum('bldn,bln->bld', state, C)
        return y + u * D


class AttentionBlock(nn.Module):
    def __init__(self, d_model, num_heads=4, dropout=0.1):
        super().__init__()
        self.norm1 = nn.LayerNorm(d_model)
        self.mha = nn.MultiheadAttention(d_model, num_heads, dropout=dropout, batch_first=True)
        self.norm2 = nn.LayerNorm(d_model)
        self.ff = nn.Sequential(
            nn.Linear(d_model, d_model * 4), nn.GELU(), nn.Dropout(dropout),
            nn.Linear(d_model * 4, d_model),
        )

    def forward(self, x, need_weights=False):
        h = self.norm1(x)
        attn_out, attn_w = self.mha(h, h, h, need_weights=need_weights, average_attn_weights=True)
        x = x + attn_out
        x = x + self.ff(self.norm2(x))
        return x, attn_w


class MultiScaleCNNMambaAttnNet(nn.Module):
    def __init__(self, in_channels=12, num_classes=5, base_channels=32,
                 mamba_layers=2, attn_heads=4, dropout=0.3, stage_dropout=0.1):
        super().__init__()
        self.stem = nn.Sequential(
            nn.Conv1d(in_channels, base_channels, 7, padding=3),
            nn.BatchNorm1d(base_channels), nn.GELU(),
        )
        self.stage1 = MultiScaleConvBlock(base_channels, base_channels * 2)
        self.pool1 = nn.MaxPool1d(2)
        self.drop1 = nn.Dropout(stage_dropout)
        self.stage2 = MultiScaleConvBlock(base_channels * 2, base_channels * 4)
        self.pool2 = nn.MaxPool1d(2)
        self.drop2 = nn.Dropout(stage_dropout)
        self.stage3 = MultiScaleConvBlock(base_channels * 4, base_channels * 8)
        self.pool3 = nn.MaxPool1d(2)
        self.drop3 = nn.Dropout(stage_dropout)

        d_model = base_channels * 8
        self.mamba_layers = nn.ModuleList([MambaBlock(d_model, dropout=dropout) for _ in range(mamba_layers)])
        self.attn = AttentionBlock(d_model, num_heads=attn_heads, dropout=dropout)

        self.classifier = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.GELU(), nn.Dropout(dropout),
            nn.Linear(d_model, num_classes),
        )

    def forward(self, x, return_attn=False):          # x: (B, 12, T)
        x = self.stem(x)
        x = self.drop1(self.pool1(self.stage1(x)))
        x = self.drop2(self.pool2(self.stage2(x)))
        x = self.drop3(self.pool3(self.stage3(x)))     # (B, d_model, T')
        x = x.transpose(1, 2)                          # (B, T', d_model)
        for layer in self.mamba_layers:
            x = layer(x)
        x, attn_w = self.attn(x, need_weights=return_attn)
        x_t = x.transpose(1, 2)
        feat = torch.cat([
            F.adaptive_avg_pool1d(x_t, 1).squeeze(-1),
            F.adaptive_max_pool1d(x_t, 1).squeeze(-1),
        ], dim=-1)
        logits = self.classifier(feat)
        if return_attn:
            return logits, attn_w      # attn_w: (B, T', T') attention map over the pooled sequence
        return logits
