"""Streetak key art: a real one-hand grip on the ball at the hip (founder, 5 Nov: «وضعية إيده مع الكورة مش ماسكة خالص»).

The reference (players posing with a ball at their side): the arm hangs a little away from the body, the ball is held
against the hip, the palm on its outer side and the fingers spread and wrapped round it, the thumb over the front.

From a bone dump of the hero in the old pose (kadump.py), this:
  1. turns the hand so the palm faces the body and the fingers point down and a little forward;
  2. bends each finger (one factor per finger over its three joints) until its tip just touches the ball;
  3. puts the ball between the palm and the hip, and reports the gaps (fingers, hip/thigh).
It writes the new local rotations as new poses (ballholdG / ballholdGM) into poses.json, next to the old ones.

usage: python3 grip_solver.py poses.json dump_left.json dump_right.json out_poses.json
"""
import json
import sys

import numpy as np
from scipy.spatial.transform import Rotation as Rot

R_BALL = 11.0
PALM_GAP = 1.6      # palm skin to the leather
TIP_GAP = 0.9       # a fingertip's pad
FINGERS = ["index", "middle", "ring", "pinky"]


def unit(v):
    v = np.asarray(v, float)
    return v / max(1e-9, np.linalg.norm(v))


class Skel:
    def __init__(self, dump):
        self.B = dump["bones"]
        self.local = {n: Rot.from_quat(b["l_q"]) for n, b in self.B.items()}
        self.lt = {n: np.array(b["l_t"]) for n, b in self.B.items()}

    def fk(self, names_needed):
        cs = {}

        def get(n):
            if n in cs:
                return cs[n]
            p = self.B[n]["parent"]
            if p not in self.B:
                r, t = Rot.from_quat(self.B[n]["cs_q"]), np.array(self.B[n]["cs_t"])
            else:
                pr, pt = get(p)
                r, t = pr * self.local[n], pt + pr.apply(self.lt[n])
            cs[n] = (r, t)
            return cs[n]

        for n in names_needed:
            get(n)
        return cs


def solve(dump, side, base_pose):
    sx = 1.0 if side == "l" else -1.0
    S = Skel(dump)
    b = lambda n: f"{n}_{side}"
    chain = [b("hand")] + [b(f"{f}_{k}") for f in FINGERS for k in ("metacarpal", "01", "02", "03")] + \
            [b(f"thumb_{k}") for k in ("01", "02", "03")] + [b("thigh"), "pelvis", b("lowerarm")]
    cs = S.fk(chain)
    H_r, H_t = cs[b("hand")]
    m1, m3 = cs[b("middle_01")][1], cs[b("middle_03")][1]
    f_old = unit(m1 - H_t)
    t = m3 - m1
    n_old = unit(t - t.dot(f_old) * f_old)
    # 1. the new hand frame: fingers down and a little forward (+Y is towards the camera), palm towards the body
    f_new = unit([0.0, 0.42, -1.0])
    n_new = np.array([-sx, 0.0, 0.0])
    n_new = unit(n_new - n_new.dot(f_new) * f_new)
    Fo = np.column_stack([f_old, n_old, np.cross(f_old, n_old)])
    Fn = np.column_stack([f_new, n_new, np.cross(f_new, n_new)])
    delta = Rot.from_matrix(Fn @ Fo.T)
    lower_r = cs[b("lowerarm")][0]
    S.local[b("hand")] = lower_r.inv() * (delta * H_r)

    # the fingers' curl as it is now (rotation vectors) and a scale per finger
    base = {n: S.local[n] for n in S.local}
    def set_curl(f, k):
        for j in ("01", "02", "03"):
            n = b(f"{f}_{j}")
            S.local[n] = Rot.from_rotvec(base[n].as_rotvec() * k)

    def palm_and_ball():
        c = S.fk(chain)
        pts = [c[b("hand")][1]] + [c[b(f"{f}_01")][1] for f in FINGERS]
        palm = np.mean(pts, axis=0)
        hr = c[b("hand")][0]
        # the palm normal from the new frame (delta applied): n_new by construction
        ball = palm + n_new * (R_BALL + PALM_GAP)
        return c, palm, ball

    def tip(c, f):
        r3, t3 = c[b(f"{f}_03")]
        return t3 + r3.apply(unit(S.lt[b(f"{f}_03")])) * 2.2

    # 2. per finger: the curl factor whose tip lands on the ball (a bisection on k in [0, 1.6])
    c, palm, ball = palm_and_ball()
    report = {}
    for f in FINGERS:
        lo, hi = 0.0, 1.6
        for _ in range(30):
            k = (lo + hi) / 2
            set_curl(f, k)
            c = S.fk(chain)
            d = np.linalg.norm(tip(c, f) - ball) - R_BALL
            if d > TIP_GAP:
                lo = k          # not touching yet: bend more
            else:
                hi = k
        set_curl(f, hi)
        c = S.fk(chain)
        joints_in = min(np.linalg.norm(c[b(f"{f}_{j}")][1] - ball) - R_BALL for j in ("01", "02", "03"))
        report[f] = dict(k=round(hi, 3), tip_gap=round(float(np.linalg.norm(tip(c, f) - ball) - R_BALL), 2),
                         min_joint_gap=round(float(joints_in), 2))
    # the thumb: left as the hand carries it (over the front of the ball); report its gap
    c, palm, ball = palm_and_ball()
    th = min(np.linalg.norm(c[b(f"thumb_{j}")][1] - ball) - R_BALL for j in ("01", "02", "03"))
    # 3. the hip: the ball against the thigh's top (the thigh bone line from thigh to ~40 cm down)
    th_t = c[b("thigh")][1]
    hip_d = np.linalg.norm((ball - th_t) * np.array([1, 1, 0]))   # horizontal distance to the hip joint's line
    report["thumb_gap"] = round(float(th), 2)
    report["ball"] = [round(float(x), 1) for x in ball]
    report["palm"] = [round(float(x), 1) for x in palm]
    report["hip_horizontal"] = round(float(hip_d), 1)
    out = json.loads(json.dumps(base_pose))
    for n in [b("hand")] + [b(f"{f}_{j}") for f in FINGERS for j in ("01", "02", "03")]:
        q = S.local[n].as_quat()
        out.setdefault(n, {"t": list(S.lt[n])})
        out[n] = {"q": [float(x) for x in q], "t": out[n].get("t", list(S.lt[n]))}
    return out, report


if __name__ == "__main__":
    poses_p, dl, dr, out_p = sys.argv[1:5]
    data = json.load(open(poses_p))
    L = json.load(open(dl))
    Rr = json.load(open(dr))
    pg, rep = solve(L, "l", data["poses"]["ballhold"])
    print("ballholdG", json.dumps(rep))
    pgm, repm = solve(Rr, "r", data["poses"]["ballholdM"])
    print("ballholdGM", json.dumps(repm))
    data["poses"]["ballholdG"] = pg
    data["poses"]["ballholdGM"] = pgm
    data["anchors"]["ballholdG"] = data["anchors"]["ballhold"]
    data["anchors"]["ballholdGM"] = data["anchors"]["ballholdM"]
    json.dump(data, open(out_p, "w"))
