import numpy as np
import pandas as pd

from gaia_wobble.metrics import evaluate


def test_perfect_and_removed_known():
    n = 200
    df = pd.DataFrame({"score": np.arange(n, 0, -1.0), "y": np.arange(n) < 5, "known": np.arange(n) < 2})
    m = evaluate(df, "score", known="known")
    assert m.loc["all", "P@10"] == 0.5 and m.loc["all", "hits@100"] == 5
    assert m.loc["new", "n_pos"] == 3 and m.loc["new", "hits@100"] == 3 and m.loc["new", "Recall@100"] == 1.0
