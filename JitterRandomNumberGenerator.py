import hashlib
import time
import sys
import os
import struct
import itertools
global ik
ik = 0


def get_physical_jitter_seed(index: int) -> str:
    global ik
    raw_seed = []
    for _1 in range(2):
        # 0.001〜0.003秒程度の微小な物理遅延（Jitter）を挿入してOSのジッターを取り込む
        #time.sleep(0.000000002* (1 + (index % 3)))
        for _3 in range(1):
            os.sched_yield()
            time.sleep(0.0004* (1 + (index % 3)))

        now_ns = str(int(time.time_ns()) % 10000000 / 1000)
        date_str = time.strftime("%Y%m%d%H%M%S")  
        worker_pid = os.getpid()

        interleaved = ""
        for i, char in enumerate(now_ns):
            interleaved += f"{char}{index + i}"
            
        raw_seed.append(f"{interleaved}{date_str}{interleaved}{worker_pid}{interleaved}{index}{interleaved}{now_ns}")
    ik += 1
    t1 = raw_seed[0]
    t2 = raw_seed[1]
    raw_seed = str("".join([bytes([(x1 + y1) % 256]).decode("utf-8") for x1, y1 in zip(list(bytes(t1.encode())), list(bytes(t2.encode())))]))

    return hashlib.sha512(raw_seed.encode()).hexdigest()


def self_action_transform(data_str: str, layer: int) -> str:
    transformed = f"{data_str}{layer}"
    return hashlib.sha512(transformed.encode()).hexdigest()


def generate_chaos_number(min_val: int, max_val: int, layers: int = 5) -> int:
    global ik
    """カオスピラミッド構造を用いて指定範囲内の数値を算出する

    :param min_val: 出力範囲の最小値（含む）
    :param max_val: 出力範囲の最大値（含む）
    :param layers: 初期ノード数／ピラミッドの深さ（デフォルト: 5）
    :return: 確定された数値
    """
    if min_val > max_val:
        min_val, max_val = max_val, min_val

    # 1. 初期シード群の生成（階層数に応じたノード数）
    current_layer = [get_physical_jitter_seed(i+ik) for i in range(layers)]

    # 2. ピラミッド構造による1点集約
    layer_num = 1
    while len(current_layer) > 1:
        layer_num += 1
        next_layer = []
        i = 0
        while i < len(current_layer):
            if i == len(current_layer) - 1:
                combined = current_layer[i] + next_layer[-1]
                fused = self_action_transform(combined, layer_num)
                next_layer[-1] = fused
                i += 1
            else:
                node_a = current_layer[i]
                node_b = current_layer[i + 1]
                combined = node_a + node_b
                fused = self_action_transform(combined, layer_num)
                next_layer.append(fused)
                i += 2
        current_layer = next_layer

    # 3. 頂点ハッシュ値を指定範囲の数値に変換
    big_number = int(current_layer[0], 16)

    # 指定された最大値・最小値の範囲に収める
    MAX_SHA256_VAL = (1 << 256) - 1
    MAX_SHA512_VAL = (1 << 512) - 1
    range_size = (max_val - min_val) + 1
    #result_number = min_val + (big_number % range_size)
    result_number = min_val + ((big_number * range_size) // MAX_SHA512_VAL)

    return result_number

def generate_32_chaos(count: int) -> list:
    num = [generate_chaos_number(min_val=0, max_val=(1 << 512) - 1, layers=25).to_bytes(64, byteorder='big') for _ in range(count)]
    result = [struct.unpack('>32H', num[i]) for i in range(count)]
    int16_list = [x - 32768 for x in list(itertools.chain.from_iterable(result))]
    return int16_list

# --- 実行例 ---
if __name__ == "__main__":
    result = generate_chaos_number(min_val=-1024, max_val=1023, layers=25)
    print()
