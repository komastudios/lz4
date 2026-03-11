import os
import platform
import sys
from pathlib import Path
from cffi import FFI

# --- Library Loading ---

ffi = FFI()

# Define C structures and function signatures
# (Simplified versions sufficient for the wrapper)
ffi.cdef("""
    // Block API
    int LZ4_compress_default(const char* src, char* dst, int srcSize, int dstCapacity);
    int LZ4_decompress_safe(const char* src, char* dst, int compressedSize, int dstCapacity);
    int LZ4_compressBound(int inputSize);

    // Frame API
    typedef size_t LZ4F_errorCode_t;
    typedef struct LZ4F_cctx_s LZ4F_cctx;
    typedef struct LZ4F_dctx_s LZ4F_dctx;
    
    typedef struct {
        unsigned int blockSizeID;
        unsigned int blockMode;
        unsigned int contentChecksumFlag;
        unsigned int frameType;
        unsigned long long contentSize;
        unsigned int dictID;
        unsigned int blockChecksumFlag;
    } LZ4F_frameInfo_t;

    typedef struct {
        LZ4F_frameInfo_t frameInfo;
        int compressionLevel;
        unsigned int autoFlush;
        unsigned int favorDecSpeed;
        unsigned int reserved[3];
    } LZ4F_preferences_t;

    typedef struct {
        unsigned int stableDst;
        unsigned int skipChecksums;
        unsigned int reserved1;
        unsigned int reserved0;
    } LZ4F_decompressOptions_t;

    unsigned LZ4F_isError(LZ4F_errorCode_t code);
    const char* LZ4F_getErrorName(LZ4F_errorCode_t code);
    
    size_t LZ4F_compressFrameBound(size_t srcSize, const LZ4F_preferences_t* preferencesPtr);
    size_t LZ4F_compressFrame(void* dstBuffer, size_t dstCapacity, const void* srcBuffer, size_t srcSize, const LZ4F_preferences_t* preferencesPtr);
    
    LZ4F_errorCode_t LZ4F_createDecompressionContext(LZ4F_dctx** dctxPtr, unsigned version);
    LZ4F_errorCode_t LZ4F_freeDecompressionContext(LZ4F_dctx* dctx);
    
    size_t LZ4F_decompress(LZ4F_dctx* dctx, void* dstBuffer, size_t* dstSizePtr, const void* srcBuffer, size_t* srcSizePtr, const LZ4F_decompressOptions_t* dOptPtr);
""")

_lib = None

def _load_lib():
    global _lib
    if _lib is not None:
        return _lib

    # 1. Environment Variable
    env_path = os.environ.get("LZ4_NATIVE_LIB")
    if env_path and os.path.exists(env_path):
        try:
            return ffi.dlopen(env_path)
        except Exception as e:
            print(f"Warning: Failed to load LZ4_NATIVE_LIB at {env_path}: {e}", file=sys.stderr)

    # 2. Bundled Library (relative to this file)
    system = platform.system()
    if system == "Darwin":
        names = ["liblz4.dylib", "liblz4.1.dylib"]
    elif system == "Windows":
        names = ["lz4.dll", "liblz4.dll"]
    else: # Linux/Unix
        names = ["liblz4.so", "liblz4.so.1"]

    package_dir = Path(__file__).parent.resolve()
    lib_dir = package_dir / "lib"
    
    if lib_dir.exists():
        for name in names:
            bundled_path = lib_dir / name
            if bundled_path.exists():
                try:
                    return ffi.dlopen(str(bundled_path))
                except Exception:
                    pass

    # 3. System Library (ABI mode)
    # On most Unix systems, ffi.dlopen can find the system library by name
    for name in ["lz4", "liblz4.so.1", "liblz4.dylib"]:
        try:
            return ffi.dlopen(name)
        except Exception:
            pass
            
    raise RuntimeError("Could not find lz4 shared library. "
                       "Install it system-wide or set LZ4_NATIVE_LIB env var.")

_lib = _load_lib()

LZ4F_VERSION = 100 

def _check_error(code, func_name):
    if _lib.LZ4F_isError(code):
        err_name = ffi.string(_lib.LZ4F_getErrorName(code)).decode('utf-8', errors='replace')
        raise RuntimeError(f"{func_name} failed: {err_name} (code {code})")
    return code

# --- High Level API ---

def compress(data):
    """Block compression (LZ4_compress_default). Matches existing usage."""
    if not data: return b""
    src = bytes(data)
    src_size = len(src)
    dst_cap = _lib.LZ4_compressBound(src_size)
    dst_buf = ffi.new("char[]", dst_cap)
    
    sz = _lib.LZ4_compress_default(src, dst_buf, src_size, dst_cap)
    if sz <= 0:
        raise RuntimeError("LZ4 block compression failed")
    return ffi.unpack(dst_buf, sz)

def decompress(data, uncompressed_size):
    """Block decompression (LZ4_decompress_safe). Requires known output size."""
    if uncompressed_size == 0: return b""
    src = bytes(data)
    dst_buf = ffi.new("char[]", uncompressed_size)
    
    sz = _lib.LZ4_decompress_safe(src, dst_buf, len(src), uncompressed_size)
    if sz < 0:
        raise RuntimeError(f"LZ4 block decompression failed: {sz}")
    if sz != uncompressed_size:
        raise RuntimeError(f"Size mismatch: expected {uncompressed_size}, got {sz}")
    return ffi.unpack(dst_buf, sz)

def compress_frame(data):
    """Frame compression (LZ4F_compressFrame)."""
    if not data: return b""
    src = bytes(data)
    src_size = len(src)
    
    # Calculate bound (worst case)
    bound = _lib.LZ4F_compressFrameBound(src_size, ffi.NULL)
    dst_buf = ffi.new("char[]", bound)
    
    sz = _lib.LZ4F_compressFrame(dst_buf, bound, src, src_size, ffi.NULL)
    _check_error(sz, "LZ4F_compressFrame")
    
    return ffi.unpack(dst_buf, sz)

def decompress_frame(data, buffer_size=65536):
    """Frame decompression. Automatically handles context and streaming."""
    if not data: return b""
    
    # Create context
    dctx_ptr = ffi.new("LZ4F_dctx**")
    ret = _lib.LZ4F_createDecompressionContext(dctx_ptr, LZ4F_VERSION)
    _check_error(ret, "LZ4F_createDecompressionContext")
    dctx = dctx_ptr[0]
    
    try:
        src = bytes(data)
        src_len = len(src)
        src_ptr_offset = 0
        
        out_chunks = []
        
        dst_buf = ffi.new("char[]", buffer_size)
        dst_sz_val = ffi.new("size_t*", buffer_size)
        src_sz_val = ffi.new("size_t*")
        
        while src_ptr_offset < src_len:
            src_sz_val[0] = src_len - src_ptr_offset
            dst_sz_val[0] = buffer_size
            
            # Use pointer arithmetic to pass the current source position
            ret = _lib.LZ4F_decompress(
                dctx,
                dst_buf, dst_sz_val,
                ffi.from_buffer(src[src_ptr_offset:]), src_sz_val,
                ffi.NULL
            )
            _check_error(ret, "LZ4F_decompress")
            
            # Append output
            if dst_sz_val[0] > 0:
                out_chunks.append(ffi.unpack(dst_buf, dst_sz_val[0]))
            
            # Advance input
            src_ptr_offset += src_sz_val[0]
            
            # ret is hint for next size, but 0 means end of frame usually.
            if ret == 0:
                break
                
        return b"".join(out_chunks)
        
    finally:
        _lib.LZ4F_freeDecompressionContext(dctx)
