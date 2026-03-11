#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "lz4.h"

#define ASSERT(expr, msg) do { \
    if(!(expr)) { \
        fprintf(stderr, "%s:%d: Assertion failed: %s\n", __FILE__, __LINE__, msg); \
        exit(EXIT_FAILURE); \
    } \
} while(0)

#define ASSERT_EQ(val1, val2) do { \
    if((val1) != (val2)) { \
        fprintf(stderr, "%s:%d: Expected: %s == %s\n", \
                __FILE__, __LINE__, #val1, #val2); \
        exit(EXIT_FAILURE); \
    } \
} while(0)

void test_version(void) {
    ASSERT_EQ(LZ4_versionNumber(), LZ4_VERSION_NUMBER);
    fprintf(stderr, "  test_version passed\n");
}

void test_compress_bound(void) {
    int bound = LZ4_compressBound(1024);
    ASSERT(bound > 0, "compressBound should be positive for valid input");

    int zero_bound = LZ4_compressBound(0x7E000001);
    ASSERT_EQ(zero_bound, 0);

    fprintf(stderr, "  test_compress_bound passed\n");
}

void test_compress_decompress(void) {
    const char src[] = "Hello, LZ4 compression! This is a test of round-trip compression and decompression.";
    int src_size = (int)sizeof(src);

    int max_dst_size = LZ4_compressBound(src_size);
    ASSERT(max_dst_size > 0, "compressBound failed");

    char* compressed = (char*)malloc((size_t)max_dst_size);
    ASSERT(compressed != NULL, "malloc failed");

    int compressed_size = LZ4_compress_default(src, compressed, src_size, max_dst_size);
    ASSERT(compressed_size > 0, "compression failed");

    char* decompressed = (char*)malloc((size_t)src_size);
    ASSERT(decompressed != NULL, "malloc failed");

    int decompressed_size = LZ4_decompress_safe(compressed, decompressed, compressed_size, src_size);
    ASSERT_EQ(decompressed_size, src_size);
    ASSERT(memcmp(src, decompressed, (size_t)src_size) == 0, "decompressed data does not match original");

    free(compressed);
    free(decompressed);
    fprintf(stderr, "  test_compress_decompress passed\n");
}

void test_decompress_failure(void) {
    const char src[] = "Test data for decompression failure.";
    int src_size = (int)sizeof(src);

    int max_dst_size = LZ4_compressBound(src_size);
    char* compressed = (char*)malloc((size_t)max_dst_size);
    ASSERT(compressed != NULL, "malloc failed");

    int compressed_size = LZ4_compress_default(src, compressed, src_size, max_dst_size);
    ASSERT(compressed_size > 0, "compression failed");

    /* corrupt the compressed data */
    compressed[0] ^= 0xFF;

    char* decompressed = (char*)malloc((size_t)src_size);
    ASSERT(decompressed != NULL, "malloc failed");

    int result = LZ4_decompress_safe(compressed, decompressed, compressed_size, src_size);
    ASSERT(result < 0, "decompress_safe should fail on corrupt data");

    /* truncated data */
    compressed[0] ^= 0xFF; /* restore first byte */
    result = LZ4_decompress_safe(compressed, decompressed, 1, src_size);
    ASSERT(result < 0, "decompress_safe should fail on truncated data");

    free(compressed);
    free(decompressed);
    fprintf(stderr, "  test_decompress_failure passed\n");
}

int main(int argc, char** argv) {
    (void)argc;
    (void)argv;

    fprintf(stderr, "Running LZ4 tests...\n");
    fprintf(stderr, "LZ4 version: %d\n", LZ4_versionNumber());

    test_version();
    test_compress_bound();
    test_compress_decompress();
    test_decompress_failure();

    fprintf(stderr, "All tests passed.\n");
    return 0;
}
