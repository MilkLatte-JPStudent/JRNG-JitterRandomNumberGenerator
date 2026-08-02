import hashlib
import time


def get_physical_jitter_seed(index: int) -> str:
    # 0.001〜0.003秒程度の微小な物理遅延（Jitter）を挿入してOSのジッターを取り込む
    time.sleep(0.001 * (1 + (index % 3)))

    now_ns = str(time.time_ns())
    date_str = time.strftime("%Y%m%d%H%M%S")  

    interleaved = ""
    for i, char in enumerate(now_ns):
        interleaved += f"{char}{index + i}"

    raw_seed = f"{date_str}{interleaved}{index}"
    return hashlib.sha256(raw_seed.encode()).hexdigest()


def self_action_transform(data_str: str, layer: int) -> str:
    transformed = f"{data_str}_B_LAYER_{layer}"
    return hashlib.sha256(transformed.encode()).hexdigest()


def generate_chaos_number(min_val: int, max_val: int, layers: int = 5) -> int:
    """カオスピラミッド構造を用いて指定範囲内の数値を算出する

    :param min_val: 出力範囲の最小値（含む）
    :param max_val: 出力範囲の最大値（含む）
    :param layers: 初期ノード数／ピラミッドの深さ（デフォルト: 5）
    :return: 確定された数値
    """
    if min_val > max_val:
        min_val, max_val = max_val, min_val

    # 1. 初期シード群の生成（階層数に応じたノード数）
    current_layer = [get_physical_jitter_seed(i) for i in range(layers)]

    # 2. ピラミッド構造による1点集約
    layer_num = 1
    while len(current_layer) > 1:
        layer_num += 1
        next_layer = []
        i = 0
        while i < len(current_layer):
            if i == len(current_layer) - 1:
                combined = current_layer[i] + next_layer[-1] + "EXTRA"
                fused = self_action_transform(combined, layer_num)
                next_layer[-1] = fused
                i += 1
            else:
                node_a = current_layer[i]
                node_b = current_layer[i + 1]
                combined = node_a + "_FUSE_" + node_b
                fused = self_action_transform(combined, layer_num)
                next_layer.append(fused)
                i += 2
        current_layer = next_layer

    # 3. 頂点ハッシュ値を指定範囲の数値に変換
    top_chaos_hash = current_layer[0]
    big_number = int(top_chaos_hash, 16)

    # 指定された最大値・最小値の範囲に収める
    range_size = (max_val - min_val) + 1
    result_number = min_val + (big_number % range_size)

    return result_number


# --- 実行例 ---
if __name__ == "__main__":
    # 例: 最小値 1, 最大値 100, 階層数(初期ノード) 75
    result = generate_chaos_number(min_val= -1000, max_val=1000, layers=400)

    # 数値のみを出力
    print(result)
