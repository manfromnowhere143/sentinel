# Iter146 qualification in progress

2026-10-10. Local independent replay supports 3,362 synthetic CPU steps and eight
replica pairs. All four arms exercised the 401-action cap. Sixty-four focused tests
passed with 38 warnings. Raw was committed at 4c36188c813c68aab2f16ebd5b281ea96de02300
before analysis. See proof/cpu_analysis.json and proof/commands/pre_gpu_tests.stdout.

Completion is explicitly the simulator's rc >= 1 criterion, approximately 90% of its
recorded route samples. Collision, off-route events and censoring override completion;
reward cannot determine success. Physical validity and literal route-end completion
remain unestablished. Prior Iter139/142 recovery nulls are unchanged.

The separately registered GPU qualification is being prepared; no new GPU episode has
run yet. Read GPU_QUALIFICATION_BINDING.md and STATE.json for its exact scope. The
14-scenario / 112-slot study remains proposed and unadmitted.
