import unittest
import lz4_native
import os

class TestLZ4Native(unittest.TestCase):
    def test_block_compression(self):
        data = b"Hello World" * 100
        compressed = lz4_native.compress(data)
        self.assertGreater(len(compressed), 0)
        decompressed = lz4_native.decompress(compressed, len(data))
        self.assertEqual(data, decompressed)

    def test_frame_compression(self):
        data = b"Hello Frame" * 100
        compressed = lz4_native.compress_frame(data)
        self.assertGreater(len(compressed), 0)
        # Magic number check (LZ4 Frame)
        self.assertEqual(compressed[:4], b'\x04\x22\x4D\x18')
        decompressed = lz4_native.decompress_frame(compressed)
        self.assertEqual(data, decompressed)

if __name__ == "__main__":
    print(f"Testing with lib: {lz4_native._lib}")
    unittest.main()
