# Pre-measurement infrastructure amendment — 2026-10-09

Status: preregistered operational amendment. No benchmark call, host Python test, simulator
construction or driving episode has run in Iter137 at this amendment. Keep HYPOTHESIS.md intact.

The first start RPC lost its client connection (`No route to host`). The provider nevertheless
started the instance. The elapsed delay and subsequent session gap consumed the preparation
window. The agent stopped the instance immediately after readback. Provider timestamps show
11:59:19.860–12:57:23.678 UTC (about 58 minutes); final readback is TERMINATED. Do not call this
benchmark data or omit its resource cost. The retained client elapsed time and provider timestamps
are distinct observations; the exact source of the client/session delay is not established.

Before any measurement, permit one additional start of the same instance, bounded to 60 minutes
from that start, with these protections: asynchronous provider start; short client command timeouts;
a guest shutdown timer armed after identity and workload preflight; retain failed commands and
partial output. No replacement instance, corpus expansion, extra measured repetitions, measured
retry or changed decision criterion is permitted. Total instance budget across these two attempts
is at most 120 minutes. The second window includes setup, all 912 calls and independent replay.
Stop it early on completion. If that attempt cannot complete, retain the unobserved portion.

All source/input bindings, the eight-block order, 180-second block ceiling, 30-minute benchmark
ceiling, exact numerical equality rule and separate 50 ms accounting remain unchanged. This
amendment precedes measurement and changes only the infrastructure recovery budget and controls.
