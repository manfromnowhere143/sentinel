# Correction to callback interpretation

The first replay of amended raw data optimizer_raw_v2.json returned invalid. Its
checker incorrectly required the last SLSQP callback input to equal the final
returned input even when no refinement ran. At integration case4 their maximum
coordinate difference is 8.637717708113025e-7. Callback observations are optimization
progress; the returned solution is separately retained and independently replayed.

Correct only that checker assumption: final equality with refinement history is
required when refinement exists. With no refinement, validate the actual returned
states, controls, objective and KKT certificate directly, without equating callback
and returned state. No raw data, solver, tolerance, population or result is changed.
The invalid replay and its diagnostic are retained. The corrected checker must be
committed before reinterpreting the same raw data and reject altered final controls.
