"""Reality check of the simulation (docs/simulation_plan.md). Stages: N (null sample), C (200 DR3 orbits, calibration then test), A, B.
Fixed before the first run: criteria, seeds, allowed adjustments (k(G) from the null calibration half, s from the calibration half of C)."""
import json

import duckdb
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from ..masses import photocentre_a0_mas
from ..paths import DATA_DIR, PROCESSED, RAW, REPO
from .observe import simulate_star
from .orbit import thiele_innes_offsets
from .samples import CONTROL_IDS, G_CLASSES, SEED

OUT = DATA_DIR / "interim" / "simulation"
S_GRID = [0.8, 0.9, 1.0, 1.1, 1.25, 1.5]
N_REAL_C = 20  # noise/parameter realisations per star in check C
K_BIN, K_MIN = 0.5, 25


def _rng(*keys):
    return np.random.default_rng([SEED, *[int(k) for k in keys]])


# ------------------------------------------------------------------ normalisation k(G) from the null calibration half
def null_simulate(part: str, s: float = 1.0) -> pd.DataFrame:
    d = pd.read_parquet(OUT / "null_sample.parquet")
    d = d[d.part == part].reset_index(drop=True)
    rows = []
    for i, r in enumerate(d.itertuples()):
        sim = simulate_star(r.ra, r.dec, r.phot_g_mean_mag, int(r.astrometric_n_obs_al // 9), _rng(1, i), s=s)
        rows.append(sim)
    return pd.concat([d, pd.DataFrame(rows)], axis=1)


def fit_k(cal: pd.DataFrame) -> pd.DataFrame:
    """k(G) per 0.5 mag bin: median real RUWE / median simulated UWE; bins with fewer than K_MIN stars are merged with the next one."""
    cal = cal.sort_values("phot_g_mean_mag")
    edges = np.arange(np.floor(cal.phot_g_mean_mag.min() * 2) / 2, cal.phot_g_mean_mag.max() + K_BIN, K_BIN)
    b = np.digitize(cal.phot_g_mean_mag, edges)
    groups, cur = [], []
    for k in np.unique(b):
        cur.append(k)
        if (np.isin(b, cur)).sum() >= K_MIN:
            groups.append(cur); cur = []
    if cur:
        groups[-1] = groups[-1] + cur if groups else cur
    rows = []
    for g in groups:
        sub = cal[np.isin(b, g)]
        rows.append({"g_lo": sub.phot_g_mean_mag.min(), "g_hi": sub.phot_g_mean_mag.max(), "n": len(sub),
                     "k": sub.ruwe.median() / sub.uwe.median()})
    return pd.DataFrame(rows)


def apply_k(k: pd.DataFrame, g: np.ndarray) -> np.ndarray:
    centres = ((k.g_lo + k.g_hi) / 2).to_numpy()
    return np.interp(g, centres, k.k.to_numpy())


# ------------------------------------------------------------------ orbit stars: Gaia's own solutions with parameter draws
def orbit_table(ids) -> pd.DataFrame:
    return duckdb.sql(f"""
        SELECT source_id, a_thiele_innes a, b_thiele_innes b, f_thiele_innes f, g_thiele_innes g, eccentricity e, period P, t_periastron tp,
               a_thiele_innes_error ea, b_thiele_innes_error eb, f_thiele_innes_error ef, g_thiele_innes_error eg,
               eccentricity_error ee, period_error eP, t_periastron_error etp
        FROM '{RAW}/nss/nss_two_body_orbit.parquet' WHERE source_id IN ({', '.join(map(str, ids))}) AND nss_solution_type = 'Orbital'""").df()


def draw_variant(o, rng):
    n = lambda v, e: v + (rng.normal(0, e) if np.isfinite(e) else 0.0)
    e = float(np.clip(n(o.e, o.ee), 0.0, 0.95))
    return dict(A=n(o.a, o.ea), B=n(o.b, o.eb), F=n(o.f, o.ef), G=n(o.g, o.eg), e=e, P_days=max(n(o.P, o.eP), 1.0), tperi_days=n(o.tp, o.etp))


def simulate_orbit_star(star, orb, n_real, k, s, key, variants=True):
    """`n_real` realisations, each with its own parameter variant and noise. Returns simulated RUWE (after k), AEN, chi2/dof per realisation."""
    from .observe import nominal_transits

    nominal = nominal_transits(star.ra, star.dec, "dr3")
    kk = float(apply_k(k, np.array([star.phot_g_mean_mag]))[0])
    out = []
    for j in range(n_real):
        rng = _rng(*key, j)
        par = draw_variant(orb, rng) if variants else dict(A=orb.a, B=orb.b, F=orb.f, G=orb.g, e=orb.e, P_days=orb.P, tperi_days=orb.tp)
        sim = simulate_star(star.ra, star.dec, star.phot_g_mean_mag, int(star.astrometric_n_obs_al // 9), rng,
                            offsets=lambda t, p=par: thiele_innes_offsets(t, **p), s=s, nominal=nominal)
        out.append({"ruwe": sim["uwe"] * kk, "aen": sim["excess_noise"], "chi2_dof": sim["chi2"] / max(sim["n_good_obs"] - 5, 1) * kk**2})
    return pd.DataFrame(out)


def summarize_c(part: str, k, s, n_real=N_REAL_C) -> tuple[pd.DataFrame, dict]:
    c = pd.read_parquet(OUT / "check_c_sample.parquet")
    c = c[c.part == part].reset_index(drop=True)
    orbs = orbit_table(c.source_id.tolist()).set_index("source_id")
    rows = []
    for i, r in enumerate(c.itertuples()):
        sims = simulate_orbit_star(r, orbs.loc[r.source_id], n_real, k, s, key=(2, i))
        lo, hi = sims.ruwe.quantile([0.05, 0.95])
        rows.append({"source_id": r.source_id, "ruwe_real": r.ruwe, "ruwe_sim_med": sims.ruwe.median(), "p05": lo, "p95": hi,
                     "inside": bool(lo <= r.ruwe <= hi), "aen_real": r.astrometric_excess_noise, "aen_sim_med": sims.aen.median(),
                     "chi2dof_real": r.chi2_per_dof, "chi2dof_sim_med": sims.chi2_dof.median()})
    t = pd.DataFrame(rows)
    ratio = t.ruwe_sim_med / t.ruwe_real
    stats = {"n": len(t), "median_ratio": float(ratio.median()), "log_median_ratio": float(np.log(ratio).median()),
             "spearman_ruwe": float(spearmanr(t.ruwe_sim_med, t.ruwe_real)[0]), "share_inside_90": float(t.inside.mean()),
             "spearman_aen": float(spearmanr(t.aen_sim_med, t.aen_real)[0]), "median_ratio_aen": float((t.aen_sim_med / t.aen_real.replace(0, np.nan)).median()),
             "spearman_chi2dof": float(spearmanr(t.chi2dof_sim_med, t.chi2dof_real)[0]), "median_ratio_chi2dof": float((t.chi2dof_sim_med / t.chi2dof_real).median())}
    return t, stats


def save(name, obj):
    (OUT / f"{name}.json").write_text(json.dumps(obj, indent=2, default=float) + "\n")


# ------------------------------------------------------------------ Model A features from a simulation (plan, item 5)
_GRID = {}


def _sigma_grid():
    """sigma_formal grid from the WHOLE DR3 catalogue (a small sample leaves most bins empty)."""
    if "g" not in _GRID:
        from ..amplitude import sigma_formal_grid

        full = duckdb.sql(f"""SELECT phot_g_mean_mag, bp_rp, astrometric_excess_noise_sig, chi2_per_dof, astrometric_excess_noise
                              FROM '{PROCESSED}/features_dr3.parquet' WHERE chi2_per_dof IS NOT NULL""").df()
        _GRID["g"] = sigma_formal_grid(full)
    return _GRID["g"]


def real_features(ids) -> pd.DataFrame:
    """Real values of the astrometric features of Model A plus the helpers needed to derive them from a simulation."""
    from ..amplitude import add_amplitude

    df = duckdb.sql(f"""
        SELECT f.source_id, f.phot_g_mean_mag, f.bp_rp, f.parallax, f.astrometric_excess_noise, f.astrometric_excess_noise_sig, f.chi2_per_dof,
               f.ruwe, f.ruwe_z, f.ruwe_excess, f.wobble_ratio, f.a1_max_mas, r.ruwe_expected, r.ruwe_sigma
        FROM '{PROCESSED}/features_dr3.parquet' f JOIN '{PROCESSED}/ruwe_features_dr3.parquet' r USING (source_id)
        WHERE f.source_id IN ({', '.join(map(str, ids))})""").df()
    return add_amplitude(df, _sigma_grid())


def fit_aen_sig_map(real: pd.DataFrame):
    from sklearn.isotonic import IsotonicRegression

    x = (real.astrometric_excess_noise / real.sigma_formal_mas).to_numpy()
    y = real.astrometric_excess_noise_sig.to_numpy()
    ok = np.isfinite(x) & np.isfinite(y)  # a few catalogue rows have no excess-noise value
    return IsotonicRegression(increasing=True, out_of_bounds="clip").fit(x[ok], y[ok])


def model_features(sim: pd.DataFrame, real: pd.DataFrame, k: pd.DataFrame, aen_map) -> pd.DataFrame:
    """Simulated Model-A features for stars in `real` (same order): `sim` has uwe, excess_noise, chi2, n_good_obs per star."""
    kk = apply_k(k, real.phot_g_mean_mag.to_numpy())
    ruwe = sim.uwe.to_numpy() * kk
    f = pd.DataFrame({"ruwe": ruwe})
    f["ruwe_excess"] = ruwe - real.ruwe_expected.to_numpy()
    f["ruwe_z"] = f.ruwe_excess / real.ruwe_sigma.to_numpy()
    f["chi2_per_dof"] = sim.chi2.to_numpy() / np.maximum(sim.n_good_obs.to_numpy() - 5, 1) * kk**2
    f["astrometric_excess_noise"] = sim.excess_noise.to_numpy()
    f["astrometric_excess_noise_sig"] = aen_map.predict(sim.excess_noise.to_numpy() / real.sigma_formal_mas.to_numpy())
    f["wobble_ratio"] = sim.excess_noise.to_numpy() / real.a1_max_mas.to_numpy()
    return f


FEATURES = ["ruwe", "ruwe_z", "ruwe_excess", "astrometric_excess_noise_sig", "chi2_per_dof", "wobble_ratio", "astrometric_excess_noise"]


def stage_null_test(k, aen_map) -> dict:
    sim = null_simulate("test")
    real = real_features(sim.source_id.tolist()).set_index("source_id").loc[sim.source_id].reset_index()
    f = model_features(sim, real, k, aen_map)
    real["g_class"] = sim.g_class.to_numpy()
    res = {"n": len(sim), "short_share": float(sim.short.mean()), "by_class": {}}
    ok = True
    for cls in ("G<10", "10-13", "13-16"):
        m = (real.g_class == cls).to_numpy()
        q = lambda x: x.quantile([0.25, 0.5, 0.75, 0.9, 0.99]).to_numpy()
        qr, qs = q(real.ruwe[m]), q(f.ruwe[m])
        p75_dev = float(qs[2] / qr[2] - 1)
        width_dev = float((qs[2] - qs[0]) / (qr[2] - qr[0]) - 1)
        passed = abs(p75_dev) <= 0.10 and abs(width_dev) <= 0.25
        ok &= passed
        feat = {}
        for name in FEATURES:
            a, b = real[name][m], f[name][m]
            feat[name] = {"real_q25_50_75_90": [float(v) for v in a.quantile([.25, .5, .75, .9])], "sim_q25_50_75_90": [float(v) for v in b.quantile([.25, .5, .75, .9])]}
        res["by_class"][cls] = {"n": int(m.sum()), "ruwe_real_q25_50_75_90_99": [float(v) for v in qr], "ruwe_sim_q25_50_75_90_99": [float(v) for v in qs],
                                "p75_deviation": p75_dev, "iqr_width_deviation": width_dev, "passed": bool(passed), "features": feat}
    res["N_passed"] = bool(ok)
    return res


def stage_c(k, aen_map, null_cal_real) -> dict:
    out = {"s_grid": {}}
    for s in S_GRID:
        _, st = summarize_c("calibration", k, s)
        out["s_grid"][str(s)] = st
        print(f"  C calibration s={s}: log median ratio {st['log_median_ratio']:+.3f}, spearman {st['spearman_ruwe']:.2f}, inside {st['share_inside_90']:.2f}", flush=True)
    best = min(S_GRID, key=lambda s: (round(abs(out["s_grid"][str(s)]["log_median_ratio"]), 6), abs(s - 1.0)))
    out["s_chosen"] = best
    t, st = summarize_c("test", k, best)
    st["criteria"] = {"i_spearman_gt_0.6": st["spearman_ruwe"] > 0.6, "ii_median_ratio_in_0.7_1.4": 0.7 <= st["median_ratio"] <= 1.4, "iii_inside_ge_0.70": st["share_inside_90"] >= 0.70}
    st["C_passed"] = bool(all(st["criteria"].values()))
    out["test"] = st
    t.to_parquet(OUT / "check_c_test_results.parquet", index=False)
    return out


def published_orbit_draw(pl: dict, rng):
    """Check B: dark companion, published elements with Gaussian uncertainties, unpublished angles and periastron time uniform."""
    P = max(rng.normal(pl["P"], pl["eP"]), 1.0)
    e = float(np.clip(rng.normal(pl["e"], pl["ee"]), 0.0, 0.95))
    inc = np.radians(rng.normal(pl["i"], pl["ei"]))
    m2 = max(rng.normal(pl["m2_mjup"], pl["em2"]), 0.1) * 9.5479e-4
    m1 = max(rng.normal(pl["m1"], pl["em1"]), 0.05)
    a_rel_au = ((m1 + m2) * (P / 365.25) ** 2) ** (1 / 3)
    a_mas = a_rel_au * m2 / (m1 + m2) * pl["parallax"]
    w, W, tp = rng.uniform(0, 2 * np.pi), rng.uniform(0, 2 * np.pi), rng.uniform(0, P)
    cw, sw, cW, sW, ci = np.cos(w), np.sin(w), np.cos(W), np.sin(W), np.cos(inc)
    return dict(A=a_mas * (cw * cW - sw * sW * ci), B=a_mas * (cw * sW + sw * cW * ci), F=a_mas * (-sw * cW - cw * sW * ci),
                G=a_mas * (-sw * sW + cw * cW * ci), e=e, P_days=P, tperi_days=tp)


PUBLISHED = {  # NASA Exoplanet Archive (Stefansson et al. 2025); m1 = host mass
    1457486023639239296: dict(name="Gaia-4 b", P=571.3, eP=1.4, e=0.338, ee=0.026, i=116.9, ei=4.2, m2_mjup=11.8, em2=0.7, m1=0.644, em1=0.025),
    2074815898041643520: dict(name="Gaia-5 b", P=358.62, eP=0.2, e=0.6423, ee=0.0026, i=129.7, ei=1.0, m2_mjup=20.87, em2=0.53, m1=0.339, em1=0.027),
}


def stage_ab(k, s, n=1000) -> dict:
    from .observe import nominal_transits

    res = {}
    real = real_features(CONTROL_IDS).set_index("source_id")
    orbs = orbit_table(CONTROL_IDS).set_index("source_id")
    for sid in CONTROL_IDS:
        r = real.loc[sid]
        star = pd.Series({"ra": float(duckdb.sql(f"SELECT ra FROM '{PROCESSED}/features_dr3.parquet' WHERE source_id = {sid}").fetchone()[0]),
                          "dec": float(duckdb.sql(f"SELECT dec FROM '{PROCESSED}/features_dr3.parquet' WHERE source_id = {sid}").fetchone()[0]),
                          "phot_g_mean_mag": r.phot_g_mean_mag, "astrometric_n_obs_al": duckdb.sql(f"SELECT astrometric_n_obs_al FROM '{PROCESSED}/features_dr3.parquet' WHERE source_id = {sid}").fetchone()[0]})
        a = simulate_orbit_star(star, orbs.loc[sid], n, k, s, key=(3, sid % 1000003))
        nominal = nominal_transits(star.ra, star.dec, "dr3")
        kk = float(apply_k(k, np.array([star.phot_g_mean_mag]))[0])
        rows = []
        pl = PUBLISHED[sid] | {"parallax": float(r.parallax)}
        for j in range(n):
            rng = _rng(4, sid % 1000003, j)
            par = published_orbit_draw(pl, rng)
            sim = simulate_star(star.ra, star.dec, star.phot_g_mean_mag, int(star.astrometric_n_obs_al // 9), rng,
                                offsets=lambda t, p=par: thiele_innes_offsets(t, **p), s=s, nominal=nominal)
            rows.append({"ruwe": sim["uwe"] * kk, "aen": sim["excess_noise"]})
        b = pd.DataFrame(rows)
        q = lambda x, y: [float(v) for v in x.quantile(y)]
        res[str(sid)] = {"name": PUBLISHED[sid]["name"], "ruwe_real": float(r.ruwe), "aen_real": float(r.astrometric_excess_noise),
                         "A_gaia_orbit": {"ruwe_q05_50_95": q(a.ruwe, [.05, .5, .95]), "aen_q05_50_95": q(a.aen, [.05, .5, .95]),
                                          "passed_ruwe": bool(a.ruwe.quantile(.05) <= r.ruwe <= a.ruwe.quantile(.95)),
                                          "aen_inside": bool(a.aen.quantile(.05) <= r.astrometric_excess_noise <= a.aen.quantile(.95)), "n": n},
                         "B_published": {"ruwe_q05_50_95": q(b.ruwe, [.05, .5, .95]), "aen_q05_50_95": q(b.aen, [.05, .5, .95]),
                                         "passed_ruwe": bool(b.ruwe.quantile(.05) <= r.ruwe <= b.ruwe.quantile(.95)),
                                         "aen_inside": bool(b.aen.quantile(.05) <= r.astrometric_excess_noise <= b.aen.quantile(.95)), "n": n}}
    return res
