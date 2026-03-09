#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define XXH_NAMESPACE LZ4_
#include "xxhash.h"

#define ASSERT(expr, msg) do { \
    if(!(expr)) { \
        fprintf(stderr, "%s:%d: Assertion failed: %s\n", __FILE__, __LINE__, msg); \
        exit(EXIT_FAILURE); \
    } \
} while(0)

static const char test_data[] = "Hello, xxHash! Testing all hash variants with LZ4_ namespace.";

void test_xxh32(void) {
    XXH32_hash_t h = LZ4_XXH32(test_data, sizeof(test_data), 0);
    ASSERT(h != 0, "XXH32 returned zero");

    XXH32_hash_t h2 = LZ4_XXH32(test_data, sizeof(test_data), 42);
    ASSERT(h != h2, "XXH32 with different seeds should differ");

    fprintf(stderr, "  test_xxh32 passed (h=0x%08x)\n", h);
}

void test_xxh64(void) {
    XXH64_hash_t h = LZ4_XXH64(test_data, sizeof(test_data), 0);
    ASSERT(h != 0, "XXH64 returned zero");

    XXH64_hash_t h2 = LZ4_XXH64(test_data, sizeof(test_data), 42);
    ASSERT(h != h2, "XXH64 with different seeds should differ");

    fprintf(stderr, "  test_xxh64 passed (h=0x%016llx)\n", (unsigned long long)h);
}

void test_xxh3_64(void) {
    XXH64_hash_t h = LZ4_XXH3_64bits(test_data, sizeof(test_data));
    ASSERT(h != 0, "XXH3_64bits returned zero");

    XXH64_hash_t h2 = LZ4_XXH3_64bits_withSeed(test_data, sizeof(test_data), 42);
    ASSERT(h != h2, "XXH3_64bits with different seeds should differ");

    fprintf(stderr, "  test_xxh3_64 passed (h=0x%016llx)\n", (unsigned long long)h);
}

void test_xxh3_128(void) {
    XXH128_hash_t h = LZ4_XXH3_128bits(test_data, sizeof(test_data));
    ASSERT(h.low64 != 0 || h.high64 != 0, "XXH3_128bits returned zero");

    XXH128_hash_t h2 = LZ4_XXH3_128bits_withSeed(test_data, sizeof(test_data), 42);
    ASSERT(h.low64 != h2.low64 || h.high64 != h2.high64, "XXH3_128bits with different seeds should differ");

    fprintf(stderr, "  test_xxh3_128 passed (h=0x%016llx%016llx)\n",
            (unsigned long long)h.high64, (unsigned long long)h.low64);
}

int main(int argc, char** argv) {
    (void)argc;
    (void)argv;

    fprintf(stderr, "Running xxHash tests (namespace=LZ4_)...\n");
    fprintf(stderr, "xxHash version: %u\n", LZ4_XXH_versionNumber());

    test_xxh32();
    test_xxh64();
    test_xxh3_64();
    test_xxh3_128();

    fprintf(stderr, "All xxHash tests passed.\n");
    return 0;
}
