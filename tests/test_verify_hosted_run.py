"""Synthetic acceptance-gate contract tests. No real cloud is claimed."""
from __future__ import annotations
import copy
import json
import tempfile
import shutil
import unittest
from pathlib import Path
from PIL import Image, ImageDraw
from PIL.PngImagePlugin import PngInfo

import nbformat
import pandas as pd

from research.verify_hosted_run import (
    SOURCE_FIELDS, RECEIPT_FIELDS, TABLES, PLOTS,
    compare_notebook, compare_tables, verify, verify_derived_images,
    compare_plot_pixels,
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
            # Kaggle CLI pulls preserve source and execution counts but
            # sometimes strip all rich output media from notebook files.
            stripped = nbformat.read(str(b), as_version=4)
            for cell in stripped.cells:
                if cell.cell_type == "code":
                    cell.outputs = []
            nbformat.write(stripped, str(b))
            with self.assertRaisesRegex(ValueError,"Missing saved PNG"):
                compare_notebook(a, b)
            self.assertEqual(compare_notebook(
                a,b,require_embedded_images=False)["embedded_pngs"],0)
            shutil.copy2(a,b)

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

    def test_plot_comparison_ignores_png_metadata_but_detects_visual_tampering(self):
        chart = Path(__file__).resolve().parents[1] / "docs/figures/heldout_reliability.png"
        with tempfile.TemporaryDirectory() as tmp:
            local, cloud = Path(tmp)/"local", Path(tmp)/"cloud"
            local.mkdir(); cloud.mkdir()
            for name in PLOTS:
                shutil.copy2(chart,local/name)
                shutil.copy2(chart,cloud/name)
            initial=compare_plot_pixels(local,cloud,require_exact=True)
            self.assertTrue(all(x["decoded_pixels_equal"] for x in initial.values()))
            # PNG tEXt chunks and compression bytes may differ across
            # environments even when the rendered chart pixels are identical.
            metadata=PngInfo()
            metadata.add_text("rendered-by","synthetic metadata only")
            with Image.open(local/PLOTS[0]) as img:
                img.save(cloud/PLOTS[0],format="PNG",pnginfo=metadata)
            self.assertNotEqual((local/PLOTS[0]).read_bytes(),
                                (cloud/PLOTS[0]).read_bytes())
            after=compare_plot_pixels(local,cloud,require_exact=True)
            self.assertTrue(after[PLOTS[0]]["decoded_pixels_equal"])
            # A valid, same-sized high-detail chart with tampered visible
            # content must fail even when its container/structure is valid.
            with Image.open(local/PLOTS[1]) as img:
                altered=img.convert("RGB")
                ImageDraw.Draw(altered).rectangle(
                    (80, 80, 300, 170), fill=(255, 0, 0))
                altered.save(cloud/PLOTS[1],format="PNG")
            self.assertGreater((cloud/PLOTS[1]).stat().st_size,10000)
            self.assertFalse(compare_plot_pixels(
                local,cloud)[PLOTS[1]]["decoded_pixels_equal"])
            with self.assertRaisesRegex(ValueError,"pixel content differs"):
                compare_plot_pixels(local,cloud,require_exact=True)

    def test_runtime_and_cold_retrieval_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            local=base/"local";remote=base/"hosted"
            local.mkdir();remote.mkdir()
            for name in TABLES:
                v=pd.DataFrame({"id":[1], "p":[.45]})
                v.to_csv(local/name,index=False)
                v.to_csv(remote/name,index=False)
            chart=Path(__file__).resolve().parents[1] / "docs/figures/heldout_reliability.png"
            for name in PLOTS:
                shutil.copy2(chart,remote/name)
                shutil.copy2(chart,local/name)
            self.assertEqual(len(verify_derived_images(remote)),4)
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
            b["runtime"]={"colab_detected":False,"kaggle_detected":True}
            b["retrieval"]={"api_calls":505,"cache_hits":0,"candidate_exclusions":0}
            (remote/"derived_run_receipt.json").write_text(json.dumps(b))
            # Simulate a Kaggle source-only notebook downloaded by CLI.
            stripped=nbformat.read(str(notebook),as_version=4)
            for cell in stripped.cells:
                if cell.cell_type=="code":cell.outputs=[]
            stripped_file=base/"kaggle_pull.ipynb"
            nbformat.write(stripped,str(stripped_file))
            accepted=verify(local,remote,notebook,stripped_file,"kaggle")
            self.assertEqual(accepted["source_notebook"]["embedded_pngs"],0)
            self.assertEqual(len(accepted["exported_pngs"]),4)
            (remote/"minute20_comeback.png").write_bytes(b"not a real PNG")
            with self.assertRaisesRegex(ValueError,"PNG artifact"):
                verify(local,remote,notebook,stripped_file,"kaggle")


if __name__=="__main__":
    unittest.main()
