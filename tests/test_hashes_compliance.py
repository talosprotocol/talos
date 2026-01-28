import json
import hashlib
import unittest
import sys
from pathlib import Path

# Add connector source to path (Prioritize local version)
sys.path.insert(0, str(Path.cwd() / "services/mcp-connector/src"))

try:
    from talos_mcp.domain.tool_policy import DocumentValidator, DocumentSpec, ToolPolicyError
except ImportError as e:
    print(f"Import Error: {e}")
    import sys
    print(sys.path)
    raise

# Re-implement JCS logic locally for verification
def jcs_serialize(data) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')

class TestHashesCompliance(unittest.TestCase):
    def setUp(self):
        # Load vectors
        vector_path = Path("contracts/schemas/mcp/hashing_vectors.json")
        if not vector_path.exists():
            vector_path = Path("services/mcp-connector/contracts/schemas/mcp/hashing_vectors.json")
        
        if not vector_path.exists():
            vector_path = Path("/Users/nileshchakraborty/workspace/talos/contracts/schemas/mcp/hashing_vectors.json")

        with open(vector_path, "r") as f:
            self.vectors = json.load(f)

    def test_tool_call_digests(self):
        for case in self.vectors["tool_call_vectors"]:
            input_data = case["input"]
            expected_digest = case["digest"]
            
            serialized = jcs_serialize(input_data)
            computed = hashlib.sha256(serialized).hexdigest()
            
            self.assertEqual(
                computed, 
                expected_digest, 
                f"Digest mismatch for {case['description']}"
            )

    def test_document_digests(self):
        for case in self.vectors["document_vectors"]:
            doc_type = case["doc_type"]
            expected_digest = case["digest"]
            
            if doc_type == "json":
                input_data = case["input"]
                serialized = jcs_serialize(input_data)
                computed = hashlib.sha256(serialized).hexdigest()
            elif doc_type == "bytes":
                import base64
                input_b64 = case["input_b64"]
                decoded = base64.b64decode(input_b64)
                computed = hashlib.sha256(decoded).hexdigest()
            
            self.assertEqual(computed, expected_digest, f"Doc digest mismatch for {case['description']}")

    def test_negative_validation(self):
        """Verify negative cases raise ToolPolicyError with correct code."""
        if "negative_validation_vectors" not in self.vectors:
            print("Skipping negative validation (vectors not present)")
            return

        for case in self.vectors["negative_validation_vectors"]:
            print(f"Testing Negative Case: {case['description']}")
            d_spec = case["doc_spec"]
            
            # Construct DocumentSpec from vector dict
            spec = DocumentSpec(
                write_content_pointers=d_spec.get("write_content_pointers", []),
                read_content_pointers=d_spec.get("read_content_pointers", []),
                content_encoding=d_spec.get("content_encoding", "utf8"),
                max_read_bytes=10000,
                max_write_bytes=d_spec.get("max_write_bytes", 10000),
                max_batch_bytes=100000
            )
            
            expected_code = case["error_code"]
            args = case["args"]
            expected_hashes = case.get("expected_hashes")

            with self.assertRaises(ToolPolicyError) as cm:
                DocumentValidator.validate_write_content(
                    doc_spec=spec,
                    args=args,
                    expected_hashes=expected_hashes
                )
            
            self.assertEqual(cm.exception.code, expected_code, f"Wrong error code for {case['description']}")

if __name__ == "__main__":
    unittest.main()
