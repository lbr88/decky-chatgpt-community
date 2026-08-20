from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class OperationResult:
    ok: bool
    message: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
