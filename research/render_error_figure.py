"""Render optional frozen-test failure diagnostics; never trains or tunes a model."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
AUDIT=ROOT/"docs"/"ERROR_AUDIT_RECEIPT.json"
OUTPUT=ROOT/"docs"/"figures"/"phase_error_audit.png"

def main() -> None:
    receipt=json.loads(AUDIT.read_text(encoding="utf8"))
    phases=("0-9","10-19","20-29","30+")
    values=[receipt["by_phase"][p] for p in phases]
    e0=[v["M0_10bin_ECE"] for v in values]
    e1=[v["M1_10bin_ECE"] for v in values]
    db=[v["delta_brier_M1_minus_M0"] for v in values]
    fig,(a,b)=plt.subplots(1,2,figsize=(10.3,3.45),width_ratios=[1.15,1])
    x=np.arange(4)
    a.bar(x-.18,e0,width=.35,color="#788899",label="M0 gold only")
    a.bar(x+.18,e1,width=.35,color="#2A607F",label="M1 gold + time")
    a.set_xticks(x,phases)
    a.set_ylabel("10-bin ECE (lower is better)")
    a.set_ylim(0,max(e0+e1)*1.33)
    a.set_title("Calibration by match phase",fontsize=11)
    a.legend(loc="upper right",frameon=False,fontsize=8)
    for i,(u,v) in enumerate(zip(e0,e1)):
        a.annotate(f"{u:.3f}",(i-.18,u),xytext=(0,3),textcoords="offset points",ha="center",fontsize=8)
        a.annotate(f"{v:.3f}",(i+.18,v),xytext=(0,3),textcoords="offset points",ha="center",fontsize=8)
    b.axhline(0,color="#313943",linewidth=.9)
    b.bar(x,db,color=["#2A607F" if val<=0 else "#B55A39" for val in db],width=.56)
    b.set_xticks(x,phases)
    b.set_ylabel("M1 minus M0 Brier (negative is better)")
    b.set_title("Brier gain reverses at minute 30+",fontsize=11)
    span=max(abs(q) for q in db)*1.35
    b.set_ylim(-span,span)
    for i,val in enumerate(db):
        b.annotate(f"{val:+.4f}",(i,val),xytext=(0,3 if val>0 else -11),
                   textcoords="offset points",ha="center",fontsize=8)
    for ax in (a,b):
        ax.set_xlabel("Minute")
        ax.spines[["top","right"]].set_visible(False)
        ax.tick_params(labelsize=9)
    fig.suptitle("Fixed held-out forecasts · descriptive error audit, not model selection",
                 fontsize=12,fontweight="bold",y=1.025)
    fig.tight_layout()
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(OUTPUT,dpi=190,bbox_inches="tight",facecolor="white")
    plt.close(fig)
    print("Rendered",OUTPUT,OUTPUT.stat().st_size)

if __name__=="__main__":
    main()
