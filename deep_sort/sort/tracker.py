# vim: expandtab:ts=4:sw=4
from __future__ import absolute_import
import numpy as np
from . import kalman_filter
from . import linear_assignment
from . import iou_matching
from .track import Track


class Tracker:
    """
    This is the multi-target tracker.
    Parameters
    ----------
    metric : nn_matching.NearestNeighborDistanceMetric
        A distance metric for measurement-to-track association.
    max_age : int
        Maximum number of missed misses before a track is deleted.
    n_init : int
        Number of consecutive detections before the track is confirmed. The
        track state is set to `Deleted` if a miss occurs within the first
        `n_init` frames.
    Attributes
    ----------
    metric : nn_matching.NearestNeighborDistanceMetric
        The distance metric used for measurement to track association.
    max_age : int
        Maximum number of missed misses before a track is deleted.
    n_init : int
        Number of frames that a track remains in initialization phase.
    kf : kalman_filter.KalmanFilter
        A Kalman filter to filter target trajectories in image space.
    tracks : List[Track]
        The list of active tracks at the current time step.
    """
    GATING_THRESHOLD = np.sqrt(kalman_filter.chi2inv95[4])

    def __init__(self, metric, max_iou_distance=0.9, max_age=30, n_init=3, _lambda=0, _alpha=0):
        self.metric = metric
        self.max_iou_distance = max_iou_distance
        self.max_age = max_age
        self.n_init = n_init
        self._lambda = _lambda
        self._alpha = _alpha

        self.kf = kalman_filter.KalmanFilter()
        self.tracks = []
        self._next_id = 1

    def predict(self):
        """Propagate track state distributions one time step forward.

        This function should be called once every time step, before `update`.
        """
        for track in self.tracks:
            track.predict(self.kf)

    def increment_ages(self):
        for track in self.tracks:
            track.increment_age()
            track.mark_missed()

    def update(self, detections, classes):
        """Perform measurement update and track management.

        Parameters
        ----------
        detections : List[deep_sort.detection.Detection]
            A list of detections at the current time step.

        """
        # Run matching cascade.
        matches, unmatched_tracks, unmatched_detections = \
            self._match(detections)

        # Update track set.
        for track_idx, detection_idx in matches:
            self.tracks[track_idx].update(
                self.kf, detections[detection_idx], classes[detection_idx])
        for track_idx in unmatched_tracks:
            self.tracks[track_idx].mark_missed()
        for detection_idx in unmatched_detections:
            self._initiate_track(detections[detection_idx], classes[detection_idx].item())
        self.tracks = [t for t in self.tracks if not t.is_deleted()]

        # Update distance metric.
        active_targets = [t.track_id for t in self.tracks if t.is_confirmed()]
        features, targets = [], []
        for track in self.tracks:
            if not track.is_confirmed():
                continue
            features += track.features
            targets += [track.track_id for _ in track.features]
            track.features = []
        self.metric.partial_fit(np.asarray(features), np.asarray(targets), active_targets)

    def _full_cost_metric(self, tracks, dets, track_indices, detection_indices):
        """
        This implements the full lambda-based cost-metric. However, in doing so, it disregards
        the possibility to gate the position only which is provided by
        linear_assignment.gate_cost_matrix(). Instead, I gate by everything.
        Note that the Mahalanobis distance is itself an unnormalised metric. Given the cosine
        distance being normalised, we employ a quick and dirty normalisation based on the
        threshold: that is, we divide the positional-cost by the gating threshold, thus ensuring
        that the valid values range 0-1.
        Note also that the authors work with the squared distance. I also sqrt this, so that it
        is more intuitive in terms of values.
        """
        # Compute First the Position-based Cost Matrix
        pos_cost = np.empty([len(track_indices), len(detection_indices)])
        msrs = np.asarray([dets[i].to_xyah() for i in detection_indices])
        for row, track_idx in enumerate(track_indices):
            pos_cost[row, :] = np.sqrt(
                self.kf.gating_distance(
                    tracks[track_idx].mean, tracks[track_idx].covariance, msrs, False
                )
            ) / self.GATING_THRESHOLD
        pos_gate = pos_cost > 1.0
        # Compute the IOU-based Cost Matrix
        iou_cost = iou_matching.iou_cost(tracks, dets, track_indices, detection_indices)
        # Now Compute the Appearance-based Cost Matrix
        app_cost = self.metric.distance(
            np.array([dets[i].feature for i in detection_indices]),
            np.array([tracks[i].track_id for i in track_indices]),
        )
        app_gate = app_cost > self.metric.matching_threshold
        # print('pos_min: ', pos_cost.min(), 'app_min: ', app_cost.min())
        # print('iou_min: ', iou_cost.min(), 'iou_mean: ', iou_cost.mean(), 'iou_max: ', iou_cost.max())
        # print('pos: ', pos_gate.shape, pos_gate.size, pos_gate.sum())
        # print('app: ', app_gate.shape, app_gate.size, app_gate.sum())
        # Now combine and threshold
        cost_matrix = self._lambda * pos_cost + self._alpha * iou_cost + (1 - self._lambda - self._alpha) * app_cost
        # cost_matrix[app_gate] = linear_assignment.INFTY_COST
        # cost_matrix[pos_gate] = linear_assignment.INFTY_COST
        cost_matrix[np.logical_or(pos_gate, app_gate)] = linear_assignment.INFTY_COST
        # a = np.logical_or(pos_gate, app_gate)
        # print('cost matrix: ', cost_matrix.shape, cost_matrix.size, a.sum())
        # Return Matrix
        return cost_matrix

    # def _match(self, detections):
    #     # Split track set into confirmed and unconfirmed tracks.
    #     confirmed_tracks = [i for i, t in enumerate(self.tracks) if t.is_confirmed()]
    #     unconfirmed_tracks = [i for i, t in enumerate(self.tracks) if not t.is_confirmed()]
    #
    #     # Associate confirmed tracks using appearance features.
    #     matches_a, unmatched_tracks_a, unmatched_detections = linear_assignment.matching_cascade(
    #         self._full_cost_metric,
    #         linear_assignment.INFTY_COST - 1,  # no need for self.metric.matching_threshold here,
    #         self.max_age,
    #         self.tracks,
    #         detections,
    #         confirmed_tracks,
    #     )
    #
    #     # Associate remaining tracks together with unconfirmed tracks using IOU.
    #     iou_track_candidates = unconfirmed_tracks + [
    #         k for k in unmatched_tracks_a if self.tracks[k].time_since_update == 1
    #     ]
    #     unmatched_tracks_a = [
    #         k for k in unmatched_tracks_a if self.tracks[k].time_since_update != 1
    #     ]
    #     matches_b, unmatched_tracks_b, unmatched_detections = linear_assignment.min_cost_matching(
    #         iou_matching.iou_cost,
    #         self.max_iou_distance,
    #         self.tracks,
    #         detections,
    #         iou_track_candidates,
    #         unmatched_detections,
    #     )
    #
    #     matches = matches_a + matches_b
    #     unmatched_tracks = list(set(unmatched_tracks_a + unmatched_tracks_b))
    #     return matches, unmatched_tracks, unmatched_detections

    def _match(self, detections):
        # Split track set into confirmed and unconfirmed tracks.
        confirmed_tracks = [i for i, t in enumerate(self.tracks) if t.is_confirmed()]
        unconfirmed_tracks = [i for i, t in enumerate(self.tracks) if not t.is_confirmed()]

        det_candidates_high = []
        det_candidates_low = []
        for i in range(len(detections)):
            if detections[i].confidence > 0.7:
                det_candidates_high.append(i)
            elif detections[i].confidence > 0.2:
                det_candidates_low.append(i)

        matches_a, unmatched_tracks_a, unmatched_detections_high = linear_assignment.min_cost_matching(
            self._full_cost_metric,
            linear_assignment.INFTY_COST - 1,
            self.tracks,
            detections,
            confirmed_tracks,
            det_candidates_high,
        )

        matches_b, unmatched_tracks_b, unmatched_detections_high = linear_assignment.min_cost_matching(
            iou_matching.iou_cost,
            self.max_iou_distance,
            self.tracks,
            detections,
            unconfirmed_tracks,
            unmatched_detections_high,
        )

        # Associate remaining tracks together with unconfirmed tracks using IOU.
        iou_track_candidates = unmatched_tracks_a + unmatched_tracks_b

        matches_c, unmatched_tracks_c, unmatched_detections_low = linear_assignment.min_cost_matching(
            iou_matching.iou_cost,
            self.max_iou_distance - 0.3,
            self.tracks,
            detections,
            iou_track_candidates,
            det_candidates_low,
        )

        matches = matches_a + matches_b + matches_c
        # unmatched_tracks = list(set(unmatched_tracks_a + unmatched_tracks_b))
        unmatched_tracks = list(set(unmatched_tracks_c))
        return matches, unmatched_tracks, unmatched_detections_high

    def _initiate_track(self, detection, class_id):
        mean, covariance = self.kf.initiate(detection.to_xyah())
        self.tracks.append(Track(
            mean, covariance, self._next_id, class_id, self.n_init, self.max_age,
            detection.feature))
        self._next_id += 1
