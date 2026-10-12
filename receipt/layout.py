from dataclasses import dataclass

from receipt.vision import TextObservation


@dataclass
class ReceiptLine:
    observations: list[TextObservation]

    @property
    def text(self) -> str:
        ordered = sorted(self.observations, key=lambda obs: obs.x)
        return "    ".join(obs.text for obs in ordered)

    @property
    def y(self) -> float:
        return sum(obs.y for obs in self.observations) / len(self.observations)


def reconstruct_lines(
    observations: list[TextObservation],
    y_tolerance: float = 0.008,
) -> list[ReceiptLine]:

    observations = sorted(observations, key=lambda obs: -obs.y)

    lines: list[ReceiptLine] = []

    for observation in observations:

        best_line = None
        best_distance = float("inf")

        for line in lines:
            distance = abs(observation.y - line.y)

            if distance <= y_tolerance and distance < best_distance:
                best_line = line
                best_distance = distance

        if best_line is None:
            lines.append(ReceiptLine(observations=[observation]))
        else:
            best_line.observations.append(observation)

    return sorted(lines, key=lambda line: -line.y)