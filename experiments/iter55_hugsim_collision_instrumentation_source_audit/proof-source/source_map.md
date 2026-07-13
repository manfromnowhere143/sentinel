# Iteration 55 - HUGSIM collision instrumentation source map

Verdict: `COLLISION_INSTRUMENTATION_SOURCE_MAP_COMPLETE`

## Checkout

- HEAD: `62c690d39fd90020e68a196bd8bcc1c4d4191f2e`
- Expected: `62c690d39fd90020e68a196bd8bcc1c4d4191f2e`
- SHA match: `True`

## Labels

- `metric_source_identified`: `True`
- `collision_geometry_source_identified`: `True`
- `actor_identity_available_in_source`: `True`
- `instrumentation_point_supported`: `True`
- `source_map_insufficient`: `False`

## Candidate Instrumentation Points

- `sim/utils/score_calculator.py` score `826` actor_identity `True`
- `closed_loop.py` score `224` actor_identity `True`

## Ranked Source Files

### `sim/utils/score_calculator.py`

- score `826`, metric `True`, geometry `True`, identity `True`
- line `31` terms `ttc`: `'ttc': 5,`
- line `51` terms `box, collision`: `def bg_collision_det(points, box):`
- line `52` terms `box`: `O, A, B, C = box[0], box[1], box[2], box[5]`

### `data/kitti360/annotation.py`

- score `351`, metric `False`, geometry `False`, identity `True`
- line `71` terms `box, object`: `# Class that contains the information of a single annotated object as 3D bounding box`
- line `83` terms `id, object`: `# the ID of the corresponding object`
- line `88` terms `bbox`: `# the window that contains the bbox`

### `data/InverseForm/library/data/cityscapes_labels.py`

- score `322`, metric `False`, geometry `False`, identity `True`
- line `23` terms `contact`: `# Contact`
- line `40` terms `name`: `'name'        , # The identifier of this label, e.g. 'car', 'person', ... .`
- line `41` terms `name`: `# We use them to uniquely name a class`

### `sim/hugsim_env/envs/hug_sim.py`

- score `321`, metric `False`, geometry `True`, identity `True`
- line `9` terms `collision`: `from sim.utils.score_calculator import create_rectangle, bg_collision_det`
- line `21` terms `box, collision`: `def fg_collision_det(ego_box, objs):`
- line `22` terms `box`: `ego_x, ego_y, _, ego_w, ego_l, ego_h, ego_yaw = ego_box`

### `data/colmap/colmap_reader.py`

- score `309`, metric `False`, geometry `False`, identity `True`
- line `9` terms `contact`: `# For inquiries contact  george.drettakis@inria.fr`
- line `17` terms `id, name`: `"CameraModel", ["model_id", "model_name", "num_params"])`
- line `19` terms `id`: `"Camera", ["id", "model", "width", "height", "params"])`

### `utils/semantic_utils.py`

- score `300`, metric `False`, geometry `False`, identity `False`
- line `18` terms `name`: `'name'        , # The identifier of this label, e.g. 'car', 'person', ... .`
- line `19` terms `name`: `# We use them to uniquely name a class`
- line `21` terms `id`: `'id'          , # An integer ID that is associated with this label.`

### `data/waymo/load.py`

- score `297`, metric `False`, geometry `False`, identity `True`
- line `18` terms `vehicle`: `type_list = ['UNKNOWN', 'VEHICLE', 'PEDESTRIAN', 'SIGN', 'CYCLIST']`
- line `37` terms `box`: `bottom_center: center of bottom face of 3D bounding box`
- line `39` terms `box`: `return: vertices of 3D bounding box (8*3)`

### `submodules/Pplan/utils/geometry_utils.py`

- score `282`, metric `False`, geometry `False`, identity `True`
- line `92` terms `box`: `def get_box_world_coords(pos, yaw, extent):`
- line `104` terms `box`: `def get_upright_box(pos, extent):`
- line `106` terms `box`: `boxes = get_box_world_coords(pos, yaws, extent)`

### `data/InverseForm/utils/misc.py`

- score `242`, metric `False`, geometry `False`, identity `False`
- line `31` terms `id`: `# TP exist where value == num_classes*class_id + class_id`
- line `128` terms `object`: `You pass images/tensors from training pipeline into this object and it first`
- line `140` terms `name`: `:webpage_fn: name of webpage file`

### `data/nusc/utils.py`

- score `242`, metric `False`, geometry `False`, identity `True`
- line `44` terms `vehicle`: `"vehicle.car",`
- line `45` terms `vehicle`: `"vehicle.bicycle",`
- line `46` terms `vehicle`: `"vehicle.motorcycle",`

### `data/nusc/load.py`

- score `236`, metric `False`, geometry `False`, identity `True`
- line `16` terms `bbox`: `get_vertices, point_in_bbox, frame_check, get_sample_pose, load_cam,`
- line `17` terms `box`: `traj_dict_to_list, get_box)`
- line `32` terms `name`: `if __name__ == "__main__":`

### `closed_loop.py`

- score `224`, metric `True`, geometry `True`, identity `True`
- line `27` terms `.write`: `clip.write_videofile(output_path)`
- line `58` terms `open(`: `with open(obs_pipe, "wb") as pipe:`
- line `59` terms `.dump, .write`: `pipe.write(pickle.dumps((obs, info)))`

## Boundary

source-map only; no HUGSIM run, actor match, safety, transfer, benchmark, or retuning claim
