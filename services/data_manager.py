"""
Module de gestion des données persistantes (JSON).
Gère la sauvegarde et le chargement des joueurs et objets.
"""
import json
import os
from typing import Dict, List, Optional

from models.item import Item, Pet, EquipmentSet
from models.player import Player


class DataManager:
    """Gestionnaire de données pour la persistance JSON."""

    def __init__(self, data_folder: str = "data"):
        """
        Initialise le gestionnaire de données.
        
        Args:
            data_folder: Dossier contenant les fichiers de données
        """
        self.data_folder = data_folder
        self.players_file = os.path.join(data_folder, "players.json")
        self.items_file = os.path.join(data_folder, "items.json")
        self.pets_file = os.path.join(data_folder, "pets.json")
        self.sets_file = os.path.join(data_folder, "sets.json")
        
        self._ensure_data_folder()
        self._items_cache: Dict[str, Item] = {}
        self._players_cache: Dict[int, Player] = {}
        self._pets_cache: Dict[str, Pet] = {}
        self._sets_cache: Dict[str, EquipmentSet] = {}
        self._egg_cost: int = 5000
        self._egg_drop_rates: Dict[str, float] = {}
        
        self._load_items()
        self._load_players()
        self._load_pets()
        self._load_sets()

    def _ensure_data_folder(self) -> None:
        """Crée le dossier de données s'il n'existe pas."""
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)

    # ==================== GESTION DES OBJETS ====================

    def _load_items(self) -> None:
        """Charge les objets depuis le fichier JSON."""
        if os.path.exists(self.items_file):
            with open(self.items_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item_data in data.get("items", []):
                    item = Item.from_dict(item_data)
                    self._items_cache[item.item_id] = item

    def get_item(self, item_id: str) -> Optional[Item]:
        """Récupère un objet par son ID."""
        return self._items_cache.get(item_id)

    def get_all_items(self) -> List[Item]:
        """Retourne la liste de tous les objets."""
        return list(self._items_cache.values())

    # ==================== GESTION DES PETS ====================

    def _load_pets(self) -> None:
        """Charge les pets depuis le fichier JSON."""
        if os.path.exists(self.pets_file):
            with open(self.pets_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._egg_cost = data.get("egg_cost", 5000)
                self._egg_drop_rates = data.get("egg_drop_rates", {})
                for pet_data in data.get("pets", []):
                    pet = Pet.from_dict(pet_data)
                    self._pets_cache[pet.pet_id] = pet

    def get_pet(self, pet_id: str) -> Optional[Pet]:
        """Récupère un pet par son ID."""
        return self._pets_cache.get(pet_id)

    def get_all_pets(self) -> List[Pet]:
        """Retourne la liste de tous les pets."""
        return list(self._pets_cache.values())

    def get_egg_cost(self) -> int:
        """Retourne le coût d'un œuf."""
        return self._egg_cost

    def get_egg_drop_rates(self) -> Dict[str, float]:
        """Retourne les taux de drop des œufs."""
        return self._egg_drop_rates

    # ==================== GESTION DES SETS ====================

    def _load_sets(self) -> None:
        """Charge les sets d'équipement depuis le fichier JSON."""
        if os.path.exists(self.sets_file):
            with open(self.sets_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for set_data in data.get("sets", []):
                    equipment_set = EquipmentSet.from_dict(set_data)
                    self._sets_cache[equipment_set.set_id] = equipment_set

    def get_set(self, set_id: str) -> Optional[EquipmentSet]:
        """Récupère un set par son ID."""
        return self._sets_cache.get(set_id)

    def get_all_sets(self) -> List[EquipmentSet]:
        """Retourne la liste de tous les sets."""
        return list(self._sets_cache.values())

    def get_equipped_set_pieces(self, player: Player) -> Dict[str, int]:
        """
        Compte le nombre de pièces équipées par set.
        Retourne un dict {set_id: nombre_de_pièces}.
        """
        set_counts: Dict[str, int] = {}
        for item_id in player.get_equipped_items():
            item = self.get_item(item_id)
            if item and item.set_id:
                set_counts[item.set_id] = set_counts.get(item.set_id, 0) + 1
        return set_counts

    def get_set_bonuses(self, player: Player) -> Dict[str, dict]:
        """
        Calcule les bonus de set actifs pour un joueur.
        Retourne un dict {set_id: bonus_actif}.
        """
        set_pieces = self.get_equipped_set_pieces(player)
        active_bonuses: Dict[str, dict] = {}
        
        for set_id, count in set_pieces.items():
            equipment_set = self.get_set(set_id)
            if equipment_set:
                if count >= 4:
                    active_bonuses[set_id] = {
                        "set_name": equipment_set.name,
                        "pieces": count,
                        "bonus": equipment_set.bonus_4
                    }
                elif count >= 2:
                    active_bonuses[set_id] = {
                        "set_name": equipment_set.name,
                        "pieces": count,
                        "bonus": equipment_set.bonus_2
                    }
        
        return active_bonuses

    def calculate_total_drop_bonus(self, player: Player) -> float:
        """
        Calcule le bonus total de taux de drop pour un joueur.
        Inclut: pet équipé + bonus de sets.
        """
        total_bonus = 0.0
        
        # Bonus du pet équipé
        if player.equipped_pet:
            pet = self.get_pet(player.equipped_pet)
            if pet:
                total_bonus += pet.drop_bonus
        
        # Bonus des sets
        set_bonuses = self.get_set_bonuses(player)
        for set_id, bonus_info in set_bonuses.items():
            bonus = bonus_info.get("bonus", {})
            total_bonus += bonus.get("drop_bonus", 0.0)
        
        return total_bonus

    def calculate_total_coin_bonus(self, player: Player) -> float:
        """
        Calcule le bonus total de pièces pour un joueur.
        Inclut: bonus de sets.
        """
        total_bonus = 0.0
        
        # Bonus des sets
        set_bonuses = self.get_set_bonuses(player)
        for set_id, bonus_info in set_bonuses.items():
            bonus = bonus_info.get("bonus", {})
            total_bonus += bonus.get("coin_bonus", 0.0)
        
        return total_bonus

    # ==================== GESTION DES JOUEURS ====================

    def _load_players(self) -> None:
        """Charge les joueurs depuis le fichier JSON."""
        if os.path.exists(self.players_file):
            with open(self.players_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for player_data in data.get("players", []):
                    player = Player.from_dict(player_data)
                    self._players_cache[player.user_id] = player

    def _save_players(self) -> None:
        """Sauvegarde tous les joueurs dans le fichier JSON."""
        players_data = {
            "players": [player.to_dict() for player in self._players_cache.values()]
        }
        with open(self.players_file, 'w', encoding='utf-8') as f:
            json.dump(players_data, f, ensure_ascii=False, indent=2)

    def get_player(self, user_id: int) -> Player:
        """
        Récupère un joueur par son ID Discord.
        Crée un nouveau joueur si inexistant.
        """
        if user_id not in self._players_cache:
            self._players_cache[user_id] = Player(user_id=user_id)
            self._save_players()
        return self._players_cache[user_id]

    def save_player(self, player: Player) -> None:
        """Sauvegarde un joueur spécifique."""
        self._players_cache[player.user_id] = player
        self._save_players()

    def save_all(self) -> None:
        """Sauvegarde toutes les données."""
        self._save_players()

    # ==================== STATISTIQUES ====================

    def get_leaderboard(self, limit: int = 10) -> List[Player]:
        """Retourne le classement des joueurs par richesse."""
        sorted_players = sorted(
            self._players_cache.values(),
            key=lambda p: p.coins,
            reverse=True
        )
        return sorted_players[:limit]

    def get_collection_leaderboard(self, limit: int = 10) -> List[Player]:
        """Retourne le classement par nombre d'objets uniques."""
        sorted_players = sorted(
            self._players_cache.values(),
            key=lambda p: len(p.inventory),
            reverse=True
        )
        return sorted_players[:limit]
