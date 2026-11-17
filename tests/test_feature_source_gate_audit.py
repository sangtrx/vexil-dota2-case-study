import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"))
from feature_source_gate_audit import report


class FeasibilityGate(unittest.TestCase):
    def test_blocks_have_explanations_and_no_personal_chat(self):
        doc=report({
            "chat_event_counts":{"chat_events":10,
                "games_with_chat":1,
                "chat_events_before_game":2,
                "chat_events_after_duration":3,
                "upgrade_entries":5,
                "upgrade_entries_with_timestamps":0},
            "chat_type_counts":{"chat":10},
        })
        self.assertIn("BLOCKED",doc)
        self.assertIn("not",doc)
        self.assertNotIn("test_dummy_message_secret",doc)

if __name__=="__main__":
    unittest.main()
