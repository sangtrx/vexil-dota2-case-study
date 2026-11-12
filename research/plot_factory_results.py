#!/usr/bin/env python3
"""Render honest top-eight exploratory model ranking with adjusted uncertainty."""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'research/results/all_28_candidate_scores.csv'
DEST=ROOT/'research/results/exploratory_top8_forest.png'

def main():
    full=pd.read_csv(DATA)
    best=full.loc[full.model!='M1_time_value'].sort_values('logloss').head(8)
    y=np.arange(len(best))
    fig,ax=plt.subplots(figsize=(10.5,5.4),constrained_layout=True)
    center=best.delta_ll_vs_M1.to_numpy()
    lower=best.maxT_familywise95_low.to_numpy()
    upper=best.maxT_familywise95_high.to_numpy()
    ax.errorbar(center,y,xerr=np.vstack((center-lower,upper-center)),
                fmt='o',capsize=3,linewidth=1.35)
    ax.axvline(0,linestyle='--',alpha=.8)
    ax.axvline(-.005,linestyle=':',alpha=.8)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{r.model} — {r.title}" for r in best.itertuples()],fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel('Minute-weighted validation log-loss difference vs M1 (negative = better)')
    ax.set_title('28 preregistered hypotheses — top 8 point estimates, all FAIL the advancement gate',
                 fontsize=11)
    ax.grid(True,axis='x',alpha=.2)
    fig.text(.01,-.045,
      'Whiskers: paired 95% MAX-T intervals simultaneously adjusted for all 28 hypotheses. Previously inspected 103-game validation; no fresh test.',
      fontsize=8.4)
    fig.savefig(DEST,dpi=165,bbox_inches='tight',facecolor='white')
    plt.close(fig)
    print('PLOT_RENDERED',DEST,DEST.stat().st_size)

if __name__=='__main__':main()
