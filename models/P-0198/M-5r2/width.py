#!/usr/bin/env python3
"""CHI Issue E.b / F field-width → U, D, k. UNSIGNED algebra, not silicon.

Primary: ARM IHI 0050E.b (Issue E.b, ID081621)
  Table 13-8 Snoop flit format (p.13-413)
  Table 13-9 Data flit fields (p.13-414/13-415)
  Table 13-18 Size encodings (p.13-427): max 64 B, 0b111 reserved
Cross-check: ARM public Channel Interface overview (ihi0050/latest) SNP ≈ 88 b
  IHI0050F Issue F §13.6 / DataWidth 000–100 = 4 B–64 B (still no 128 B Data)
"""

from __future__ import annotations

import math

# Table 13-8 fixed fields excluding SrcID, FwdNID, Addr, MPAM:
# QoS4 + TxnID12 + FwdTxnID12 + Opcode5 + NS1 + DoNotGoToSD1 + RetToSrc1 + TraceTag1 = 37
# SrcID + FwdNID = 2N, N ∈ [7, 11]
# Addr SAW ∈ [41, 49] = Req_Addr_Width - 3
# MPAM M ∈ {0, 11}
# Spec total: S = 51+SAW+M .. 59+SAW+M  (= 37+2N+SAW+M)

SNP_FIXED = 37
N_LO, N_HI = 7, 11
SAW_LO, SAW_HI = 41, 49
MPAM_OFF, MPAM_ON = 0, 11

# Stay bits subtracted from W_snp to get usable payload U.
# valid is SNPFLITV (separate pin in Table 13-4); still charged (must remain).
# dest is NOT in Table 13-8 (no TgtID); ring eject needs it.
VALID, CH_DISC, ITAG, ETAG, QOS_STAY = 1, 2, 1, 1, 4
H_FRAG = 32  # src≤11 + TxnID12 + frag_id4 + last1 + pad


def w_snp(n: int, saw: int, mpam: int) -> int:
    return SNP_FIXED + 2 * n + saw + mpam


def s_keep(n: int, qos: bool = False) -> int:
    # qos=True: Table 13-8 QoS(4) stays so ghost cannot overwrite native priority
    extra = QOS_STAY if qos else 0
    return VALID + CH_DISC + n + ITAG + ETAG + extra


def usable(n: int, saw: int, mpam: int) -> tuple[int, int, int]:
    w = w_snp(n, saw, mpam)
    s = s_keep(n)
    return w, s, w - s


def d_of(beat_bytes: int, with_be: bool) -> int:
    data = beat_bytes * 8
    be = (data // 8) if with_be else 0
    return data + be + H_FRAG


def k_of(d: int, u: int) -> int:
    return math.ceil(d / u)


PINS = {
    "E.b-narrow": dict(n=7, saw=41, mpam=0, note="Table 13-8 min: N=7 SAW=41 no MPAM"),
    "E.b-mid": dict(n=11, saw=45, mpam=0, note="Table 13-8 N=11 Addr[47:3] no MPAM"),
    "E.b-wide": dict(n=11, saw=49, mpam=11, note="Table 13-8 max: N=11 SAW=49 MPAM=11"),
    "overview-88": dict(n=7, saw=None, mpam=None, w_override=88, note="public overview SNP=88b; dest N=7"),
    "conserv-U68": dict(
        n=11,
        saw=None,
        mpam=None,
        w_override=88,
        qos=True,
        note="overview 88 minus S_keep=20 (N=11 dest + QoS4 stay)",
    ),
}


def pin_u(name: str) -> tuple[int, int, int, str]:
    p = PINS[name]
    if p.get("w_override") is not None:
        w = p["w_override"]
        s = s_keep(p["n"], qos=bool(p.get("qos")))
        return w, s, w - s, p["note"]
    w, s, u = usable(p["n"], p["saw"], p["mpam"])
    return w, s, u, p["note"]


def main() -> int:
    print("P-0198/M-5r2 CHI width → k   UNSIGNED / not silicon / not card-claim")
    print("spec: ARM IHI 0050E.b Table 13-8 (Snoop) / Table 13-9 (Data) / Table 13-18 (Size≤64B)")
    print("Issue E Data bus DW ∈ {128,256,512} bit = {16,32,64} B; 128 B beat is NOT legal (sensitivity only)")
    print()
    print(f"{'pin':14} {'W_snp':6} {'S_keep':6} {'U':5} note")
    us = {}
    for name in PINS:
        w, s, u, note = pin_u(name)
        us[name] = u
        print(f"{name:14} {w:6} {s:6} {u:5} {note}")
    print()
    print("U interval: "
          f"[{min(us.values())}, {max(us.values())}]   "
          f"KILL uses min U = {min(us.values())}")
    print()
    print(f"{'beat':6} {'BE':4} {'D':5} {'U':4} {'k':4} legal_E")
    ks = []
    for beat, legal in ((16, True), (32, True), (64, True), (128, False)):
        for with_be in (True, False):
            d = d_of(beat, with_be)
            for name, u in us.items():
                k = k_of(d, u)
                ks.append((beat, with_be, name, u, d, k, legal))
                if name in ("E.b-narrow", "overview-88", "conserv-U68", "E.b-wide"):
                    print(
                        f"{beat:4}B  {'Y' if with_be else 'n':4} {d:5} {u:4} {k:4} "
                        f"{'Y' if legal else 'N'}  {name}"
                    )
    k64 = [t[5] for t in ks if t[0] == 64]
    k128 = [t[5] for t in ks if t[0] == 128]
    print()
    print(f"64 B  k interval = [{min(k64)}, {max(k64)}]   (Issue E legal)")
    print(f"128 B k interval = [{min(k128)}, {max(k128)}]  (NOT Issue E; platform gen_config.py:529 sensitivity)")
    print(f"KILL judged at worst k = {max(k64 + k128)}")
    print()
    print("C_dat_off = 2  (Dat sub-rings; TMultiRing.cpp:223-231)")
    print("C_snp_off = 1")
    for k in sorted(set([min(k64), max(k64), min(k128), max(k128)])):
        lo = 2.0 / (2.0 + 1.0 / k)
        print(f"  k={k:2}  T_dat/T_off ≥ 2/(2+1/k) = {lo:.4f}   C_dat_on ≤ 2+1/k = {2 + 1/k:.4f}")
    print("no wires added; no 1+duty_dat; k=1 is FAKE_WIDTH")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
