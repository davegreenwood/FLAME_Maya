# -----------------------------------------------------------------------------
# Hack of the model loading tool due to opencv problems with Maya
# -----------------------------------------------------------------------------


# the sys append could be performed at maya start
import sys
sys.path.append(
    '/Users/Shared/anaconda2/envs/maya2016/lib/python2.7/site-packages')

import numpy as np
import cPickle as pickle
import chumpy as ch


def rodrigues(r):
    '''
    Rodrigues formula
    Input: 1x3 array of rotations about x, y, and z
    Output: 3x3 rotation matrix
    '''
    def S(n):
        Sn = np.array([[0, -n[2], n[1]], [n[2], 0, -n[0]], [-n[1], n[0], 0]])
        return Sn

    theta = np.linalg.norm(r)

    if theta > 1e-30:
        n = r / theta
        Sn = S(n)
        R = np.eye(3) + np.sin(theta) * Sn + \
            (1 - np.cos(theta)) * np.dot(Sn, Sn)
    else:
        Sr = S(r)
        theta2 = theta**2
        R = np.eye(3) + (1 - theta2 / 6.) * Sr + \
            (.5 - theta2 / 24.) * np.dot(Sr, Sr)

    return R


class Rodrigues(ch.Ch):
    dterms = 'rt'

    def compute_r(self):
        return rodrigues(self.rt.r)

    def compute_dr_wrt(self, wrt):
        if wrt is self.rt:
            raise NotImplementedError()


def with_zeros(x):
    return ch.vstack((x, ch.array([[0.0, 0.0, 0.0, 1.0]])))


def pack(x):
    return ch.hstack([np.zeros((4, 3)), x.reshape((4, 1))])


def posemap(s):
    if s == 'lrotmin':
        return lrotmin
    else:
        raise Exception('Unknown posemapping: %s' % (str(s),))


def lrotmin(p):
    if isinstance(p, np.ndarray):
        p = p.ravel()[3:]
        return np.concatenate(
            [(rodrigues(np.array(pp)) - np.eye(3)).ravel()
             for pp in p.reshape((-1, 3))]).ravel()
    if p.ndim != 2 or p.shape[1] != 3:
        p = p.reshape((-1, 3))
    p = p[1:]
    return ch.concatenate([
        (rodrigues(pp) - ch.eye(3)).ravel() for pp in p]).ravel()


def global_rigid_transformation(pose, J, kintree_table):
    def _rodrigues(x):
        return Rodrigues(x)
    results = {}
    pose = pose.reshape((-1, 3))
    id_to_col = {kintree_table[1, i]: i for i in range(kintree_table.shape[1])}
    parent = {i: id_to_col[kintree_table[0, i]]
              for i in range(1, kintree_table.shape[1])}

    results[0] = with_zeros(
        ch.hstack((_rodrigues(pose[0, :]), J[0, :].reshape((3, 1)))))

    for i in range(1, kintree_table.shape[1]):
        results[i] = results[parent[i]].dot(
            with_zeros(ch.hstack((_rodrigues(pose[i, :]),
                                  ((J[i, :] - J[parent[i], :]).reshape((3, 1)))
                                  ))))

    results = [results[i] for i in sorted(results.keys())]
    results_global = results

    if True:
        results2 = [results[i] - (pack(
            results[i].dot(ch.concatenate(((J[i, :]), 0))))
        ) for i in range(len(results))]
        results = results2
    result = ch.dstack(results)
    return result, results_global


def verts_core(pose, v, J, weights, kintree_table, want_Jtr=False):
    A, A_global = global_rigid_transformation(pose, J, kintree_table)
    T = A.dot(weights.T)

    rest_shape_h = ch.vstack((v.T, np.ones((1, v.shape[0]))))

    v = (T[:, 0, :] * rest_shape_h[0, :].reshape((1, -1)) +
         T[:, 1, :] * rest_shape_h[1, :].reshape((1, -1)) +
         T[:, 2, :] * rest_shape_h[2, :].reshape((1, -1)) +
         T[:, 3, :] * rest_shape_h[3, :].reshape((1, -1))).T

    v = v[:, :3]

    if not want_Jtr:
        return v
    Jtr = ch.vstack([g[:3, 3] for g in A_global])
    return (v, Jtr)


def ready_arguments(fname_or_dict):

    if not isinstance(fname_or_dict, dict):
        dd = pickle.load(open(fname_or_dict))
    else:
        dd = fname_or_dict

    want_shapemodel = 'shapedirs' in dd
    nposeparms = dd['kintree_table'].shape[1] * 3

    if 'trans' not in dd:
        dd['trans'] = np.zeros(3)
    if 'pose' not in dd:
        dd['pose'] = np.zeros(nposeparms)
    if 'shapedirs' in dd and 'betas' not in dd:
        dd['betas'] = np.zeros(dd['shapedirs'].shape[-1])

    for s in ['v_template', 'weights', 'posedirs', 'pose',
              'trans', 'shapedirs', 'betas', 'J']:
        if (s in dd) and not hasattr(dd[s], 'dterms'):
            dd[s] = ch.array(dd[s])

    if want_shapemodel:
        dd['v_shaped'] = dd['shapedirs'].dot(dd['betas']) + dd['v_template']
        v_shaped = dd['v_shaped']
        J_tmpx = ch.MatVecMult(dd['J_regressor'], v_shaped[:, 0])
        J_tmpy = ch.MatVecMult(dd['J_regressor'], v_shaped[:, 1])
        J_tmpz = ch.MatVecMult(dd['J_regressor'], v_shaped[:, 2])
        dd['J'] = ch.vstack((J_tmpx, J_tmpy, J_tmpz)).T
        dd['v_posed'] = v_shaped + \
            dd['posedirs'].dot(posemap(dd['bs_type'])(dd['pose']))
    else:
        dd['v_posed'] = dd['v_template'] + \
            dd['posedirs'].dot(posemap(dd['bs_type'])(dd['pose']))

    return dd


def load_model(fname_or_dict):
    dd = ready_arguments(fname_or_dict)
    args = {
        'pose': dd['pose'],
        'v': dd['v_posed'],
        'J': dd['J'],
        'weights': dd['weights'],
        'kintree_table': dd['kintree_table'],
        'want_Jtr': True,
    }

    result, Jtr = verts_core(**args)
    result = result + dd['trans'].reshape((1, 3))
    result.J_transformed = Jtr + dd['trans'].reshape((1, 3))

    for k, v in dd.items():
        setattr(result, k, v)

    return result
