"""Pure route walking for the opt-in development telemetry producer."""

import math


def haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6_371_000 * 2 * math.atan2(math.sqrt(h), math.sqrt(1 - h))


def bearing_deg(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlon = lon2 - lon1
    y = math.sin(dlon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


class RouteWalker:
    def __init__(self, coordinates: list[tuple[float, float]], start_progress_m: float):
        self.coordinates = coordinates
        self.segment_lengths = [
            haversine_m(coordinates[index], coordinates[index + 1])
            for index in range(len(coordinates) - 1)
        ]
        self.total_length_m = sum(self.segment_lengths)
        self.progress_m = min(max(start_progress_m, 0.0), self.total_length_m)
        self.direction = 1

    def point_at(self, progress_m: float) -> tuple[float, float]:
        remaining = min(max(progress_m, 0.0), self.total_length_m)
        for index, segment_length in enumerate(self.segment_lengths):
            if remaining <= segment_length or index == len(self.segment_lengths) - 1:
                start = self.coordinates[index]
                end = self.coordinates[index + 1]
                ratio = 0.0 if segment_length <= 0 else remaining / segment_length
                return (
                    start[0] + (end[0] - start[0]) * ratio,
                    start[1] + (end[1] - start[1]) * ratio,
                )
            remaining -= segment_length
        return self.coordinates[-1]

    def step(self, distance_m: float) -> tuple[float, float, float]:
        next_progress = self.progress_m + distance_m * self.direction
        if next_progress >= self.total_length_m:
            overflow = next_progress - self.total_length_m
            self.progress_m = max(0.0, self.total_length_m - overflow)
            self.direction = -1
        elif next_progress <= 0.0:
            overflow = -next_progress
            self.progress_m = min(self.total_length_m, overflow)
            self.direction = 1
        else:
            self.progress_m = next_progress

        position = self.point_at(self.progress_m)
        lookahead = min(
            max(self.progress_m + (12.0 * self.direction), 0.0),
            self.total_length_m,
        )
        target = self.point_at(lookahead)
        heading = bearing_deg(position, target) if target != position else 0.0
        return position[0], position[1], heading
