#!/usr/bin/env python3
"""Pure post-run reporting and complete negative-result archive.

Reads the one-shot saved output; NEVER refits, rescores a hidden test,
alters thresholds, downloads data, or changes the selected model.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
CACHE=Path('/home/ai-agent/.cache/vexil-proposal-factory-20261113')
DEST=ROOT/'research/results'
REPORT=ROOT/'docs/PROPOSAL_FACTORY_RESULTS.md'
NUM=28

def fnum(x,nd=6):
    return f"{float(x):.{nd}f}"

def main():
    receipt=json.loads((CACHE/'screen_receipt.json').read_text())
    lock=json.loads((CACHE/'screen_consumed.lock.json').read_text())
    frozen=json.loads((ROOT/'research/proposal_registry_manifest.json').read_text())
    assert receipt['candidate_count']==frozen['proposal_count']==NUM
    assert receipt['source_git_head']==lock['source_git_head']
    assert receipt['source_git_head']=='bc134daa6f8db0ad8e090f2102d694b700eb5f67'
    assert receipt['registry_sha256']==frozen['registry_sha256']
    assert receipt['num_passed']==0 and receipt['selected_for_fresh_confirmation'] is None
    assert receipt['train_games']==291 and receipt['validation_games']==103
    assert all(receipt[key]==0 for key in ('original_test_games_accessed',
              'first_forward_test_games_accessed','second_forward_test_games_accessed'))

    scored=pd.read_csv(CACHE/'all_28_candidate_scores.csv')
    folds=pd.read_csv(CACHE/'train_only_3fold_scores.csv')
    phase=pd.read_csv(CACHE/'calibration_and_phase_scores.csv')
    ci=pd.read_csv(CACHE/'familywise_simultaneous_ci.csv')
    val=pd.read_csv(CACHE/'dev_validation_predictions_28.csv')
    assert scored.model.nunique()==29 and len(scored)==29
    assert folds.model.nunique()==29 and len(folds)==29*3
    assert len(phase)==29*5
    assert ci.model.nunique()==28
    assert len(val)==3784 and val.match_id.nunique()==103
    assert scored.loc[scored.model=='M1_time_value','logloss'].iloc[0] >0.519345
    assert scored.loc[scored.model=='M1_time_value','logloss'].iloc[0] <0.519347
    assert not scored.passes_exploratory_screen.any()

    # Keep byte-identical copies of the derived outputs, including failures.
    DEST.mkdir(parents=True,exist_ok=True)
    output_files=[
        'all_28_candidate_scores.csv','train_only_3fold_scores.csv',
        'familywise_simultaneous_ci.csv','calibration_and_phase_scores.csv',
        'dev_validation_predictions_28.csv','screen_consumed.lock.json','screen_receipt.json'
    ]
    digests={}
    for name in output_files:
        raw=(CACHE/name).read_bytes()
        (DEST/name).write_bytes(raw)
        digests[name]=hashlib.sha256(raw).hexdigest()

    cards=DEST/'outcomes'
    cards.mkdir(exist_ok=True)
    bycard={card['id']:card for card in frozen['cards']}
    for row in scored.to_dict('records'):
        mid=row['model']
        if mid=='M1_time_value':continue
        info=bycard[mid]
        alone=folds[folds.model==mid].sort_values('fold')
        path=cards/(mid+'.md')
        content=f"""# {mid} — {row['title']}

**Exploratory model screen: {'PASS' if row['passes_exploratory_screen'] else 'FAIL'}.**
Registered card: [{mid}]({ROOT.name and '../../proposals/'+Path(info['file']).name}).
No independent holdout was opened for this candidate.

Family: {row['family']}. Model: {row['algorithm']}.
Columns: {int(row['column_count'])}; additional registered features: {', '.join(info['new_features']) or 'none (shape only)'}.

| Metric | This model | Fixed M1 comparator | Difference (candidate−M1) |
|---|---:|---:|---:|
| Validation log loss | {fnum(row['logloss'])} | 0.519346 | {fnum(row['delta_ll_vs_M1'])} |
| Validation Brier | {fnum(row['brier'])} | 0.175767 | {fnum(row['delta_brier_vs_M1'])} |
| Equal-match-weighted log loss difference | — | — | {fnum(row['equal_match_mean_delta_ll'])} |

Paired validation whole-series CI (unadjusted):
[{fnum(row['paired_percentile95_low'])}, {fnum(row['paired_percentile95_high'])}].
Familywise 95% simultaneous MAX-T interval against M1 among all {NUM} hypotheses:
**[{fnum(row['maxT_familywise95_low'])}, {fnum(row['maxT_familywise95_high'])}]**.

Three predeclared chronological series-safe train-only folds
(delta log loss, negative favors candidate):
{', '.join(f'{fnum(r.delta_ll_vs_M1)}' for r in alone.itertuples())}.
Favorable direction in **{int(row['favorable_train_folds'])}/3**.

**Decision:** This historical validation set was already inspected in
earlier research. Even a low point estimate is NOT new blinded evidence.
No candidate is promoted merely for lower log loss; a future fresh
confirmation is required. Results for ALL 28 proposals are retained
to prevent selective reporting.
"""
        path.write_text(content)
    rank=scored[scored.model!='M1_time_value'].sort_values('logloss')
    lines=[]
    for r in rank.itertuples():
        lines.append("| "+str(r.model)+" | "+str(r.family)+" | "+
            fnum(r.logloss)+" | "+fnum(r.brier)+" | "+
            fnum(r.delta_ll_vs_M1)+" | "+
            fnum(r.maxT_familywise95_high)+" | "+
            str(int(r.favorable_train_folds))+"/3 | NO |")
    top=rank.iloc[0]
    m1=scored[scored.model=='M1_time_value'].iloc[0]
    top_phase=phase[phase.model.isin(['M1_time_value',top.model])]
    pivot=top_phase.pivot(index='phase',columns='model',values='logloss')
    phase_lines=[]
    for seg in ('overall','0-9','10-19','20-29','30+'):
        phase_lines.append("| "+seg+" | "+
                fnum(pivot.loc[seg,'M1_time_value'])+" | "+
                fnum(pivot.loc[seg,top.model])+" | "+
                fnum(pivot.loc[seg,top.model]-pivot.loc[seg,'M1_time_value'])+" |")
    ftop=folds[folds.model==top.model].sort_values('fold')
    screener=(
        "The top candidate achieved the point-estimate loss threshold."
        if top.delta_ll_vs_M1<=-.005 else
        "Even the top candidate missed the point-estimate loss threshold."
    )
    output=f"""# Vexil proposal factory — all 28 outcomes, including failures
**13 November 2026 · one-shot exploratory screen · DO NOT PROMOTE**

## Registered before outcomes

- Proposal cards: research/proposals/P01...P28; registry SHA256:
  {receipt['registry_sha256']}.
- Immutable code and screen-registration commit:
  {receipt['source_git_head']}.
- Source: original 500-match OpenDota cache, **291 training games**
  and **103 previously inspected validation games**. No external datasets
  or endpoints were introduced. None of the original 106-match test,
  first 200-match forward test or second 200-match gate-confirmation
  test labels were loaded in this 28-model evaluation.
- The feature builder passed **{receipt['pit_checks']:,}** real
  prefix-truncation, endpoint-cutoff and postgame-label poison checks
  on all 394 development games. Earlier separate audits checked
  900 cached games and 32,106 clock/gold-sum indexes.
- **28 hypotheses** fixed; three train-only chronological, series-safe
  folds; one full 291-train vs 103-validation comparison per model;
  log loss, Brier, per-game sensitivity, ECE/phase reporting.
- **5,000** paired **series-or-singleton** block bootstraps across
  **53 clusters**, using ONE simultaneous 95% max-|t| familywise
  adjustment over all 28 candidate-minus-M1 differences.
  This attempts to control the finite search family but does not
  repair earlier adaptive reuse of the same validation outcomes.

## Verdict

**0 of 28 models met the complete precommitted advancement screen.**
The original M1 gold×time remains the selected take-home model.
No new blind cohort is needed, and NO existing consumed test set
was opened to rescue a seemingly strong candidate.

The best point estimate was **{top.model} ({top.title})**,
log loss **{fnum(top.logloss)}** vs M1 **{fnum(m1.logloss)}**:
difference **{fnum(top.delta_ll_vs_M1)}**. Its Brier was
{fnum(top.brier)} vs {fnum(m1.brier)}. {screener}
But only **{int(top.favorable_train_folds)}/3** earlier training-only
time folds favored it; the simultaneous 95% upper bound was
**{fnum(top.maxT_familywise95_high)}**, above zero. Both the
ordinary paired CI [{fnum(top.paired_percentile95_low)},
{fnum(top.paired_percentile95_high)}] and adjusted interval
[{fnum(top.maxT_familywise95_low)},
{fnum(top.maxT_familywise95_high)}] span zero. **HOLD.**

Earlier training-only fold deltas for {top.model}
(negative is better):
{', '.join(f'{fnum(r.delta_ll_vs_M1)}' for r in ftop.itertuples())}.
The fixed non-parametric phase score table below is DESCRIPTIVE
because it uses the same previously inspected 103 validation games.

| Phase | M1 log loss | {top.model} log loss | {top.model}−M1 |
|---|---:|---:|---:|
{chr(10).join(phase_lines)}

## Full 28-way ranking (all candidates retained)

Positive candidate-minus-M1 log loss is WORSE, and a positive
adjusted upper interval bound is insufficient for evidence
of improvement. The fold count is a direction check, not a p-value.

| ID | Family | Log loss ↓ | Brier ↓ | Δlogloss vs M1 | MAX-T upper 95% | favorable folds | passes |
|---|---|---:|---:|---:|---:|---|---|
{chr(10).join(lines)}

Reference M1: log loss {fnum(m1.logloss)}, Brier
{fnum(m1.brier)}; P22 high-dimensional hero one-hot scored
substantially WORSE than M1. This is consistent with risk from
fitting 160 signed hero indicators on only 291 independent
training games replicated over many correlated minute rows;
it is NOT proof hero drafts lack predictive value.

## Scientific interpretation

1. **P20 item-purchase events** produce the most encouraging
   validation point difference, but the sign reverses in
   training-only forward folds, and both unadjusted and familywise
   confidence intervals include zero. Purchase-log entries are
   a proxy for reported item acquisition, NOT verified inventory
   possession or live network receipt.
2. **P08 economic distribution** has the second-best validation
   point estimate but performed worse than M1 in **all three
   earlier train-only folds**. This is exactly the false-positive
   pattern a large idea search can create.
3. **P15 recent kills** favors M1 less consistently; it does not
   meet the practical gain or uncertainty criterion. Its events
   may largely be reflected in gold/XP.
4. Shallow tree models, additive B-splines and a raw
   hero-identity model were not rewarded with a compelling
   gain; network capacity is not scientific novelty.
5. Some predictors overlap negative feature experiments
   already explored in separate PR #4 and #5. This factory
   DOES NOT make those old validations independent.

## Code, lineage and stopping rule

- research/execute_proposal_factory.py — single screen, fixed
  familywise selection rule; no model search grid or hidden test.
- research/proposal_factory_features.py — 201 feature columns,
  all fields strictly from OpenDota observations through minute t.
- research/proposal_factory_registry.py — frozen 28-hypothesis spec.
- research/results/all_28_candidate_scores.csv — full-precision
  metrics, Brier, equal-match sensitivity, familywise bounds.
- research/results/train_only_3fold_scores.csv — 87 recorded rows
  (29 models including M1 × 3 folds).
- research/results/calibration_and_phase_scores.csv — 145 rows,
  all 29 models × five phases; fixed-bin descriptive ECE.
- research/results/dev_validation_predictions_28.csv —
  3,784 validation minute rows × 29 probability series, with
  match/series IDs, minutes and observed labels; PRIVATE repo only.
- research/results/screen_receipt.json and lock.json — code
  registration, source SHA, exact input split and STOP result.
- research/results/outcomes/P01...P28 — individual unfiltered
  model verdicts so no failed proposal disappears from view.

**Do not ship any of P01–P28 on the present evidence.**
The statistically defensible next move is to formulate ONE
narrower hypothesis with independently observable item life
cycle or stronger team-state semantics, register it prospectively,
and verify it on a genuinely fresh later cohort ONLY after
a strong development screen. It may still be negative.

The original notebook and ≤4-page take-home REPORT.md in
Draft PR #3 remain unchanged and separately submission-ready
only after their own outstanding Colab and human-hours checks.
"""
    REPORT.write_text(output)
    (DEST/'archive_checksums.json').write_text(json.dumps({
        'files':digests,'registered_git_head':receipt['source_git_head'],
        'results_document_sha256':hashlib.sha256(output.encode()).hexdigest(),
        'score_rows':len(scored),'fold_rows':len(folds),
        'calibration_phase_rows':len(phase),'probability_rows':len(val),
        'num_outcome_cards':len(list(cards.glob('P*.md'))),
        'all_decisions_hold':not scored.passes_exploratory_screen.any()
    },sort_keys=True,indent=2)+'\n')
    print('FACTORY_REPORT_RENDERED',
          {'report_words':len(output.split()),'proposal_outcomes':len(list(cards.glob('P*.md'))),
           'records':len(scored),'calibration':len(phase),
           'num_passed':receipt['num_passed'],'top_id':top.model})

if __name__=='__main__':main()
