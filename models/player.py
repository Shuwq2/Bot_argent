"""
Module définissant les joueurs et leur inventaire.
"""
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict


@dataclass
class Player:
    """Représente un joueur avec son inventaire et ses statistiques."""
    user_id: int
    coins: int = 0
    inventory: Dict[str, int] = field(default_factory=dict)  # item_id -> quantité
    daily_chests_opened: int = 0
    last_chest_date: str = ""
    total_chests_opened: int = 0
    total_items_sold: int = 0

    # Constantes de jeu
    MAX_DAILY_CHESTS = 50
    CHEST_COST = 3500  # Coût pour ouvrir un coffre supplémentaire

    def can_open_free_chest(self) -> bool:
        """Vérifie si le joueur peut ouvrir un coffre gratuitement."""
        self._reset_daily_if_needed()
        return self.daily_chests_opened < self.MAX_DAILY_CHESTS

    def get_remaining_free_chests(self) -> int:
        """Retourne le nombre de coffres gratuits restants."""
        self._reset_daily_if_needed()
        return max(0, self.MAX_DAILY_CHESTS - self.daily_chests_opened)

    def can_afford_chest(self) -> bool:
        """Vérifie si le joueur peut payer pour un coffre supplémentaire."""
        return self.coins >= self.CHEST_COST

    def open_chest(self, paid: bool = False) -> bool:
        """
        Tente d'ouvrir un coffre.
        Retourne True si réussi, False sinon.
        """
        self._reset_daily_if_needed()
        
        if not paid and self.can_open_free_chest():
            self.daily_chests_opened += 1
            self.total_chests_opened += 1
            return True
        elif paid and self.can_afford_chest():
            self.coins -= self.CHEST_COST
            self.total_chests_opened += 1
            return True
        return False

    def add_item(self, item_id: str, quantity: int = 1) -> None:
        """Ajoute un objet à l'inventaire."""
        if item_id in self.inventory:
            self.inventory[item_id] += quantity
        else:
            self.inventory[item_id] = quantity

    def remove_item(self, item_id: str, quantity: int = 1) -> bool:
        """Retire un objet de l'inventaire. Retourne True si réussi."""
        if item_id not in self.inventory or self.inventory[item_id] < quantity:
            return False
        
        self.inventory[item_id] -= quantity
        if self.inventory[item_id] <= 0:
            del self.inventory[item_id]
        return True

    def add_coins(self, amount: int) -> None:
        """Ajoute des pièces au joueur."""
        self.coins += amount

    def sell_item(self, item_id: str, item_value: int, quantity: int = 1) -> bool:
        """Vend un objet et ajoute les pièces correspondantes."""
        if self.remove_item(item_id, quantity):
            self.add_coins(item_value * quantity)
            self.total_items_sold += quantity
            return True
        return False

    def _reset_daily_if_needed(self) -> None:
        """Réinitialise le compteur journalier si nécessaire."""
        today = date.today().isoformat()
        if self.last_chest_date != today:
            self.daily_chests_opened = 0
            self.last_chest_date = today

    def to_dict(self) -> dict:
        """Convertit le joueur en dictionnaire pour la sauvegarde."""
        return {
            "user_id": self.user_id,
            "coins": self.coins,
            "inventory": self.inventory,
            "daily_chests_opened": self.daily_chests_opened,
            "last_chest_date": self.last_chest_date,
            "total_chests_opened": self.total_chests_opened,
            "total_items_sold": self.total_items_sold
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Player":
        """Crée un Player à partir d'un dictionnaire."""
        return cls(
            user_id=data["user_id"],
            coins=data.get("coins", 0),
            inventory=data.get("inventory", {}),
            daily_chests_opened=data.get("daily_chests_opened", 0),
            last_chest_date=data.get("last_chest_date", ""),
            total_chests_opened=data.get("total_chests_opened", 0),
            total_items_sold=data.get("total_items_sold", 0)
        )
