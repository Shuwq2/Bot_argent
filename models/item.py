"""
Module définissant les objets collectibles du jeu.
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List


class Rarity(Enum):
    """Énumération des raretés disponibles avec leurs taux de drop."""
    NORMAL = ("Normal", 0.70, "⬜", 10)        # 70% de chance
    RARE = ("Rare", 0.20, "🟦", 50)            # 20% de chance
    EPIC = ("Epic", 0.065, "🟪", 200)          # 6.5% de chance
    LEGENDARY = ("Légendaire", 0.01, "🟨", 1000)   # 1% de chance
    MYTHIC = ("Mythique", 0.0015, "🟥", 5000)   # 0.15% de chance

    def __init__(self, display_name: str, drop_rate: float, emoji: str, base_value: int):
        self.display_name = display_name
        self.drop_rate = drop_rate
        self.emoji = emoji
        self.base_value = base_value


class ItemType(Enum):
    """Type d'objet pour l'équipement."""
    HELMET = ("Casque", "🪖")
    CHESTPLATE = ("Plastron", "🛡️")
    LEGGINGS = ("Jambières", "👖")
    BOOTS = ("Bottes", "👢")
    WEAPON = ("Arme", "⚔️")
    ACCESSORY = ("Accessoire", "💍")
    CONSUMABLE = ("Consommable", "🧪")
    MATERIAL = ("Matériau", "📦")
    PET_EGG = ("Œuf de Pet", "🥚")

    def __init__(self, display_name: str, emoji: str):
        self.display_name = display_name
        self.emoji = emoji


@dataclass
class Item:
    """Représente un objet collectible."""
    item_id: str
    name: str
    rarity: Rarity
    description: str
    value: int  # Valeur en pièces
    category: str
    item_type: Optional[str] = None  # Type d'équipement
    set_id: Optional[str] = None     # ID du set d'équipement
    stats: Optional[dict] = None     # Stats de l'item (attaque, défense, etc.)

    def to_dict(self) -> dict:
        """Convertit l'objet en dictionnaire pour la sauvegarde."""
        data = {
            "item_id": self.item_id,
            "name": self.name,
            "rarity": self.rarity.name,
            "description": self.description,
            "value": self.value,
            "category": self.category
        }
        if self.item_type:
            data["item_type"] = self.item_type
        if self.set_id:
            data["set_id"] = self.set_id
        if self.stats:
            data["stats"] = self.stats
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Item":
        """Crée un Item à partir d'un dictionnaire."""
        return cls(
            item_id=data["item_id"],
            name=data["name"],
            rarity=Rarity[data["rarity"]],
            description=data["description"],
            value=data["value"],
            category=data["category"],
            item_type=data.get("item_type"),
            set_id=data.get("set_id"),
            stats=data.get("stats")
        )

    def is_equipable(self) -> bool:
        """Vérifie si l'item peut être équipé."""
        return self.item_type in ["HELMET", "CHESTPLATE", "LEGGINGS", "BOOTS", "WEAPON", "ACCESSORY"]

    def get_display(self) -> str:
        """Retourne l'affichage formaté de l'objet."""
        return f"{self.rarity.emoji} **{self.name}** ({self.rarity.display_name}) - {self.value} 💰"


@dataclass
class Pet:
    """Représente un pet avec bonus de drop."""
    pet_id: str
    name: str
    rarity: Rarity
    description: str
    drop_bonus: float  # Bonus de taux de drop (ex: 0.02 = +2%)
    emoji: str

    def to_dict(self) -> dict:
        return {
            "pet_id": self.pet_id,
            "name": self.name,
            "rarity": self.rarity.name,
            "description": self.description,
            "drop_bonus": self.drop_bonus,
            "emoji": self.emoji
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Pet":
        return cls(
            pet_id=data["pet_id"],
            name=data["name"],
            rarity=Rarity[data["rarity"]],
            description=data["description"],
            drop_bonus=data["drop_bonus"],
            emoji=data["emoji"]
        )


@dataclass
class EquipmentSet:
    """Définit un set d'équipement avec bonus."""
    set_id: str
    name: str
    pieces: List[str]  # Liste des item_ids qui composent le set
    bonus_2: dict      # Bonus avec 2 pièces
    bonus_4: dict      # Bonus avec 4 pièces (set complet)
    description: str

    def to_dict(self) -> dict:
        return {
            "set_id": self.set_id,
            "name": self.name,
            "pieces": self.pieces,
            "bonus_2": self.bonus_2,
            "bonus_4": self.bonus_4,
            "description": self.description
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EquipmentSet":
        return cls(
            set_id=data["set_id"],
            name=data["name"],
            pieces=data["pieces"],
            bonus_2=data["bonus_2"],
            bonus_4=data["bonus_4"],
            description=data["description"]
        )
