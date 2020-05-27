import mne
import torch

from collections import Iterable
from torch.utils.data.dataset import random_split


class DN3ConfigException(BaseException):
    """
    Exception to be triggered when DN3-configuration parsing fails.
    """
    pass


def rand_split(dataset, frac=0.75):
    if frac >= 1:
        return dataset
    samples = len(dataset)
    return random_split(dataset, lengths=[round(x) for x in [samples*frac, samples*(1-frac)]])


def unfurl(_set: set):
    _list = list(_set)
    for i in range(len(_list)):
        if not isinstance(_list[i], Iterable):
            _list[i] = [_list[i]]
    return tuple(x for z in _list for x in z)


def min_max_normalize(x: torch.Tensor):
    if len(x.shape) == 2:
        return (x - x.min()) / (x.max() - x.min())
    elif len(x.shape) == 3:
        return (x - torch.min(torch.min(x, keepdim=True, dim=-1)[0], keepdim=True, dim=-1)[0]) / \
               (torch.max(torch.max(x, keepdim=True, dim=-1)[0], keepdim=True, dim=-1)[0] -
                torch.min(torch.min(x, keepdim=True, dim=-1)[0], keepdim=True, dim=-1)[0])


def make_epochs_from_raw(raw: mne.io.Raw, tmin, tlen, event_ids=None, baseline=None, decim=1, filter_bp=None,
                         drop_bad=False, use_annotations=False):
    sfreq = raw.info['sfreq']
    if filter_bp is not None:
        if isinstance(filter_bp, (list, tuple)) and len(filter_bp) == 2:
            raw.load_data()
            raw.filter(filter_bp[0], filter_bp[1])
        else:
            print('Filter must be provided as a two-element list [low, high]')

    try:
        if use_annotations:
            events = mne.events_from_annotations(raw, event_id=event_ids)[0]
        else:
            events = mne.find_events(raw)
    except ValueError as e:
        raise DN3ConfigException(*e.args)

    return mne.Epochs(raw, events, tmin=tmin, tmax=tmin + tlen - 1 / sfreq, preload=True, decim=decim,
                      baseline=baseline, reject_by_annotation=drop_bad)