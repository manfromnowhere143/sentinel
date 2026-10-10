import sys
sys.path.append('')
import argparse
import cv2
import torch
import sklearn
import mmcv
import os
import warnings
from mmcv import Config, DictAction
from mmcv.cnn import fuse_conv_bn
from mmcv.parallel import MMDataParallel, MMDistributedDataParallel
from mmcv.runner import (get_dist_info, init_dist, load_checkpoint,
                         wrap_fp16_model)

from mmdet3d.apis import single_gpu_test
# from mmdet3d.datasets import build_dataset
# from projects.mmdet3d_plugin.datasets.builder import build_dataloader
from mmdet3d.models import build_model
from mmdet.apis import set_random_seed
# from projects.mmdet3d_plugin.uniad.apis.test import custom_multi_gpu_test
from mmdet.datasets import replace_ImageToTensor
import time
import os.path as osp
import numpy as np
from queue import Queue
import pickle
from mmdet3d.core import Box3DMode
from dataparser import parse_raw
from tools.closeloop.visualizer import draw_bev, draw_proj
from visualizer import save_visualize_img, to_video
import multiprocessing

warnings.filterwarnings("ignore")


# ---- Sentinel iter48: released union, client-side port (frozen NeuroNCAP params) --------
# Decision rule and parameters are the iteration-15 released union exactly as replay-verified
# in iteration 42. SENTINEL_ENABLED gates behavior: OFF arm returns the plan untouched.
import json as _sjson, math as _smath, os as _sos

_S48_PARAMS = {
    "cpa_margin": float(_sos.environ.get("SENTINEL_CPA_MARGIN", "1.5")),
    "ttc_thresh": float(_sos.environ.get("SENTINEL_TTC", "2.5")),
    "min_closing": float(_sos.environ.get("SENTINEL_MIN_CLOSING", "3.0")),
    "max_gap": float(_sos.environ.get("SENTINEL_MAXGAP", "30.0")),
    "min_score": float(_sos.environ.get("SENTINEL_MIN_SCORE", "0.3")),
    "release_k": int(_sos.environ.get("SENTINEL_RELEASE_K", "4")),
    "dt": 0.5,
}
_S48_ENABLED = _sos.environ.get("SENTINEL_ENABLED", "0") == "1"
_s48_state = {"frame": -1, "braking": False, "clear": 0}
_s48_track = {}
print("SENTINEL_I48_UNION_PATCH_LOADED enabled=%d params=%s"
      % (1 if _S48_ENABLED else 0, _sjson.dumps(_S48_PARAMS, sort_keys=True)), flush=True)


def _s48_write(output_dir, row):
    try:
        with open(_sos.path.join(output_dir, "sentinel_iter48_decisions.jsonl"), "a") as f:
            f.write(_sjson.dumps(row, sort_keys=True) + "\n")
    except Exception:
        pass


def _sentinel_i48_intervene(plan_traj, result, data, output_dir):
    if not _S48_ENABLED:
        return plan_traj
    _s48_state["frame"] += 1
    try:
        p = _S48_PARAMS
        base = [[float(x), float(y)] for x, y in plan_traj.tolist()]
        boxes = result["boxes_3d"]
        centers = boxes.gravity_center.numpy()
        scores = result["scores_3d"].numpy()
        ids = result["track_ids"].numpy()
        R = data["l2g_r_mat"].detach().cpu().numpy().reshape(3, 3)
        t = data["l2g_t"].detach().cpu().numpy().reshape(3)
        ts = float(data["timestamp"])  # HUGSIM: seconds
        pre_braking = bool(_s48_state["braking"])
        pre_clear = int(_s48_state["clear"])
        ego_wx, ego_wy = float(t[0]), float(t[1])
        ego_world_plan = []
        for px, py in base:
            w = R @ np.array([px, py, 0.0]) + t
            ego_world_plan.append((float(w[0]), float(w[1])))
        H = len(ego_world_plan)
        min_cpa = 1e9
        min_ttc = 1e9
        newtrack = {}
        objs_log = []
        for i in range(min(len(centers), len(scores))):
            sc = float(scores[i])
            if not _smath.isfinite(sc) or sc < p["min_score"]:
                continue
            ox, oy = float(centers[i][0]), float(centers[i][1])
            if _smath.hypot(ox, oy) > p["max_gap"]:
                continue
            w = R @ np.array([ox, oy, 0.0]) + t
            wx, wy = float(w[0]), float(w[1])
            oid = int(ids[i]) if i < len(ids) else "idx_%d" % i
            newtrack[oid] = (wx, wy, ts)
            avx = avy = 0.0
            if oid in _s48_track:
                pwx, pwy, pts = _s48_track[oid]
                dta = ts - pts  # seconds already (unit-correct NeuroNCAP mechanism)
                if dta > 1e-3:
                    avx, avy = (wx - pwx) / dta, (wy - pwy) / dta
            for k in range(H):
                th = (k + 1) * p["dt"]
                ax, ay = wx + avx * th, wy + avy * th
                ex, ey = ego_world_plan[k]
                d = _smath.hypot(ex - ax, ey - ay)
                if d < min_cpa:
                    min_cpa = d
            dx, dy = ego_wx - wx, ego_wy - wy
            gapw = _smath.hypot(dx, dy)
            if gapw > 1e-3:
                closing = (avx * dx + avy * dy) / gapw
                if closing > max(p["min_closing"], 0.5):
                    ttc = gapw / closing
                    if ttc < min_ttc:
                        min_ttc = ttc
            objs_log.append({"id": oid, "bev": [ox, oy], "world": [wx, wy],
                             "vel": [avx, avy], "score": sc})
        _s48_track.clear()
        _s48_track.update(newtrack)
        fired = min_cpa < p["cpa_margin"] or min_ttc < p["ttc_thresh"]
        release = False
        if fired:
            _s48_state["braking"] = True
            _s48_state["clear"] = 0
        elif _s48_state["braking"]:
            _s48_state["clear"] += 1
            if _s48_state["clear"] >= p["release_k"]:
                _s48_state["braking"] = False
                _s48_state["clear"] = 0
                release = True
        brake = bool(_s48_state["braking"])
        _s48_write(output_dir, {
            "trace_version": "iter48_hugsim_union_v1",
            "frame_index": _s48_state["frame"],
            "ts": ts,
            "traj": base,
            "objs": objs_log,
            "l2g_t": [float(v) for v in t.tolist()],
            "l2g_r_mat": [[float(v) for v in row] for row in R.tolist()],
            "params": p,
            "pre_braking": pre_braking,
            "pre_clear": pre_clear,
            "min_cpa": float(min_cpa),
            "min_ttc": float(min_ttc),
            "fired": bool(fired),
            "post_braking": bool(_s48_state["braking"]),
            "post_clear": int(_s48_state["clear"]),
            "brake": brake,
            "release": bool(release),
        })
        print("SENTINEL_I48_DECISION frame=%d fired=%d brake=%d release=%d clear=%d "
              "min_cpa=%.4f min_ttc=%.4f objs=%d"
              % (_s48_state["frame"], int(fired), int(brake), int(release),
                 _s48_state["clear"], min_cpa, min_ttc, len(objs_log)), flush=True)
        if brake:
            return np.zeros_like(plan_traj)  # latched committed-stop trajectory
    except Exception as e:
        _s48_write(output_dir, {"trace_version": "iter48_hugsim_union_v1",
                                "trace_error": str(e),
                                "frame_index": _s48_state["frame"]})
        print("SENTINEL_I48_DECISION_ERROR frame=%d err=%s"
              % (_s48_state["frame"], str(e).replace("\n", " ")[:200]), flush=True)
    return plan_traj


def parse_args():
    parser = argparse.ArgumentParser(
        description='MMDet test (and eval) a model')
    parser.add_argument('config', help='test config file path')
    parser.add_argument('checkpoint', help='checkpoint file')
    parser.add_argument('--output', type=str, required=True)
    # parser.add_argument('--out', default='output/results.pkl', help='output result file in pickle format')
    parser.add_argument(
        '--fuse-conv-bn',
        action='store_true',
        help='Whether to fuse conv and bn, this will slightly increase'
        'the inference speed')
    parser.add_argument(
        '--format-only',
        action='store_true',
        help='Format the output results without perform evaluation. It is'
        'useful when you want to format the result to a specific format and '
        'submit it to the test server')
    parser.add_argument(
        '--eval',
        type=str,
        nargs='+',
        help='evaluation metrics, which depends on the dataset, e.g., "bbox",'
        ' "segm", "proposal" for COCO, and "mAP", "recall" for PASCAL VOC')
    parser.add_argument('--show', action='store_true', help='show results')
    parser.add_argument(
        '--show-dir', help='directory where results will be saved')
    parser.add_argument(
        '--gpu-collect',
        action='store_true',
        help='whether to use gpu to collect results.')
    parser.add_argument(
        '--tmpdir',
        help='tmp directory used for collecting results from multiple '
        'workers, available when gpu-collect is not specified')
    parser.add_argument('--seed', type=int, default=0, help='random seed')
    parser.add_argument(
        '--deterministic',
        action='store_true',
        help='whether to set deterministic options for CUDNN backend.')
    parser.add_argument(
        '--cfg-options',
        nargs='+',
        action=DictAction,
        help='override some settings in the used config, the key-value pair '
        'in xxx=yyy format will be merged into config file. If the value to '
        'be overwritten is a list, it should be like key="[a,b]" or key=a,b '
        'It also allows nested list/tuple values, e.g. key="[(a,b),(c,d)]" '
        'Note that the quotation marks are necessary and that no white space '
        'is allowed.')
    parser.add_argument(
        '--options',
        nargs='+',
        action=DictAction,
        help='custom options for evaluation, the key-value pair in xxx=yyy '
        'format will be kwargs for dataset.evaluate() function (deprecate), '
        'change to --eval-options instead.')
    parser.add_argument(
        '--eval-options',
        nargs='+',
        action=DictAction,
        help='custom options for evaluation, the key-value pair in xxx=yyy '
        'format will be kwargs for dataset.evaluate() function')
    parser.add_argument(
        '--launcher',
        choices=['none', 'pytorch', 'slurm', 'mpi'],
        default='none',
        help='job launcher')
    parser.add_argument('--local_rank', type=int, default=0)
    args = parser.parse_args()
    if 'LOCAL_RANK' not in os.environ:
        os.environ['LOCAL_RANK'] = str(args.local_rank)

    if args.options and args.eval_options:
        raise ValueError(
            '--options and --eval-options cannot be both specified, '
            '--options is deprecated in favor of --eval-options')
    if args.options:
        warnings.warn('--options is deprecated in favor of --eval-options')
        args.eval_options = args.options
    return args


def main():
    args = parse_args()

    if args.eval and args.format_only:
        raise ValueError('--eval and --format_only cannot be both specified')

    cfg = Config.fromfile(args.config)
    if args.cfg_options is not None:
        cfg.merge_from_dict(args.cfg_options)
    # import modules from string list.
    if cfg.get('custom_imports', None):
        from mmcv.utils import import_modules_from_strings
        import_modules_from_strings(**cfg['custom_imports'])

    # import modules from plguin/xx, registry will be updated
    if hasattr(cfg, 'plugin'):
        if cfg.plugin:
            import importlib
            if hasattr(cfg, 'plugin_dir'):
                plugin_dir = cfg.plugin_dir
                _module_dir = os.path.dirname(plugin_dir)
                _module_dir = _module_dir.split('/')
                _module_path = _module_dir[0]

                for m in _module_dir[1:]:
                    _module_path = _module_path + '.' + m
                print(_module_path)
                plg_lib = importlib.import_module(_module_path)
            else:
                # import dir is the dirpath for the config file
                _module_dir = os.path.dirname(args.config)
                _module_dir = _module_dir.split('/')
                _module_path = _module_dir[0]
                for m in _module_dir[1:]:
                    _module_path = _module_path + '.' + m
                print(_module_path)
                plg_lib = importlib.import_module(_module_path)

    # set cudnn_benchmark
    if cfg.get('cudnn_benchmark', False):
        torch.backends.cudnn.benchmark = True

    cfg.model.pretrained = None
    # in case the test dataset is concatenated
    samples_per_gpu = 1
    if isinstance(cfg.data.test, dict):
        cfg.data.test.test_mode = True
        samples_per_gpu = cfg.data.test.pop('samples_per_gpu', 1)
        if samples_per_gpu > 1:
            # Replace 'ImageToTensor' to 'DefaultFormatBundle'
            cfg.data.test.pipeline = replace_ImageToTensor(
                cfg.data.test.pipeline)
    elif isinstance(cfg.data.test, list):
        for ds_cfg in cfg.data.test:
            ds_cfg.test_mode = True
        samples_per_gpu = max(
            [ds_cfg.pop('samples_per_gpu', 1) for ds_cfg in cfg.data.test])
        if samples_per_gpu > 1:
            for ds_cfg in cfg.data.test:
                ds_cfg.pipeline = replace_ImageToTensor(ds_cfg.pipeline)

    # init distributed env first, since logger depends on the dist info.
    if args.launcher == 'none':
        distributed = False
    else:
        distributed = True
        init_dist(args.launcher, **cfg.dist_params)

    # set random seeds
    if args.seed is not None:
        set_random_seed(args.seed, deterministic=args.deterministic)

    # build the model and load checkpoint
    cfg.model.train_cfg = None
    model = build_model(cfg.model, test_cfg=cfg.get('test_cfg'))
    fp16_cfg = cfg.get('fp16', None)
    if fp16_cfg is not None:
        wrap_fp16_model(model)
    checkpoint = load_checkpoint(model, args.checkpoint, map_location='cpu')
    if args.fuse_conv_bn:
        model = fuse_conv_bn(model)
    # old versions did not save class info in checkpoints, this walkaround is
    # for backward compatibility
    if 'CLASSES' in checkpoint.get('meta', {}):
        model.CLASSES = checkpoint['meta']['CLASSES']

    if 'PALETTE' in checkpoint.get('meta', {}):
        model.PALETTE = checkpoint['meta']['PALETTE']

    model = MMDataParallel(model, device_ids=[0]).eval()
    
    cameras = ['CAM_FRONT', 'CAM_FRONT_RIGHT', 'CAM_FRONT_LEFT',
               'CAM_BACK', 'CAM_BACK_LEFT', 'CAM_BACK_RIGHT']
    img_norm_cfg = {
        'mean': np.array([103.530, 116.280, 123.675]), 
        'std': np.array([1.0, 1.0, 1.0]), 
        'to_rgb': False
    }
    history = Queue()
    
    os.makedirs(args.output, exist_ok=True)
    obs_pipe = os.path.join(args.output, 'obs_pipe')
    plan_pipe = os.path.join(args.output, 'plan_pipe')
    if not os.path.exists(obs_pipe):
        os.mkfifo(obs_pipe)
    if not os.path.exists(plan_pipe):
        os.mkfifo(plan_pipe)
    print('Ready for recieving')
    cnt = 0
    vis_process_pool = []
    output_folder = os.path.join(args.output, 'uniad')
    os.makedirs(output_folder, exist_ok=True)
    while True:
        with open(obs_pipe, "rb") as pipe:
            raw_data = pipe.read()
            raw_data = pickle.loads(raw_data)
        print('received')
        
        if raw_data == 'Done':
            for process in vis_process_pool:
                process.join()
            to_video(output_folder)
            exit(0)

        data = parse_raw(raw_data, cameras, img_norm_cfg, history)
        raw_images = data['raw_imgs']
        del data['raw_imgs']

        try:
            with torch.no_grad():
                results = model(return_loss=False, rescale=True, **data)
        except RuntimeError as e:
            results = None
            print(e)
        
        # results post processing
        results[0]['planning_traj'] = results[0]['planning']['result_planning']['sdc_traj'].cpu().detach().numpy()
        results[0]['pts_bbox']['score_list'] = results[0]['pts_bbox']['score_list'].detach().cpu().numpy()
        results[0]['pts_bbox']['lane_score'] = results[0]['pts_bbox']['lane_score'].detach().cpu().numpy()
        results[0]['command'] = data['command'][0].cpu().detach().numpy()
        
        save_fn = osp.join(output_folder, f'{str(cnt).zfill(4)}')
        # single process
        # save_visualize_img(results[0], raw_images, save_fn)
        
        # multi-process

        if results is not None:
            plan_traj = results[0]['planning']['result_planning']['sdc_traj'][0].detach().cpu().numpy()
            from experiments.iter145_constrained_execution.client import deliver
            plan_traj = deliver(plan_traj, results[0], data, args.output,
                                _sentinel_i48_intervene, _S48_ENABLED, raw_data[1])
            with open(plan_pipe, "wb") as pipe:
                pipe.write(pickle.dumps(plan_traj))
            print('sent')
        else:
            with open(plan_pipe, "wb") as pipe:
                pipe.write(pickle.dumps(None))
            print('Waiting for visualize tasks...')
            for process in vis_process_pool:
                process.join()
            to_video(output_folder)
            exit(0)

        cnt += 1


if __name__ == '__main__':
    main()
