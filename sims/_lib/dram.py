"""Parameterized DRAM black box (假设 H-DRAM-BB). Not this machine; not silicon.

Cycle-accurate only for the timing constraints listed below. Everything else
(refresh FSM, ranks, TSV, PHY, scheduler IQ) is omitted. Warm-up in the
driver discards the cold row-buffer prefix; refresh is not modeled.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field


@dataclass
class DramTiming:
    # 假设 H-DRAM-BB — abstract cycles, clock UNKNOWN
    tRCD: int = 14
    tCL: int = 14
    tRP: int = 14
    tRAS: int = 32
    tRTP: int = 8
    tRRD_S: int = 4
    tRRD_L: int = 6
    tCCD_S: int = 4
    tCCD_L: int = 6
    tFAW: int = 16
    tBURST: int = 8
    n_bank: int = 48
    n_bg: int = 8
    page_policy: str = "open"  # open | close
    row_shift: int = 15
    n_dmc: int = 384


@dataclass
class _Bank:
    open_row: int | None = None
    last_act: int = -10**9
    last_cas: int = -10**9
    last_pre: int = -10**9


@dataclass
class _Dmc:
    banks: list[_Bank] = field(default_factory=list)
    last_act: list[int] = field(default_factory=list)
    last_act_any: int = -10**9
    last_cas: list[int] = field(default_factory=list)
    last_cas_any: int = -10**9
    bus_free: int = 0
    acts: deque = field(default_factory=deque)
    hits: int = 0
    misses: int = 0
    empties: int = 0


class BlackBoxDRAM:
    def __init__(self, timing: DramTiming | None = None):
        self.t = timing or DramTiming()
        self.dmcs = [_fresh_dmc(self.t) for _ in range(self.t.n_dmc)]

    def row_of(self, phys: int) -> int:
        return phys >> self.t.row_shift

    def bg_of(self, bank: int) -> int:
        return bank % self.t.n_bg

    def complete_at(self, arrive: int, dmc: int, bank: int, phys: int) -> int:
        if not (0 <= dmc < self.t.n_dmc) or not (0 <= bank < self.t.n_bank):
            raise ValueError(f"illegal dmc/bank {dmc}/{bank}")
        t = self.t
        ch = self.dmcs[dmc]
        b = ch.banks[bank]
        bg = self.bg_of(bank)
        row = self.row_of(phys)

        need_act = True
        t_now = arrive
        if t.page_policy == "open" and b.open_row == row:
            need_act = False
            ch.hits += 1
        elif t.page_policy == "open" and b.open_row is None:
            ch.empties += 1
        elif t.page_policy == "open":
            ch.misses += 1
            t_pre = max(t_now, b.last_cas + t.tRTP, b.last_act + t.tRAS, b.last_pre)
            t_now = t_pre + t.tRP
            b.last_pre = t_pre
            b.open_row = None
        else:
            # close-page: bank is empty on arrival (precharged after last use)
            if b.open_row is not None:
                t_pre = max(t_now, b.last_cas + t.tRTP, b.last_act + t.tRAS, b.last_pre)
                t_now = t_pre + t.tRP
                b.last_pre = t_pre
                b.open_row = None
            ch.misses += 1

        if need_act:
            t_act = self._act_legal(ch, bg, t_now)
            t_act = max(t_act, b.last_pre + t.tRP, b.last_act + 1)
            b.last_act = t_act
            b.open_row = row
            ch.last_act[bg] = t_act
            ch.last_act_any = t_act
            ch.acts.append(t_act)
            t_cas = t_act + t.tRCD
        else:
            t_cas = t_now

        same_bg = ch.last_cas[bg] >= 0
        t_ccd = t.tCCD_L if same_bg else t.tCCD_S
        t_cas = max(t_cas, ch.last_cas[bg] + t_ccd, ch.last_cas_any + t.tCCD_S, ch.bus_free, b.last_cas + t.tCCD_L)
        done = t_cas + t.tCL + t.tBURST
        b.last_cas = t_cas
        ch.last_cas[bg] = t_cas
        ch.last_cas_any = t_cas
        ch.bus_free = t_cas + t.tBURST

        if t.page_policy == "close":
            t_pre = max(t_cas + t.tRTP, b.last_act + t.tRAS)
            b.last_pre = t_pre
            b.open_row = None
        return done

    def _act_legal(self, ch: _Dmc, bg: int, t_now: int) -> int:
        t = self.t
        t_act = t_now
        last_same = ch.last_act[bg]
        last_any = ch.last_act_any
        if last_same > -10**8:
            t_act = max(t_act, last_same + t.tRRD_L)
        if last_any > -10**8:
            t_act = max(t_act, last_any + t.tRRD_S)
        while ch.acts and ch.acts[0] <= t_act - t.tFAW:
            ch.acts.popleft()
        if len(ch.acts) >= 4:
            t_act = max(t_act, ch.acts[0] + t.tFAW)
            while ch.acts and ch.acts[0] <= t_act - t.tFAW:
                ch.acts.popleft()
        return t_act

    def row_stats(self) -> dict:
        h = sum(c.hits for c in self.dmcs)
        m = sum(c.misses for c in self.dmcs)
        e = sum(c.empties for c in self.dmcs)
        return {"row_hit": h, "row_miss": m, "row_empty": e}


def _fresh_dmc(t: DramTiming) -> _Dmc:
    return _Dmc(
        banks=[_Bank() for _ in range(t.n_bank)],
        last_act=[-10**9] * t.n_bg,
        last_cas=[-10**9] * t.n_bg,
    )
