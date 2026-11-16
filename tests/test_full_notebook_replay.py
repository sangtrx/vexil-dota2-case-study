"""Fail-closed offline 500-game Jupyter replay preflight, no network needed."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"research/full_notebook_replay.py"
spec=importlib.util.spec_from_file_location("full_notebook_replay",PATH)
R=importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)


def fake_match(mid:int,patch:int):
    return {
        "match_id":mid,"radiant_gold_adv":[0,500,1000],
        "duration":800,"radiant_win":bool(mid%2),
        "patch":patch,
    }


class SourcePreflightTests(unittest.TestCase):
    def test_frozen_key_agrees_with_notebook_http_cache_key(self):
        mid=8737958835
        expected=hashlib.sha256(json.dumps(["/matches/"+str(mid),{}],
                                           sort_keys=True).encode()).hexdigest()
        self.assertEqual(R.key_for(mid),expected)

    def test_scientific_fingerprint_matches_original_notebook(self):
        # No nbformat import is necessary for the lightweight core test.
        nb=json.loads(R.NB.read_text())
        cells=[SimpleNamespace(cell_type=c["cell_type"],
                               source="".join(c.get("source",[]))) for c in nb["cells"]]
        fake=SimpleNamespace(cells=cells)
        self.assertEqual(R.scientific_fingerprint(fake),R.EXPECTED_NOTEBOOK_CODE_SHA)
        ids=R.source_ids(fake)
        self.assertEqual(len(ids),500)
        self.assertEqual(len(set(ids)),500)

    def test_mutation_of_frozen_source_is_detected(self):
        original=json.loads(R.NB.read_text())
        cells=[SimpleNamespace(cell_type=c["cell_type"],
                               source="".join(c.get("source",[]))) for c in original["cells"]]
        fake=SimpleNamespace(cells=cells)
        original_sha=R.scientific_fingerprint(fake)
        cells[4].source+="\n# malicious changed model source\n"
        self.assertNotEqual(R.scientific_fingerprint(fake),original_sha)

    def test_missing_cache_fails_before_any_kernel_or_network(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(FileNotFoundError):
                R.preflight_cache(Path(td),(12,))

    def test_wrong_match_payload_fails_even_when_filename_matches(self):
        with tempfile.TemporaryDirectory() as td:
            directory=Path(td)
            bad=fake_match(14,59)
            with gzip.open(directory/(R.key_for(13)+".json.gz"),"wt") as z:
                json.dump(bad,z)
            with self.assertRaisesRegex(ValueError,"identity mismatch"):
                R.preflight_cache(directory,(13,))

    def test_unparsed_or_wrong_terminal_result_fails_before_kernel(self):
        with tempfile.TemporaryDirectory() as td:
            directory=Path(td)
            bad=fake_match(13,59)
            bad["radiant_win"]=None
            with gzip.open(directory/(R.key_for(13)+".json.gz"),"wt") as z:
                json.dump(bad,z)
            with self.assertRaisesRegex(ValueError,"eligibility drift"):
                R.preflight_cache(directory,(13,))

    def test_complete_metadata_only_synthetic_cache_and_copy(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            source=root/"source"
            source.mkdir()
            ids=tuple(range(10000,10500))
            for index,mid in enumerate(ids):
                patch=59 if index<250 else 60
                with gzip.open(source/(R.key_for(mid)+".json.gz"),"wt") as z:
                    json.dump(fake_match(mid,patch),z)
            by_name,source_digest=R.preflight_cache(source,ids)
            self.assertEqual(len(by_name),500)
            self.assertEqual(len(source_digest),64)
            dest=R.copy_frozen_sources(by_name,root/"scratch")
            self.assertEqual(len(list(dest.iterdir())),500)
            with self.assertRaises(FileExistsError):
                R.copy_frozen_sources(by_name,root/"scratch")

    def test_source_manifest_never_includes_employer_delivery(self):
        text=PATH.read_text()
        self.assertNotIn("requests.get(",text)
        self.assertNotIn("requests.Session(",text)
        self.assertIn('EXPECTED_CODE_CELLS=14',text)
        self.assertIn('cache_hits"]!=500',text)
        self.assertIn('original_test_predictions_sha256',text)


if __name__=="__main__":
    unittest.main()
