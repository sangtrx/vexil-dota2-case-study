"""Synthetic acceptance-gate contract tests. No real cloud is claimed."""
from __future__ import annotations
import copy
import json
import tempfile
import shutil
import unittest
from pathlib import Path

import nbformat
import pandas as pd

from research.verify_hosted_run import (
    SOURCE_FIELDS, RECEIPT_FIELDS, TABLES,
    compare_notebook, compare_tables, verify,
)


class HostedRunVerificationTest(unittest.TestCase):
    def test_frozen_csv_parity_and_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            local=base/"local";remote=base/"cloud"
            local.mkdir();remote.mkdir()
            for name in TABLES:
                data=pd.DataFrame({"match_id":[1,2], "score":[.4,.6],
                                   "note":["a","b"]})
                data.to_csv(local/name,index=False)
                data.to_csv(remote/name,index=False)
            result=compare_tables(local,remote)
            self.assertEqual(len(result),8)
            df=pd.read_csv(remote/"heldout_predictions.csv")
            df.loc[0,"score"]+=.01
            df.to_csv(remote/"heldout_predictions.csv",index=False)
            with self.assertRaisesRegex(ValueError,"numeric drift"):
                compare_tables(local,remote)

    def test_saved_hosted_notebook_source_and_visuals(self):
        actual = Path(__file__).resolve().parents[1] / "live_dota2_win_probability.ipynb"
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            a, b = base/"a.ipynb", base/"b.ipynb"
            shutil.copy2(actual, a)
            shutil.copy2(actual, b)
            good = compare_notebook(a, b)
            self.assertEqual(good["executed_code_cells"], 14)
            self.assertEqual(good["embedded_pngs"], 4)

            edited = nbformat.read(str(b), as_version=4)
            edited.cells[20].source += "\n# stealth change"
            nbformat.write(edited, str(b))
            with self.assertRaisesRegex(ValueError, "source differs"):
                compare_notebook(a, b)

            edited = nbformat.read(str(a), as_version=4)
            edited.cells[15].outputs = []
            nbformat.write(edited, str(b))
            with self.assertRaisesRegex(ValueError, "Missing saved PNG"):
                compare_notebook(a, b)

    def test_runtime_and_cold_retrieval_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            local=base/"local";remote=base/"hosted"
            local.mkdir();remote.mkdir()
            for name in TABLES:
                v=pd.DataFrame({"id":[1], "p":[.45]})
                v.to_csv(local/name,index=False)
                v.to_csv(remote/name,index=False)
            a={name:"x"*64 for name in SOURCE_FIELDS}
            a.update({name:123 for name in RECEIPT_FIELDS})
            a.update(matches=500,minute_rows=18304,
                     model_selected_on_validation="M1_time_value",
                     runtime={"colab_detected":False,"kaggle_detected":False},
                     retrieval={"api_calls":0,"cache_hits":500,
                                "candidate_exclusions":0})
            b=copy.deepcopy(a)
            b["runtime"]={"colab_detected":True,"kaggle_detected":False}
            b["retrieval"]={"api_calls":500,"cache_hits":0,
                            "candidate_exclusions":0}
            (local/"derived_run_receipt.json").write_text(json.dumps(a))
            (remote/"derived_run_receipt.json").write_text(json.dumps(b))
            notebook=base/"both.ipynb"
            shutil.copy2(Path(__file__).resolve().parents[1] /
                         "live_dota2_win_probability.ipynb", notebook)
            accepted=verify(local,remote,notebook,notebook,"colab")
            self.assertEqual(accepted["outcome"],"NUMERICAL_AND_SAVED_SOURCE_PARITY_PASS")
            b["runtime"]={"colab_detected":False,"kaggle_detected":True}
            (remote/"derived_run_receipt.json").write_text(json.dumps(b))
            with self.assertRaisesRegex(ValueError,"runtime"):
                verify(local,remote,notebook,notebook,"colab")
            b["runtime"]={"colab_detected":True,"kaggle_detected":False}
            b["retrieval"]["cache_hits"]=500
            (remote/"derived_run_receipt.json").write_text(json.dumps(b))
            with self.assertRaisesRegex(ValueError,"fresh OpenDota"):
                verify(local,remote,notebook,notebook,"colab")


if __name__=="__main__":
    unittest.main()
