# Prior-art audit: live Dota 2 win probability (13 November 2026)

## What already exists and cannot be claimed as original

| Prior work | What was demonstrated or implemented | Implication for this take-home |
|---|---|---|
| Hodge et al., IEEE Transactions on Games, 2021, DOI:10.1109/TG.2019.2948469 | Live win prediction on professional DotA 2 with standard ML and engineered features | Real-time prediction, pro-match context, and feature engineering are NOT new research claims |
| Akhmedov and Phan, 2021, arXiv:2106.01782 | Dota outcome prediction with linear, neural and LSTM models based on real-time telemetry | LSTM and temporal input alone do NOT establish novelty |
| Bapela, Ranchod and Ingram, AIIDE 2025, DOI:10.1609/aiide.v21i1.36822 | Real-time chat and game-event prediction, LSTM and DistilBERT; large ranked-match dataset | Kill and event logs, even natural language chat, have been explored |
| Dota 2 Match Outcome Prediction System Using Decision Tree Ensemble Algorithms, Big Data and Cognitive Computing, 2025, DOI:10.3390/bdcc9120302 | Phase segmentation and hero/item signals in decision-tree ensembles | Early/mid/late phase models and hero/item context are not intrinsically novel. Published accuracy values are NOT comparable to the Vexil per-minute, point-in-time proper-scoring task without checking fields and sampling |
| `amarcu/dota-predictor`, MIT | OpenDota collector, 20-feature per-minute sequences, LSTM, hero embeddings, live GSI dashboard | Copying a 245k-parameter LSTM into a 500-game task creates overfit and provenance risks; only its feature schema ideas are relevant |
| `andriipletinka/dota2-time-slice-win-probability-prediction` | Replay-derived snapshots and Transformer + MLP | A Transformer is not a novelty claim and its replay source conflicts with the two-API-endpoint constraint |
| Luis A. Sanchez Calderon, Zenodo 2026, versions 1–3 (v3 record 23166182) | 90,530 pro matches, 1M snapshots, per-minute gold/XP and purchase features; v3 excluded 1,849 games where time-array position did not equal game-clock time | Time-index alignment audits and item features have close prior art. Adapt the PIT audit, but never claim it was invented here. External snapshot data cannot replace 500 OpenDota pulls in the required notebook |
| Chitayat, Block, Walker & Drachen, ACM CHI PLAY 2024, DOI:10.1145/3677079 | How Could They Win? frames game-state win conditions, not just outcome-probability forecasting | Broad gold versus objectives and win-condition narratives are prior art. The more specific short-lived event-claim proxy versus irreversible control under PIT is a new hypothesis, not a first win-condition method |
| Wilkinson & Ferro, Calibrated Probability Forecast Sequences and Measure-Valued Martingales, arXiv:2606.31621 (June 2026) | Formal martingale relationships for sequential auto-calibration and statistical tests | The martingale property is NOT our discovery; only its game-time, series-aware diagnostic implementation is specific to this study |
| Hisokaqq/Dota-2-Match-Outcome-Prediction | Pre-draft hero matchup and synergy difference with training-only statistics | Draft features and fold-local historical rates are public prior art, not novelty |
| `interpretml/interpret` (actual GitHub repository `interpretml/interpret`) | Explainable Boosting Machine and glassbox GAM curves | GAMs/EBMs are existing algorithms; useful only as a controlled complexity benchmark and likely underpowered at n=500 |
| `scikit-learn-contrib/MAPIE` | Conformal prediction sets and uncertainty quantification | Conformal methodology is existing prior art and depends on exchangeability. Match-minute rows are NOT independently exchangeable; nominal coverage guarantees must not be claimed without grouped/time-aware conformalization |
| `whanyu1212/gem-dota` | Rich replay parsing, fight/ward/map/buyback state | External replay parsing would violate Vexil's permitted source constraint. Read for design patterns only; DO NOT add it as a source |

## Distinctive hypothesis proposed here (not a priority/novelty claim)

**Ephemeral and irreversible strategic information should not be represented by the same cumulative event counter.** Roshan's pickup/claim generates a *temporary tactical window*; buybacks are an observable short-term resource commitment; structures are irreversible map-state changes. A two-timescale, point-in-time representation of these signals plus a forecast-path coherence audit differs from the specific features and evaluation baselines reviewed above.

**Novelty boundary:** This is an independently formulated research question / feature construction in this repository, not a claim that nobody anywhere has previously used similar features. We did not complete an exhaustive global novelty search, and there is no independently validated predictive improvement yet.

## Sources inspected

- https://pure.york.ac.uk/portal/en/publications/win-prediction-in-multi-player-esports-live-professional-match-pr/
- https://arxiv.org/abs/2106.01782
- https://ojs.aaai.org/index.php/AIIDE/article/view/36822
- https://doi.org/10.3390/bdcc9120302
- https://github.com/amarcu/dota-predictor
- https://github.com/andriipletinka/dota2-time-slice-win-probability-prediction
- https://zenodo.org/records/23166182
- https://doi.org/10.1145/3677079
- https://arxiv.org/abs/2606.31621
- https://github.com/Hisokaqq/Dota-2-Match-Outcome-Prediction
- https://github.com/interpretml/interpret
- https://github.com/scikit-learn-contrib/MAPIE
- https://github.com/whanyu1212/gem-dota
- https://liquipedia.net/dota2/Aegis_of_the_Immortal

The sources are cited for research context and mechanics. Their code is NOT copied. No external match dataset is used in the Vexil submission.
