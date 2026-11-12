#!/usr/bin/env python3
"""Reproduce descriptive, outcome-blind paired-match state figure from frozen CSV."""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO=Path(__file__).resolve().parents[1]
SOURCE=REPO/"research/results/matched_option_case_timeline.csv"
DEST=REPO/"research/results/matched_option_case.png"

def main():
    df=pd.read_csv(SOURCE)
    assert df.match_id.nunique()==2
    a,b=sorted(df.match_id.unique())
    fig,axes=plt.subplots(3,1,figsize=(12,8.1),sharex=True,constrained_layout=True)
    specs=[
        ("gold_lead","Radiant gold lead","gold",1),
        ("aegis_claim5","Signed 5-minute Aegis claim proxy","proxy",1),
        ("unconverted_gold_k","Gold lead with adverse tower/barracks control","k gold",1)
    ]
    styles=["-","--"]
    for i,(mid,g) in enumerate(df.groupby("match_id",sort=True)):
        line_label=f"Match {int(mid)}"
        g=g.sort_values("minute")
        for ax,(field,label,unit,divisor) in zip(axes,specs):
            ax.plot(g.minute,g[field]/divisor,
                    linewidth=2.,linestyle=styles[i],label=line_label)
    for ax,(field,label,unit,divisor) in zip(axes,specs):
        ax.axvline(25,color="0.35",linestyle=":",linewidth=1)
        ax.axhline(0,color="0.75",linewidth=.7)
        ax.set_ylabel(label+"\n("+unit+")",fontsize=10)
        ax.grid(True,alpha=.16)
        ax.legend(loc="best",fontsize=9,frameon=False)
    d=df[df.minute==25].sort_values("match_id")
    for _,r in d.iterrows():
        axes[0].annotate(f'{int(r.gold_lead):,}',(25,r.gold_lead),
                         xytext=(7,8 if r.match_id==a else -14),
                         textcoords="offset points",fontsize=9)
    axes[0].set_title("Same minute and nearly identical economy, different strategic states",
                      fontsize=13,pad=13)
    axes[-1].set_xlabel("Game clock (minutes)")
    fig.suptitle("Matched observational pair at minute 25 | Both patch 59 | Same Radiant gold sign",
                 y=1.04,fontsize=12)
    fig.text(.03,-.02,
             "Pair selected without using match outcomes. Aegis is a recent pickup proxy, not current possession. No causal effect is inferred.",
             fontsize=9)
    DEST.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(DEST,dpi=168,bbox_inches="tight",facecolor="white")
    plt.close(fig)
    print("FIGURE_WRITTEN",DEST,DEST.stat().st_size)

if __name__=="__main__":main()
