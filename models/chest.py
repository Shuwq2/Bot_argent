"""
Module gérant le système de coffres et le tirage d'objets.
"""
import random
from typing import List, Optional

from models.item import Item, Rarity


class Chest:
    """Gère le système de tirage d'objets depuis les coffres."""

    def __init__(self, items: List[Item]):
        """
        Initialise le coffre avec la liste des objets disponibles.
        
        Args:
            items: Liste de tous les objets du jeu
        """
        self.items = items
        self._items_by_rarity = self._organize_by_rarity()

    def _organize_by_rarity(self) -> dict:
        """Organise les objets par rareté pour un tirage plus efficace."""
        organized = {rarity: [] for rarity in Rarity}
        for item in self.items:
            organized[item.rarity].append(item)
        return organized

    def open(self, drop_bonus: float = 0.0) -> Optional[Item]:
        """
        Ouvre un coffre et retourne un objet aléatoire selon les taux de drop.
        
        Args:
            drop_bonus: Bonus de taux de drop (ex: 0.05 = +5% sur les raretés supérieures)
        
        Returns:
            L'objet obtenu ou None si erreur
        """
        # Déterminer la rareté avec le bonus
        rarity = self._roll_rarity(drop_bonus)
        
        # Sélectionner un objet aléatoire de cette rareté
        items_of_rarity = self._items_by_rarity.get(rarity, [])
        if not items_of_rarity:
            # Fallback sur Normal si pas d'items de cette rareté
            items_of_rarity = self._items_by_rarity.get(Rarity.NORMAL, [])
        
        if items_of_rarity:
            return random.choice(items_of_rarity)
        return None

    def _roll_rarity(self, drop_bonus: float = 0.0) -> Rarity:
        """
        Effectue le tirage de rareté basé sur les probabilités.
        Le bonus augmente les chances des raretés supérieures.
        
        Args:
            drop_bonus: Bonus appliqué aux raretés rares+
        
        Returns:
            La rareté tirée
        """
        roll = random.random()  # Entre 0 et 1
        cumulative = 0.0
        
        # Ordre du plus rare au moins rare pour le tirage
        # Le bonus augmente les chances des raretés supérieures
        rarities_data = [
            (Rarity.MYTHIC, Rarity.MYTHIC.drop_rate * (1 + drop_bonus * 2)),     
            (Rarity.LEGENDARY, Rarity.LEGENDARY.drop_rate * (1 + drop_bonus * 1.5)),
            (Rarity.EPIC, Rarity.EPIC.drop_rate * (1 + drop_bonus)),
            (Rarity.RARE, Rarity.RARE.drop_rate * (1 + drop_bonus * 0.5)),
            (Rarity.NORMAL, 1.0)  # Le reste va à Normal
        ]
        
        for rarity, rate in rarities_data[:-1]:  # Exclure Normal du calcul
            cumulative += rate
            if roll < cumulative:
                return rarity
        
        return Rarity.NORMAL  # Fallback

    def get_drop_rates_display(self) -> str:
        """Retourne un affichage formaté des taux de drop."""
        lines = ["**📊 Taux de drop:**"]
        for rarity in Rarity:
            percentage = rarity.drop_rate * 100
            lines.append(f"{rarity.emoji} {rarity.display_name}: {percentage:.1f}%")
        return "\n".join(lines)
