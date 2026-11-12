#!/usr/bin/env python3
"""Second, differently structured P20 reference: Python stdlib only.

Does not import NumPy/Pandas/scikit-learn, reuse model code, or use the
same bootstrap RNG stream as the factory. Verifies point scores and
makes a distinct, descriptive resampling sensitivity (not a new test).
"""
from __future__ import annotations
import csv
import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"research/bible/results"
DATA=ROOT/"research/results/dev_validation_predictions_28.csv"
REPS=4000

def loss(y,p):
    p=max(1e-15,min(1.0-1e-15,p))
    return -math.log(p) if y==1 else -math.log1p(-p)

def quantile(vals,p):
    vals=sorted(vals)
    x=(len(vals)-1)*p
    lo=int(math.floor(x));hi=int(math.ceil(x))
    return vals[lo]+(vals[hi]-vals[lo])*(x-lo)

def main():
    count=0
    observed_sum=0.0
    brier_delta_sum=0.0
    series=defaultdict(lambda:[0,0.0])
    matches=defaultdict(lambda:[0,0.0])
    with DATA.open(newline="") as f:
        for row in csv.DictReader(f):
            mid=int(row["match_id"])
            sid=int(row["series_id"])
            group=("s"+str(sid)) if sid>0 else ("m"+str(mid))
            y=int(row["radiant_win"])
            assert y in (0,1)
            p0=float(row["p_M1_time_value"])
            p1=float(row["p_P20"])
            d=loss(y,p1)-loss(y,p0)
            bd=(p1-y)*(p1-y)-(p0-y)*(p0-y)
            count+=1;observed_sum+=d;brier_delta_sum+=bd
            series[group][0]+=1
            series[group][1]+=d
            matches[mid][0]+=1
            matches[mid][1]+=d
    assert count==3784 and len(series)==53 and len(matches)==103
    obs=observed_sum/count
    equal_match=sum(s/n for n,s in matches.values())/len(matches)
    by_group=defaultdict(list)
    for mid,vals in matches.items():
        # equal-series weighting is sum of per-match MEANS in each
        # series, not series minute-weighted.
        pass
    series_for_match={}
    with DATA.open(newline="") as f:
        for row in csv.DictReader(f):
            mid=int(row["match_id"]);sid=int(row["series_id"])
            series_for_match[mid]="s"+str(sid) if sid>0 else "m"+str(mid)
    for mid,(n,s) in matches.items():
        by_group[series_for_match[mid]].append(s/n)
    equal_series=sum(sum(x)/len(x) for x in by_group.values())/len(by_group)
    assert abs(obs+0.0052478275179806836)<1e-12
    assert abs(equal_match+0.004491209735395407)<1e-12
    assert abs(equal_series+0.002869279834146532)<1e-12
    # DIFFERENT stdlib RNG, seed and group collection order.
    rng=random.Random(27182818)
    group_items=list(sorted(series.items(),reverse=True))
    gcount=len(group_items)
    samples=[]
    for _ in range(REPS):
        total_n=0;total_d=0.0
        for _ in range(gcount):
            n,s=group_items[rng.randrange(gcount)][1]
            total_n+=n;total_d+=s
        samples.append(total_d/total_n)
    low=quantile(samples,.025);high=quantile(samples,.975)
    original=json.loads((OUT/"stability_receipt.json").read_text())
    assert abs(obs-original["p20_minute_weighted_dll"])<1e-12
    # Not exact parity with the factory bootstrap: different seed,
    # language, ordering and basic-random stream. Loose tolerance only.
    assert low<0<high and -0.018<low<-.006 and -0.005<high<.009
    result={
        "source":"frozen prior-exposed validation predictions",
        "implementation":"Python stdlib csv/math/random, distinct from numpy/vectorized factory",
        "test_kind":"independent arithmetic/reference, NOT independent model evaluation",
        "minute_rows":count,"games":len(matches),"groups":len(series),
        "p20_minus_m1_ll_minute_weighted":obs,
        "p20_minus_m1_ll_equal_match":equal_match,
        "p20_minus_m1_ll_equal_series":equal_series,
        "p20_minus_m1_brier":brier_delta_sum/count,
        "alternative_rng_seed":27182818,
        "series_bootstrap_draws":REPS,
        "alternative_series_percentile95_lower":low,
        "alternative_series_percentile95_upper":high,
        "expected_sign_uncertain":low<0<high,
        "no_new_test_labels":True,"no_training":True
    }
    (OUT/"independent_stdlib_reference_receipt.json").write_text(
        json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("INDEPENDENT_STD_LIB_REFERENCE_PASS",json.dumps(result,sort_keys=True))

if __name__=="__main__":
    main()
