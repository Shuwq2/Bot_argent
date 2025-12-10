"""
Module de gestion des données persistantes (JSON).
Gère la sauvegarde et le chargement des joueurs et objets.
"""
import json
import os
from typing import Dict, List, Optional

from models.item import Item
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
        
        self._ensure_data_folder()
        self._items_cache: Dict[str, Item] = {}
        self._players_cache: Dict[int, Player] = {}
        
        self._load_items()
        self._load_players()

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
