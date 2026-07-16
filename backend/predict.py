import os
import numpy as np
import torch

from config import (MODEL_CHECKPOINT, CLASSES, N_LEADS, SEQ_LEN,
                     RISK_ORDER, HIGH_RISK_CLASSES)
from model import MultiScaleCNNMambaAttnNet
from preprocessing import to_model_input

LEAD_NAMES = ["I", "II", "III", "aVR", "aVL", "aVF",
              "V1", "V2", "V3", "V4", "V5", "V6"][:N_LEADS]


class ModelService:
    """Loads the checkpoint once and serves predictions for the whole app."""

    _instance = None

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = MultiScaleCNNMambaAttnNet(in_channels=N_LEADS, num_classes=len(CLASSES)).to(self.device)
        self.lead_mean = np.zeros(N_LEADS, dtype=np.float32)
        self.lead_std = np.ones(N_LEADS, dtype=np.float32)
        self.thresholds = np.full(len(CLASSES), 0.5, dtype=np.float32)
        self.loaded = False
        self._load_checkpoint()

    def _load_checkpoint(self):
        if not os.path.exists(MODEL_CHECKPOINT):
            print(f"[ModelService] WARNING: checkpoint not found at {MODEL_CHECKPOINT}. "
                  f"Predictions will use an UNTRAINED model until you add the real .pth file.")
            self.model.eval()
            return
        ckpt = torch.load(MODEL_CHECKPOINT, map_location=self.device, weights_only=False)
        state_dict = ckpt.get("model_state", ckpt)  # allow raw state_dict too
        self.model.load_state_dict(state_dict)
        self.model.eval()

        if "lead_mean" in ckpt and "lead_std" in ckpt:
            self.lead_mean = np.asarray(ckpt["lead_mean"], dtype=np.float32)
            self.lead_std = np.asarray(ckpt["lead_std"], dtype=np.float32)
        if "thresholds" in ckpt:
            self.thresholds = np.asarray(ckpt["thresholds"], dtype=np.float32)

        self.loaded = True
        print(f"[ModelService] Loaded checkpoint: {MODEL_CHECKPOINT}")

    @classmethod
    def instance(cls) -> "ModelService":
        if cls._instance is None:
            cls._instance = ModelService()
        return cls._instance

    def predict(self, raw_t_leads: np.ndarray) -> dict:
        """raw_t_leads: (SEQ_LEN, N_LEADS) unnormalized. Returns probs, predicted
        classes, risk level, and a per-lead saliency summary for the heatmap view."""
        x = to_model_input(raw_t_leads, self.lead_mean, self.lead_std)  # (1, leads, T)
        x_t = torch.from_numpy(x).to(self.device)
        x_t.requires_grad_(True)

        logits = self.model(x_t)
        probs = torch.sigmoid(logits).detach().cpu().numpy()[0]

        # Grad x Input saliency: which lead/timepoints pushed the top predicted
        # class's logit up the most. Cheap, model-agnostic explainability signal.
        top_idx = int(np.argmax(probs))
        self.model.zero_grad(set_to_none=True)
        logits[0, top_idx].backward()
        grad = x_t.grad.detach().cpu().numpy()[0]      # (leads, T)
        saliency = np.abs(grad * x[0])                  # (leads, T)
        per_lead_saliency = saliency.mean(axis=1)        # (leads,)
        per_lead_saliency = per_lead_saliency / (per_lead_saliency.max() + 1e-8)

        probs_dict = {c: float(p) for c, p in zip(CLASSES, probs)}
        predicted = [c for c, p in zip(CLASSES, probs) if p >= self.thresholds[CLASSES.index(c)]]
        if not predicted:
            predicted = [CLASSES[top_idx]]

        # NORM ("no abnormality detected") is clinically mutually exclusive
        # with every abnormal class. Because each class here gets its own
        # independent sigmoid + threshold, it's mathematically possible for
        # NORM and e.g. CD to both cross their thresholds on a borderline
        # signal — but reporting both together is a real diagnostic
        # contradiction, not just a display quirk. If any abnormal class also
        # crossed its threshold, the abnormal finding takes precedence and
        # NORM is dropped from the reported list.
        abnormal_predicted = [c for c in predicted if c != "NORM"]
        if "NORM" in predicted and abnormal_predicted:
            predicted = abnormal_predicted

        top_class = CLASSES[top_idx]
        top_conf = float(probs[top_idx])
        risk = self._risk_level(predicted)

        saliency_dict = {LEAD_NAMES[i]: float(per_lead_saliency[i]) for i in range(N_LEADS)}
        saliency_timeseries = saliency.tolist()  # full per-lead trace, for live chart overlay only

        return {
            "probs": probs_dict,
            "predicted_classes": predicted,
            "thresholds": {c: float(t) for c, t in zip(CLASSES, self.thresholds)},
            "top_class": top_class,
            "top_confidence": top_conf,
            "risk_level": risk,
            "saliency": saliency_dict,
            "saliency_timeseries": saliency_timeseries,
        }

    @staticmethod
    def _risk_level(predicted_classes) -> str:
        if any(c in HIGH_RISK_CLASSES for c in predicted_classes):
            return "HIGH"
        if predicted_classes == ["NORM"]:
            return "LOW"
        return "MODERATE"
