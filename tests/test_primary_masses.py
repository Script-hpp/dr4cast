import numpy as np

from gaia_wobble.primary_masses import mass_ms_strict


def test_strict_range_and_values():
    m = mass_ms_strict(np.array([4.635, 8.16, -5.0, 20.0, np.nan]))
    assert abs(m[0] - 1.0) < 0.01 and abs(m[1] - 0.57) < 0.01   # G2V and M0V of the table
    assert np.isnan(m[2]) and np.isnan(m[3]) and np.isnan(m[4])  # outside the table or undefined: no m1, no clipping
