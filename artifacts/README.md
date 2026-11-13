# Frozen evaluation output

[heldout_predictions.csv](heldout_predictions.csv) contains **3,837** minute-level forecasts for **106** held-out professional Dota 2 games. The five columns are match_id, minute, p_model, p_baseline, and radiant_win.

This is the unchanged BigLinux V4 output from the frozen notebook, not a replacement data source and not an input to training, selection, or execution. The identical data were independently reproduced by the private Kaggle V4 cold run with differences at floating-point roundoff (maximum absolute delta 4.44e-16).

- Executed notebook SHA-256: dd1d0a6ffd37f1f609451684e6d848d124dfa2fddbbc720c470513144fbf34bb
- This CSV SHA-256: e3b2c843172fdde029f5f5ec05536ea837ec023b8b860543cadedf028bb3cb32
- The complete notebook re-exports the CSV after Run All; it does not read it.

The labels and forecasts are retrospective research output. This file does not establish a live inference feed or an independent new holdout.
