"""Ce qu'on garde d'un article : titre, extrait, lien, date et source. Rien d'autre."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Item:
    source: str
    title: str
    summary: str
    url: str
    published_at: datetime | None  # en UTC ; None si le flux ne donne pas de date

    def to_dict(self) -> dict[str, str | None]:
        return {
            "source": self.source,
            "title": self.title,
            "summary": self.summary,
            "url": self.url,
            "published_at": self.published_at.isoformat() if self.published_at else None,
        }
