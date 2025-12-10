"""
Module définissant les joueurs et leur inventaire.
"""
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, Optional, List


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
    
    # Système de pets
    pets: Dict[str, int] = field(default_factory=dict)  # pet_id -> quantité
    equipped_pet: Optional[str] = None  # pet_id équipé
    eggs_opened: int = 0  # Total d'oeufs ouverts
    
    # Système d'équipement
    equipment: Dict[str, Optional[str]] = field(default_factory=lambda: {
        "HELMET": None,
        "CHESTPLATE": None,
        "LEGGINGS": None,
        "BOOTS": None,
        "WEAPON": None,
        "ACCESSORY": None
    })
    
    # ═══════════════════════════════════════════════════════════
    # 📊 SYSTÈME DE NIVEAU ET COMBAT
    # ═══════════════════════════════════════════════════════════
    level: int = 1
    xp: int = 0
    total_xp: int = 0
    
    # Stats de combat de base (modifiées par équipement)
    base_hp: int = 100
    base_attack: int = 10
    base_defense: int = 5
    base_speed: int = 10
    
    # Stats de combat actuelles (en combat)
    current_hp: int = 100
    
    # Compétences débloquées (skill_id -> niveau)
    skills: Dict[str, int] = field(default_factory=dict)
    equipped_skills: List[str] = field(default_factory=list)  # Max 4 skills
    
    # Stats de boss
    bosses_defeated: int = 0
    bosses_kills: Dict[str, int] = field(default_factory=dict)  # boss_id -> kills
    last_boss_fight: str = ""  # Date du dernier combat
    
    # Skill points disponibles
    skill_points: int = 0

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

    def add_pet(self, pet_id: str, quantity: int = 1) -> None:
        """Ajoute un pet à la collection."""
        if pet_id in self.pets:
            self.pets[pet_id] += quantity
        else:
            self.pets[pet_id] = quantity

    def equip_pet(self, pet_id: str) -> bool:
        """Équipe un pet. Retourne True si réussi."""
        if pet_id in self.pets and self.pets[pet_id] > 0:
            self.equipped_pet = pet_id
            return True
        return False

    def unequip_pet(self) -> None:
        """Déséquipe le pet actuel."""
        self.equipped_pet = None

    def equip_item(self, item_id: str, slot: str) -> Optional[str]:
        """
        Équipe un item dans le slot spécifié.
        Retourne l'item_id précédemment équipé ou None.
        """
        if slot not in self.equipment:
            return None
        
        old_item = self.equipment[slot]
        self.equipment[slot] = item_id
        return old_item

    def unequip_item(self, slot: str) -> Optional[str]:
        """Déséquipe l'item du slot. Retourne l'item_id déséquipé."""
        if slot not in self.equipment:
            return None
        
        old_item = self.equipment[slot]
        self.equipment[slot] = None
        return old_item

    def get_equipped_items(self) -> List[str]:
        """Retourne la liste des item_ids équipés."""
        return [item_id for item_id in self.equipment.values() if item_id]

    # ═══════════════════════════════════════════════════════════
    # 📊 MÉTHODES DE NIVEAU
    # ═══════════════════════════════════════════════════════════
    
    def get_xp_for_level(self, level: int) -> int:
        """Calcule l'XP nécessaire pour atteindre un niveau."""
        # Formule exponentielle : 100 * level^1.8
        return int(100 * (level ** 1.8))
    
    def get_xp_to_next_level(self) -> int:
        """Retourne l'XP nécessaire pour le prochain niveau."""
        return self.get_xp_for_level(self.level + 1)
    
    def get_xp_progress(self) -> tuple:
        """Retourne (xp_actuel, xp_requis, pourcentage)."""
        required = self.get_xp_to_next_level()
        current = self.xp
        percentage = min(100, int((current / required) * 100)) if required > 0 else 0
        return current, required, percentage
    
    def add_xp(self, amount: int) -> List[int]:
        """
        Ajoute de l'XP et gère les level up.
        Retourne la liste des niveaux atteints.
        """
        self.xp += amount
        self.total_xp += amount
        
        levels_gained = []
        while self.xp >= self.get_xp_to_next_level():
            self.xp -= self.get_xp_to_next_level()
            self.level += 1
            self.skill_points += 1
            levels_gained.append(self.level)
            
            # Augmenter les stats de base à chaque niveau
            self.base_hp += 10
            self.base_attack += 2
            self.base_defense += 1
            self.base_speed += 1
        
        return levels_gained
    
    def get_max_hp(self) -> int:
        """Calcule les HP max avec bonus d'équipement."""
        bonus_hp = self._get_equipment_stat("hp")
        return self.base_hp + bonus_hp
    
    def get_attack(self) -> int:
        """Calcule l'attaque totale avec bonus d'équipement."""
        bonus_attack = self._get_equipment_stat("attack")
        return self.base_attack + bonus_attack
    
    def get_defense(self) -> int:
        """Calcule la défense totale avec bonus d'équipement."""
        bonus_defense = self._get_equipment_stat("defense")
        return self.base_defense + bonus_defense
    
    def get_speed(self) -> int:
        """Calcule la vitesse totale avec bonus d'équipement."""
        bonus_speed = self._get_equipment_stat("speed")
        return self.base_speed + bonus_speed
    
    def get_coin_bonus(self) -> float:
        """Calcule le bonus de pièces (pourcentage) depuis l'équipement."""
        return self._get_equipment_stat("coin_bonus")
    
    def get_xp_bonus(self) -> float:
        """Calcule le bonus d'XP (pourcentage) depuis l'équipement."""
        return self._get_equipment_stat("xp_bonus")
    
    def _get_equipment_stat(self, stat_name: str) -> float:
        """
        Récupère la somme d'une stat depuis tous les équipements.
        Note: Nécessite que le DataManager soit passé ou que les stats soient stockées.
        """
        # Cette méthode sera appelée avec le contexte du DataManager
        # Pour l'instant, on utilise les stats stockées localement
        if not hasattr(self, '_equipment_stats_cache'):
            return 0
        return self._equipment_stats_cache.get(stat_name, 0)
    
    def update_equipment_stats(self, data_manager) -> None:
        """Met à jour le cache des stats d'équipement."""
        self._equipment_stats_cache = {
            "hp": 0,
            "attack": 0,
            "defense": 0,
            "speed": 0,
            "coin_bonus": 0.0,
            "xp_bonus": 0.0,
            "drop_bonus": 0.0
        }
        
        for slot, item_id in self.equipment.items():
            if item_id:
                item = data_manager.get_item(item_id)
                if item:
                    # TOUJOURS générer des stats selon la rareté et le slot
                    # Les stats dans items.json sont ignorées pour le combat
                    default_stats = self._get_default_item_stats(item, slot)
                    for stat, value in default_stats.items():
                        if stat in self._equipment_stats_cache:
                            self._equipment_stats_cache[stat] += value
    
    def _get_default_item_stats(self, item, slot: str) -> dict:
        """Génère des stats par défaut selon la rareté et le slot."""
        # Multiplicateurs BEAUCOUP plus élevés pour que l'équipement compte vraiment
        rarity_multipliers = {
            "NORMAL": 2,
            "RARE": 5,
            "EPIC": 15,
            "LEGENDARY": 40,
            "MYTHIC": 100  # Mythique = écrase tout
        }
        
        multiplier = rarity_multipliers.get(item.rarity.name, 1)
        
        # Stats selon le type de slot - valeurs de base plus élevées
        slot_stats = {
            "HELMET": {"defense": 8 * multiplier, "hp": 25 * multiplier},
            "CHESTPLATE": {"defense": 15 * multiplier, "hp": 50 * multiplier},
            "LEGGINGS": {"defense": 10 * multiplier, "hp": 35 * multiplier},
            "BOOTS": {"defense": 6 * multiplier, "speed": 5 * multiplier, "hp": 15 * multiplier},
            "WEAPON": {"attack": 20 * multiplier, "speed": 3 * multiplier},  # Arme = gros dégâts
            "ACCESSORY": {"coin_bonus": 0.05 * multiplier, "xp_bonus": 0.05 * multiplier, "hp": 20 * multiplier}
        }
        
        return slot_stats.get(slot, {})
    
    def heal_full(self) -> None:
        """Restaure tous les HP."""
        self.current_hp = self.get_max_hp()
    
    def take_damage(self, damage: int) -> int:
        """Inflige des dégâts. Retourne les dégâts réels."""
        # Réduction par la défense
        actual_damage = max(1, damage - self.get_defense() // 2)
        self.current_hp = max(0, self.current_hp - actual_damage)
        return actual_damage
    
    def is_alive(self) -> bool:
        """Vérifie si le joueur est en vie."""
        return self.current_hp > 0
    
    def equip_skill(self, skill_id: str) -> bool:
        """Équipe une compétence. Max 4."""
        if skill_id in self.equipped_skills:
            return False
        if len(self.equipped_skills) >= 4:
            return False
        if skill_id not in self.skills:
            return False
        self.equipped_skills.append(skill_id)
        return True
    
    def unequip_skill(self, skill_id: str) -> bool:
        """Déséquipe une compétence."""
        if skill_id in self.equipped_skills:
            self.equipped_skills.remove(skill_id)
            return True
        return False
    
    def unlock_skill(self, skill_id: str) -> bool:
        """Débloque une compétence avec des skill points."""
        if self.skill_points <= 0:
            return False
        if skill_id in self.skills:
            # Améliorer la compétence
            self.skills[skill_id] += 1
        else:
            self.skills[skill_id] = 1
        self.skill_points -= 1
        return True

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
            "total_items_sold": self.total_items_sold,
            "pets": self.pets,
            "equipped_pet": self.equipped_pet,
            "eggs_opened": self.eggs_opened,
            "equipment": self.equipment,
            # Nouvelles données niveau/combat
            "level": self.level,
            "xp": self.xp,
            "total_xp": self.total_xp,
            "base_hp": self.base_hp,
            "base_attack": self.base_attack,
            "base_defense": self.base_defense,
            "base_speed": self.base_speed,
            "current_hp": self.current_hp,
            "skills": self.skills,
            "equipped_skills": self.equipped_skills,
            "bosses_defeated": self.bosses_defeated,
            "bosses_kills": self.bosses_kills,
            "last_boss_fight": self.last_boss_fight,
            "skill_points": self.skill_points
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Player":
        """Crée un Player à partir d'un dictionnaire."""
        default_equipment = {
            "HELMET": None,
            "CHESTPLATE": None,
            "LEGGINGS": None,
            "BOOTS": None,
            "WEAPON": None,
            "ACCESSORY": None
        }
        player = cls(
            user_id=data["user_id"],
            coins=data.get("coins", 0),
            inventory=data.get("inventory", {}),
            daily_chests_opened=data.get("daily_chests_opened", 0),
            last_chest_date=data.get("last_chest_date", ""),
            total_chests_opened=data.get("total_chests_opened", 0),
            total_items_sold=data.get("total_items_sold", 0),
            pets=data.get("pets", {}),
            equipped_pet=data.get("equipped_pet"),
            eggs_opened=data.get("eggs_opened", 0),
            equipment=data.get("equipment", default_equipment),
            # Nouvelles données niveau/combat
            level=data.get("level", 1),
            xp=data.get("xp", 0),
            total_xp=data.get("total_xp", 0),
            base_hp=data.get("base_hp", 100),
            base_attack=data.get("base_attack", 10),
            base_defense=data.get("base_defense", 5),
            base_speed=data.get("base_speed", 10),
            current_hp=data.get("current_hp", 100),
            skills=data.get("skills", {}),
            equipped_skills=data.get("equipped_skills", []),
            bosses_defeated=data.get("bosses_defeated", 0),
            bosses_kills=data.get("bosses_kills", {}),
            last_boss_fight=data.get("last_boss_fight", ""),
            skill_points=data.get("skill_points", 0)
        )
        return player
