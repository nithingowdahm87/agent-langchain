import os
import json
import shutil
import tempfile
import unittest
from src.memory.long_term_memory import LongTermMemory

class TestMemory(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.memory = LongTermMemory(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_store_and_retrieve(self):
        # Store
        self.memory.store_decision(
            stage="test_stage",
            content="some_content",
            reason="looks good",
            decision="APPROVED"
        )
        
        # Verify file exists
        mem_file = os.path.join(self.test_dir, ".devops_memory.json")
        self.assertTrue(os.path.exists(mem_file))
        
        # Verify retrieve
        history = self.memory.get_history("test_stage")
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["decision"], "APPROVED")
        self.assertEqual(history[0]["reason"], "looks good")
        
    def test_persistence(self):
        # Store initial
        self.memory.store_decision("stage1", "c1", "r1", "APPROVED")
        
        # Re-initialize memory (simulate new run)
        new_memory = LongTermMemory(self.test_dir)
        history = new_memory.get_history("stage1")
        
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["content_snippet"], "c1")
        
    def test_truncation(self):
        long_content = "a" * 300
        self.memory.store_decision("stage2", long_content, "r2", "APPROVED")
        history = self.memory.get_history("stage2")
        self.assertTrue(history[0]["content_snippet"].endswith("..."))
        self.assertEqual(len(history[0]["content_snippet"]), 203) # 200 + 3 dots
        
if __name__ == "__main__":
    unittest.main()
