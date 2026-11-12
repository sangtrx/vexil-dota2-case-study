#!/usr/bin/env python3
"""Reproducible RETROSPECTIVE evaluation of already-frozen predictions.

No training. No API calls. No new blind cohorts. Every 28-model output
from PR #6 is preserved, never used to promote a model.
"""
from __future__ import annotations
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"research/results"
OUT=ROOT/"research/bible/results"
CACHE=Path("/home/ai-agent/.cache/vexil-real-data-20261113")
SEED=20261113
EPS=1e-15
BOOT=3000
MODEL_IDS=["M1_time_value"]+[f"P{i:02d}" for i in range(1,29)]

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def load_inputs():
    data=pd.read_csv(SOURCE/"dev_validation_predictions_28.csv")
    manifest=pd.read_csv(CACHE/"vexil_takehome_outputs/match_manifest.csv",
                         usecols=["match_id","start_time","patch","series_id","partition"])
    scores=pd.read_csv(SOURCE/"all_28_candidate_scores.csv")
    assert len(data)==3784 and data.match_id.nunique()==103
    assert len(manifest)==500 and set(manifest.partition)=={"train","validation","test"}
    assert len(scores)==29 and set(scores.model)==set(MODEL_IDS)
    assert set(data.match_id)==set(manifest.loc[manifest.partition=="validation","match_id"])
    assert set(data.columns).issuperset("p_"+x for x in MODEL_IDS)
    assert data.partition.eq("validation").all()
    assert data.groupby("match_id").radiant_win.nunique().eq(1).all()
    assert data.groupby("match_id").minute.min().eq(0).all()
    assert data.groupby("match_id").apply(lambda g:(np.diff(np.sort(g.minute))==1).all(),include_groups=False).all()
    val=manifest[manifest.partition=="validation"][["match_id","start_time","patch","series_id"]]
    data=data.merge(val,on=["match_id","series_id"],how="left",validate="many_to_one")
    assert data.start_time.notna().all()
    pred=data[["p_"+x for x in MODEL_IDS]].to_numpy(float)
    assert np.isfinite(pred).all() and np.all((pred>=0)&(pred<=1))
    y=data.radiant_win.to_numpy(dtype=int)
    assert set(y).issubset({0,1})
    p=np.clip(pred,EPS,1-EPS)
    ll=-(y[:,None]*np.log(p)+(1-y[:,None])*np.log1p(-p))
    br=(pred-y[:,None])**2
    check=scores.set_index("model")
    for i,model in enumerate(MODEL_IDS):
        assert abs(ll[:,i].mean()-check.loc[model,"logloss"])<1e-12,model
        assert abs(br[:,i].mean()-check.loc[model,"brier"])<1e-12,model
    assert abs(check.loc["P20","delta_ll_vs_M1"]+0.0052478275179806836)<1e-12
    return data,manifest,scores,ll,br

def groups_and_blocks(data):
    unique=data[["match_id","start_time","series_id"]].drop_duplicates().copy()
    assert len(unique)==103
    unique["key"]=np.where(unique.series_id.astype(int)>0,"s"+unique.series_id.astype(str),
                           "m"+unique.match_id.astype(str))
    group=unique.groupby("key",sort=False).agg(
        start_time=("start_time","min"),last_time=("start_time","max"),
        matches=("match_id","size")).reset_index()
    group=group.sort_values(["start_time","key"],kind="mergesort").reset_index(drop=True)
    assert len(group)==53, len(group)
    for block,subset in enumerate(np.array_split(group.index.to_numpy(),6),1):
        group.loc[subset,"block"]=block
    unique=unique.merge(group[["key","block"]],on="key",validate="many_to_one")
    result=data.merge(unique[["match_id","key","block"]],on="match_id",validate="many_to_one")
    return result,group,unique

def weighted_metrics(data,model_losses,model_briers):
    # One row per match with per-match mean proper losses, for both estimands.
    meta=data[["match_id","key","block"]].drop_duplicates().set_index("match_id")
    ll=pd.DataFrame(model_losses,columns=MODEL_IDS)
    ll["match_id"]=data.match_id.values
    br=pd.DataFrame(model_briers,columns=MODEL_IDS)
    br["match_id"]=data.match_id.values
    llmatch=ll.groupby("match_id").mean().join(meta)
    brmatch=br.groupby("match_id").mean().join(meta)
    series_ll=llmatch.groupby("key")[MODEL_IDS].mean()
    series_br=brmatch.groupby("key")[MODEL_IDS].mean()
    base=MODEL_IDS.index("M1_time_value")
    rankings=[]
    for j,m in enumerate(MODEL_IDS):
        rankings.append({
            "model":m,
            "minute_ll":float(model_losses[:,j].mean()),
            "equal_match_ll":float(llmatch[m].mean()),
            "equal_series_ll":float(series_ll[m].mean()),
            "minute_brier":float(model_briers[:,j].mean()),
            "equal_match_brier":float(brmatch[m].mean()),
            "equal_series_brier":float(series_br[m].mean()),
            "minute_dll_vs_M1":float(model_losses[:,j].mean()-model_losses[:,base].mean()),
            "equal_match_dll_vs_M1":float(llmatch[m].mean()-llmatch["M1_time_value"].mean()),
            "equal_series_dll_vs_M1":float(series_ll[m].mean()-series_ll["M1_time_value"].mean())
        })
    return pd.DataFrame(rankings),llmatch,brmatch

def block_stability(llmatch,group):
    rows=[]
    blocks=sorted(llmatch.block.unique())
    assert blocks==[1,2,3,4,5,6]
    for block in blocks:
        frame=llmatch.loc[llmatch.block==block]
        avg=frame[MODEL_IDS].mean()
        winner=min(MODEL_IDS,key=lambda m:(float(avg[m]),m))
        for m in MODEL_IDS:
            rows.append({"block":int(block),"games":len(frame),"model":m,
                        "mean_ll":float(avg[m]),
                        "delta_vs_m1":float(avg[m]-avg["M1_time_value"]),
                        "winner_in_block":m==winner})
    return pd.DataFrame(rows)

def cscv_style_rank_reversal(llmatch):
    # NOT the textbook strategy PBO: forecasts already trained, labeled
    # development val already viewed, 6 dependent time blocks.
    rows=[]
    for n,combo in enumerate(itertools.combinations(range(1,7),3),1):
        ismask=llmatch.block.isin(combo)
        ins=llmatch.loc[ismask,MODEL_IDS].mean()
        oos=llmatch.loc[~ismask,MODEL_IDS].mean()
        selected=min(MODEL_IDS,key=lambda m:(float(ins[m]),m))
        sorted_oos=sorted(MODEL_IDS,key=lambda m:(float(oos[m]),m))
        oos_rank=sorted_oos.index(selected)+1
        rows.append({
            "split":n,"in_sample_blocks":",".join(map(str,combo)),
            "out_sample_blocks":",".join(map(str,sorted(set(range(1,7))-set(combo)))),
            "IS_games":int(ismask.sum()),"OOS_games":int((~ismask).sum()),
            "IS_winner":selected,"IS_winner_loss":float(ins[selected]),
            "OOS_winner_loss":float(oos[selected]),
            "OOS_M1_loss":float(oos["M1_time_value"]),
            "OOS_winner_minus_M1":float(oos[selected]-oos["M1_time_value"]),
            "OOS_rank":oos_rank,
            "worse_than_panel_median":int(oos_rank>15),
            "OOS_top_model":sorted_oos[0]
        })
    return pd.DataFrame(rows)

def oob_stability(data,ll):
    # Use each series/singleton as the independent bootstrap block.
    key=data.key.to_numpy(str)
    group_ids,groups=pd.factorize(key,sort=True)
    assert len(groups)==53
    n=np.bincount(group_ids,minlength=len(groups)).astype(float)
    sums=np.stack([
        np.bincount(group_ids,weights=ll[:,j],minlength=len(groups))
        for j in range(len(MODEL_IDS))
    ],axis=1)
    rng=np.random.default_rng(SEED)
    rows=[]
    for t in range(BOOT):
        chosen=rng.integers(0,len(groups),size=len(groups))
        counts=np.bincount(chosen,minlength=len(groups))
        ins=counts @ sums
        winner=min(range(len(MODEL_IDS)),key=lambda j:(ins[j],MODEL_IDS[j]))
        omitted=np.where(counts==0)[0]
        if len(omitted)==0:continue
        oob=sums[omitted].sum(axis=0)/n[omitted].sum()
        rows.append({
            "draw":t+1,"winner_IS":MODEL_IDS[winner],
            "IS_unique_groups":int(np.count_nonzero(counts)),
            "OOB_groups":len(omitted),
            "OOB_minute_rows":int(n[omitted].sum()),
            "OOB_winner_minus_M1":float(oob[winner]-oob[0]),
            "OOB_winner_worse_M1":int(oob[winner]>oob[0])
        })
    return pd.DataFrame(rows)

def p20_influence(data,ll,br):
    j=MODEL_IDS.index("P20")
    dll=ll[:,j]-ll[:,0]
    dbr=br[:,j]-br[:,0]
    f=data[["match_id","key","minute","block","patch"]].copy()
    f["dll"]=dll
    f["dbr"]=dbr
    bymatch=f.groupby(["match_id","key"],sort=True).agg(
        minutes=("minute","size"),sum_dll=("dll","sum"),mean_dll=("dll","mean"),
        sum_dbr=("dbr","sum")).reset_index()
    byseries=f.groupby("key",sort=True).agg(
        minutes=("minute","size"),games=("match_id","nunique"),
        sum_dll=("dll","sum"),mean_dll=("dll","mean")).reset_index()
    total=float(dll.sum())
    n=len(f)
    byseries["leave_series_out_dll"]=(total-byseries.sum_dll)/(n-byseries.minutes)
    byseries["contribution_to_total_dll"]=byseries.sum_dll/n
    phase=np.select([f.minute<=9,f.minute<=19,f.minute<=29],
                    ["0-9","10-19","20-29"],default="30+")
    f["phase"]=phase
    phases=f.groupby("phase",sort=True).agg(
        minute_rows=("dll","size"),games=("match_id","nunique"),
        delta_ll=("dll","mean"),delta_brier=("dbr","mean")).reset_index()
    return bymatch,byseries,phases

def main():
    data,meta,scores,ll,br=load_inputs()
    data,group,one=groups_and_blocks(data)
    ranking,llmatch,brmatch=weighted_metrics(data,ll,br)
    blocks=block_stability(llmatch,group)
    cscv=cscv_style_rank_reversal(llmatch)
    # 20 directional folds are only TEN complementary pairs.
    # Pair label is canonical: earlier of the two 3-block masks.
    def pair_key(block_text):
        selected=tuple(sorted(int(x) for x in block_text.split(",")))
        other=tuple(sorted(set(range(1,7))-set(selected)))
        return ",".join(map(str,min(selected,other)))
    cscv["complement_pair"]=cscv.in_sample_blocks.map(pair_key)
    pairs=cscv.groupby("complement_pair",sort=True).agg(
        directions=("split","size"),
        directions_selected_worse_M1=("OOS_winner_minus_M1",lambda x:int((x>0).sum())),
        directions_rank_below_median=("worse_than_panel_median","sum")
    ).reset_index()
    assert len(pairs)==10 and pairs.directions.eq(2).all()
    oob=oob_stability(data,ll)
    per_match,per_series,phases=p20_influence(data,ll,br)
    assert len(cscv)==20 and len(oob)==BOOT and len(ranking)==29
    assert (cscv.OOS_rank.between(1,29)).all()
    assert (oob.OOB_groups>0).all()
    assert (ranking.loc[ranking.model=="P20","minute_dll_vs_M1"].iloc[0]<0)
    OUT.mkdir(parents=True,exist_ok=True)
    artifacts={
        "all_estimator_weights.csv":ranking,
        "time_blocks.csv":group,
        "block_model_scores.csv":blocks,
        "cscv_20_selections.csv":cscv,
        "cscv_10_complementary_pairs.csv":pairs,
        "series_oob_3000_selection.csv":oob,
        "p20_match_influence.csv":per_match,
        "p20_series_influence.csv":per_series,
        "p20_phase_sensitivity.csv":phases,
        "validation_manifest_for_kaggle.csv":one[["match_id","start_time","series_id","key","block"]]
    }
    for name,table in artifacts.items():
        table.to_csv(OUT/name,index=False)
    worst=per_series.sort_values("sum_dll").head(5)
    summary={
        "research_kind":"posthoc_development_stress; not new holdout and not official PBO",
        "source_bible_main_sha":"8e6374c8ac8c62da6611104555ce98f1cf40a528",
        "input_predictions_sha256":sha(SOURCE/"dev_validation_predictions_28.csv"),
        "input_scores_sha256":sha(SOURCE/"all_28_candidate_scores.csv"),
        "input_match_manifest_sha256":sha(CACHE/"vexil_takehome_outputs/match_manifest.csv"),
        "seed":SEED,"group_bootstrap_draws":BOOT,"models":len(MODEL_IDS),
        "validation_games":data.match_id.nunique(),"validation_series":len(group),
        "validation_minute_rows":len(data),
        "audit_source_sha256":sha(Path(__file__)),
        "cscv_style_split_count":len(cscv),
        "cscv_complementary_pair_count":len(pairs),
        "cscv_style_worse_half_count":int(cscv.worse_than_panel_median.sum()),
        "cscv_style_worse_half_fraction":float(cscv.worse_than_panel_median.mean()),
        "cscv_style_selected_worse_than_m1_fraction":float((cscv.OOS_winner_minus_M1>0).mean()),
        "oob_selected_worse_than_m1_fraction":float(oob.OOB_winner_worse_M1.mean()),
        "oob_selected_worse_given_non_m1":float(
            oob.loc[oob.winner_IS!="M1_time_value","OOB_winner_worse_M1"].mean()),
        "oob_m1_selected_count":int((oob.winner_IS=="M1_time_value").sum()),
        "oob_non_m1_selection_count":int((oob.winner_IS!="M1_time_value").sum()),
        "oob_delta_ll_mean":float(oob.OOB_winner_minus_M1.mean()),
        "oob_delta_ll_median":float(oob.OOB_winner_minus_M1.median()),
        "oob_delta_ll_q05":float(oob.OOB_winner_minus_M1.quantile(.05)),
        "oob_delta_ll_q95":float(oob.OOB_winner_minus_M1.quantile(.95)),
        "oob_conditional_rate_naive_mc_se_not_population_se":float(
            np.sqrt(oob.OOB_winner_worse_M1.mean()*
                    (1-oob.OOB_winner_worse_M1.mean())/len(oob))),
        "oob_p20_is_selected_frequency":float((oob.winner_IS=="P20").mean()),
        "oob_m1_is_selected_frequency":float((oob.winner_IS=="M1_time_value").mean()),
        "p20_leave_one_series_out_dll_min":float(per_series.leave_series_out_dll.min()),
        "p20_leave_one_series_out_dll_max":float(per_series.leave_series_out_dll.max()),
        "p20_minute_weighted_dll":float(ranking.loc[ranking.model=="P20","minute_dll_vs_M1"].iloc[0]),
        "p20_equal_match_dll":float(ranking.loc[ranking.model=="P20","equal_match_dll_vs_M1"].iloc[0]),
        "p20_equal_series_dll":float(ranking.loc[ranking.model=="P20","equal_series_dll_vs_M1"].iloc[0]),
        "no_model_fit":True,"no_api_calls":True,
        "new_independent_holdout_games":0,"screening_result_unchanged":"0 of 28 passed; M1 retained"
    }
    for name in artifacts:
        summary["sha256_"+name]=sha(OUT/name)
    (OUT/"stability_receipt.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print("BIBLE_STABILITY_AUDIT_COMPLETE",json.dumps({k:v for k,v in summary.items() if not k.startswith("sha256_") and not k.startswith("input_")},sort_keys=True),flush=True)
    print("P20_P08_M1_ESTIMANDS")
    print(ranking[ranking.model.isin(["M1_time_value","P20","P08"])].round(6).to_string(index=False))
    print("P20_PHASES")
    print(phases.round(6).to_string(index=False))
    print("SELECTION_RANK_REVERSAL")
    print(cscv.groupby("IS_winner").agg(n=("split","size"),
          worse_half=("worse_than_panel_median","sum"),
          OOS_delta_vs_M1=("OOS_winner_minus_M1","mean")).round(6).to_string())
    print("OOB_WINNERS",oob.winner_IS.value_counts().head(8).to_dict())

if __name__=="__main__":
    main()
