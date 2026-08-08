import sys
import subprocess
import threading
import struct

# --- 設定パラメータ ---
TARGET_FILE = "/Users/apple/Downloads/jrng_rdm/JitterRandomNumberGenerator_kensyou2.py"  # 実行する特定のPythonファイル名
NUM_WORKERS = 116                        # 同時実行するプロセス数
# PractRandに一気に流すバッファサイズ（例: 64MB = 64 * 1024 * 1024 バイト）
CHUNK_SIZE = 16 * 1024

# 共有バッファとロック
data_buffer = bytearray()
buffer_lock = threading.Lock()
stdout_write = sys.stdout.buffer.write
stdout_flush = sys.stdout.buffer.flush

def read_worker_output(proc):
    """各プロセスの標準出力を監視して共通バッファに溜める関数"""
    global data_buffer
    
    while True:
        # 16bit(2バイト)単位、または適当なブロック単位で読み込み
        chunk = proc.stdout.read(4096)
        if not chunk:
            break
            
        with buffer_lock:
            data_buffer.extend(chunk)
            
            # 規定サイズに達したら標準出力（パイプ先）へ一括フラッシュ
            if len(data_buffer) >= CHUNK_SIZE:
                # 規定サイズ分だけ切り出して出力
                to_send = data_buffer[:CHUNK_SIZE]
                del data_buffer[:CHUNK_SIZE]
                
                try:
                    stdout_write(to_send)
                    stdout_flush()
                except BrokenPipeError:
                    # パイプ先（PractRand）が終了した場合はプロセスを止める
                    proc.kill()
                    sys.exit(0)

def main():
    threads = []
    processes = []

    # 50個のPythonプロセスを同時に起動
    for _ in range(NUM_WORKERS):
        proc = subprocess.Popen(
            ["python", TARGET_FILE],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, # エラーログが混ざらないように除外
            bufsize=0
        )
        processes.append(proc)
        
        # 各プロセスの出力を非同期で読み取るスレッドを開始
        t = threading.Thread(target=read_worker_output, args=(proc,))
        t.daemon = True
        t.start()
        threads.append(t)

    try:
        # 子プロセスが動いている間メインスレッドを待機
        for proc in processes:
            proc.wait()
    except KeyboardInterrupt:
        # Ctrl+Cで終了されたら全ての子プロセスを強制終了
        for proc in processes:
            proc.terminate()

if __name__ == "__main__":
    #for _ in range(2 << 6):
    #while True:
        main()