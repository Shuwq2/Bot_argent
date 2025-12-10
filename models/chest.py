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

    def open(self) -> Optional[Item]:
        """
        Ouvre un coffre et retourne un objet aléatoire selon les taux de drop.
        
        Returns:
            L'objet obtenu ou None si erreur
        """
        # Déterminer la rareté
        rarity = self._roll_rarity()
        
        # Sélectionner un objet aléatoire de cette rareté
        items_of_rarity = self._items_by_rarity.get(rarity, [])
        if not items_of_rarity:
            # Fallback sur Normal si pas d'items de cette rareté
            items_of_rarity = self._items_by_rarity.get(Rarity.NORMAL, [])
        
        if items_of_rarity:
            return random.choice(items_of_rarity)
        return None

    def _roll_rarity(self) -> Rarity:
        """
        Effectue le tirage de rareté basé sur les probabilités.
        
        Returns:
            La rareté tirée
        """
        roll = random.random()  # Entre 0 et 1
        cumulative = 0.0
        
        # Ordre du plus rare au moins rare pour le tirage
        rarities_order = [
            Rarity.MYTHIC,    # 1%
            Rarity.LEGENDARY, # 4%
            Rarity.EPIC,      # 15%
            Rarity.RARE,      # 30%
            Rarity.NORMAL     # 50%
        ]
        
        for rarity in rarities_order:
            cumulative += rarity.drop_rate
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
