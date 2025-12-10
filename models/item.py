"""
Module définissant les objets collectibles du jeu.
"""
from enum import Enum
from dataclasses import dataclass


class Rarity(Enum):
    """Énumération des raretés disponibles avec leurs taux de drop."""
    NORMAL = ("Normal", 0.50, "⬜", 10)       # 50% de chance, emoji, valeur de base
    RARE = ("Rare", 0.30, "🟦", 50)           # 30% de chance
    EPIC = ("Epic", 0.15, "🟪", 200)          # 15% de chance
    LEGENDARY = ("Légendaire", 0.04, "🟨", 1000)  # 4% de chance
    MYTHIC = ("Mythique", 0.01, "🟥", 5000)   # 1% de chance

    def __init__(self, display_name: str, drop_rate: float, emoji: str, base_value: int):
        self.display_name = display_name
        self.drop_rate = drop_rate
        self.emoji = emoji
        self.base_value = base_value


@dataclass
class Item:
    """Représente un objet collectible."""
    item_id: str
    name: str
    rarity: Rarity
    description: str
    value: int  # Valeur en pièces
    category: str

    def to_dict(self) -> dict:
        """Convertit l'objet en dictionnaire pour la sauvegarde."""
        return {
            "item_id": self.item_id,
            "name": self.name,
            "rarity": self.rarity.name,
            "description": self.description,
            "value": self.value,
            "category": self.category
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Item":
        """Crée un Item à partir d'un dictionnaire."""
        return cls(
            item_id=data["item_id"],
            name=data["name"],
            rarity=Rarity[data["rarity"]],
            description=data["description"],
            value=data["value"],
            category=data["category"]
        )

    def get_display(self) -> str:
        """Retourne l'affichage formaté de l'objet."""
        return f"{self.rarity.emoji} **{self.name}** ({self.rarity.display_name}) - {self.value} 💰"
