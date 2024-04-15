import numpy as np


if __name__ == "__main__":
    num_samples_per_sample_set = 100
    num_sample_sets = 10
    samples = np.random.rand(num_samples_per_sample_set * num_sample_sets)

    signals_1 = np.reshape(
        samples,
        (num_samples_per_sample_set, num_sample_sets),
        order="F",
    ).T
    print(signals_1.shape)

    signal_list = [
        samples[i * num_samples_per_sample_set : (i + 1) * num_samples_per_sample_set]
        for i in range(num_sample_sets)
    ]
    signals = np.array(signal_list)
    print(signals.shape)

    np.testing.assert_array_equal(signals_1, signals)
