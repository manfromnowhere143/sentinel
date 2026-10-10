# Explicit SLSQP-to-refinement handoff

The shorter-horizon development suite v4 passed36 tests and failed one: the
from-rest curved fixture's refinement replay compared previous_objective against
the last SLSQP callback. As with the earlier no-refinement case, that callback is
not guaranteed to be result.x. The old raw28-input certificate remains supported
under its committed checker; those bytes and that claim scope stay unchanged.

Before further integration measurements, controller record v2 stores the actual
SLSQP returned input and every refinement's previous input. The checker uses that
explicit handoff, verifies each previous input against the preceding accepted
input, and verifies final equality whether or not refinement ran. No algorithm,
objective, threshold or iteration cap changes. Retain the development failure;
do not call its rejected execution a completed simulator qualification.
