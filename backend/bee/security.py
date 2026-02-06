from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class RiskEvent:
    timestamp: datetime
    action: str
    risk_score: int


@dataclass
class RiskMonitor:
    tolerance: int
    events: List[RiskEvent]
    halted: bool = False

    def log(self, action: str, risk_score: int) -> None:
        self.events.append(RiskEvent(datetime.utcnow(), action, risk_score))
        if risk_score >= self.tolerance:
            self.halted = True
