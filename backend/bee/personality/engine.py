from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Personality:
    essence: str = "B.E.E. - calm, precise, hive-minded"
    traits: dict[str, float] = field(default_factory=lambda: {
        "curiosity": 0.6,
        "discipline": 0.7,
        "warmth": 0.5,
        "directness": 0.8,
    })
    last_evolved: datetime | None = None

    def evolve(self, delta: dict[str, float]) -> None:
        for key, value in delta.items():
            self.traits[key] = max(0.0, min(1.0, self.traits.get(key, 0.5) + value))
        self.last_evolved = datetime.utcnow()

    def summary(self) -> str:
        trait_summary = ", ".join(f"{k}:{v:.2f}" for k, v in self.traits.items())
        return f"{self.essence} ({trait_summary})"
