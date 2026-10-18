"""LSTM training benchmark: same model, same data, GPU vs CPU wall time.

Designed for CESGA FinisTerrae-3 (TensorFlow module, A100 nodes).
Run twice via Slurm (see slurm/lstm_bench.slurm):
  - CPU mode: CUDA_VISIBLE_DEVICES="" with an exclusive 32-core node
  - GPU mode: --gres=gpu:a100:1

Output: benchmarks/lstm_bench_<mode>.csv
"""

import os
import sys
import time

import numpy as np
import pandas as pd

MODE = os.getenv("BENCH_MODE", "cpu")  # cpu | gpu | gpu_cudnn
if MODE == "cpu":
    os.environ["CUDA_VISIBLE_DEVICES"] = ""

import tensorflow as tf  # noqa: E402
from sklearn.preprocessing import MinMaxScaler  # noqa: E402

EPOCHS = 10
BATCH = 16
LOOK_BACK = 500
CSV = os.path.join(os.path.dirname(__file__), "ggal_daily.csv")
OUT = os.path.join(os.path.dirname(__file__), f"lstm_bench_{MODE}.csv")


def main() -> None:
    df = pd.read_csv(CSV)
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled = scaler.fit_transform(df[["Close"]].astype(float))

    def windows(data, look_back):
        x, y = [], []
        for i in range(len(data) - look_back):
            x.append(data[i : i + look_back, 0])
            y.append(data[i + look_back, 0])
        return np.array(x), np.array(y)

    x_train, y_train = windows(scaled, LOOK_BACK)
    x_train = x_train.reshape((x_train.shape[0], x_train.shape[1], 1))

    # cuDNN requires tanh/sigmoid activations; the original script used relu,
    # which silently falls back to a generic (slow) GPU kernel.
    cudnn = MODE == "gpu_cudnn"
    lstm_kwargs = {} if cudnn else {"activation": "relu"}
    model = tf.keras.Sequential(
        [
            tf.keras.layers.LSTM(100, input_shape=(LOOK_BACK, 1), **lstm_kwargs),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(50, activation="relu"),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(1),
        ]
    )
    model.compile(loss="mean_squared_error", optimizer="adam")

    t0 = time.perf_counter()
    history = model.fit(
        x_train,
        y_train,
        batch_size=BATCH,
        epochs=EPOCHS,
        verbose=0,
        validation_split=0.2,
    )
    wall = time.perf_counter() - t0

    devices = [d.device_type for d in tf.config.list_logical_devices()]
    row = f"{MODE},{EPOCHS},{BATCH},{x_train.shape[0]},{wall:.3f},{wall / EPOCHS:.3f},{';'.join(devices)}"
    with open(OUT, "w") as f:
        f.write("mode,epochs,batch,samples,wall_s,epoch_avg_s,devices\n")
        f.write(row + "\n")
    print(row)


if __name__ == "__main__":
    sys.exit(main())
