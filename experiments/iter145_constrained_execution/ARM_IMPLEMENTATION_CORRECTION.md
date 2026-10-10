# Braking-arm implementation correction before deployment

Review against Iter143 CASE_FAMILY_PROTOCOL and Iter144 study.py found that the
initial Iter145 bridge's unexercised forced-brake branch used indefinite -2 m/s²
and zero steering. That contradicted the proposed one-second pulse, signed-speed
stopping law and preserved nominal steering. No brake-arm episode or measurement
ran with those bytes; the96 retained integration steps are nominal-arm fixtures.

Correct before deployment: use -sign(v)*min(2,abs(v)/.25) during [0,1) or [2.5,3.5),
preserve qualified nominal steering, and resume nominal acceleration afterward.
Test positive/negative/zero speeds, no overshoot through zero, onset and end.
The monitor arm still delivers its separate zeroed-plan proposal when it triggers.
No scientific-study admission or arm outcome is created by this correction.
