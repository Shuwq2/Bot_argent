"""
Module définissant les boss et le système de combat.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class BossDifficulty(Enum):
    """Difficulté des boss."""
    EASY = ("Facile", "🟢", 1.0)
    MEDIUM = ("Moyen", "🟡", 1.5)
    HARD = ("Difficile", "🟠", 2.0)
    EXTREME = ("Extrême", "🔴", 3.0)
    MYTHIC = ("Mythique", "💀", 5.0)
    
    @property
    def display_name(self) -> str:
        return self.value[0]
    
    @property
    def emoji(self) -> str:
        return self.value[1]
    
    @property
    def multiplier(self) -> float:
        return self.value[2]


class SkillType(Enum):
    """Types de compétences."""
    ATTACK = ("Attaque", "⚔️", "#e74c3c")
    DEFENSE = ("Défense", "🛡️", "#3498db")
    HEAL = ("Soin", "💚", "#2ecc71")
    SPECIAL = ("Spécial", "✨", "#9b59b6")
    BUFF = ("Buff", "⬆️", "#f39c12")
    DEBUFF = ("Debuff", "⬇️", "#e67e22")
    
    @property
    def display_name(self) -> str:
        return self.value[0]
    
    @property
    def emoji(self) -> str:
        return self.value[1]
    
    @property
    def color(self) -> str:
        return self.value[2]


@dataclass
class Skill:
    """Représente une compétence de combat."""
    skill_id: str
    name: str
    description: str
    skill_type: SkillType
    emoji: str
    
    # Stats de base
    base_power: int = 20  # Puissance de base
    accuracy: int = 100  # Précision (%)
    cooldown: int = 0  # Tours de recharge
    mana_cost: int = 0  # Coût en mana (si implémenté)
    
    # Niveau requis pour débloquer
    level_required: int = 1
    
    # Effets spéciaux
    heal_percent: float = 0.0  # % de HP soignés
    defense_boost: float = 0.0  # Boost de défense temporaire
    attack_boost: float = 0.0  # Boost d'attaque temporaire
    dot_damage: int = 0  # Dégâts par tour
    dot_turns: int = 0  # Durée du DoT
    stun_chance: float = 0.0  # Chance d'étourdir (%)
    lifesteal: float = 0.0  # Vol de vie (%)
    
    def calculate_damage(self, attacker_attack: int, level_bonus: int = 0) -> int:
        """Calcule les dégâts de la compétence."""
        return int((self.base_power + attacker_attack) * (1 + level_bonus * 0.1))
    
    def to_dict(self) -> dict:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "skill_type": self.skill_type.name,
            "emoji": self.emoji,
            "base_power": self.base_power,
            "accuracy": self.accuracy,
            "cooldown": self.cooldown,
            "mana_cost": self.mana_cost,
            "level_required": self.level_required,
            "heal_percent": self.heal_percent,
            "defense_boost": self.defense_boost,
            "attack_boost": self.attack_boost,
            "dot_damage": self.dot_damage,
            "dot_turns": self.dot_turns,
            "stun_chance": self.stun_chance,
            "lifesteal": self.lifesteal
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Skill":
        return cls(
            skill_id=data["skill_id"],
            name=data["name"],
            description=data["description"],
            skill_type=SkillType[data.get("skill_type", "ATTACK")],
            emoji=data.get("emoji", "⚔️"),
            base_power=data.get("base_power", 20),
            accuracy=data.get("accuracy", 100),
            cooldown=data.get("cooldown", 0),
            mana_cost=data.get("mana_cost", 0),
            level_required=data.get("level_required", 1),
            heal_percent=data.get("heal_percent", 0.0),
            defense_boost=data.get("defense_boost", 0.0),
            attack_boost=data.get("attack_boost", 0.0),
            dot_damage=data.get("dot_damage", 0),
            dot_turns=data.get("dot_turns", 0),
            stun_chance=data.get("stun_chance", 0.0),
            lifesteal=data.get("lifesteal", 0.0)
        )


@dataclass
class BossAttack:
    """Représente une attaque de boss."""
    name: str
    emoji: str
    damage: int
    description: str
    chance: float = 1.0  # Probabilité d'utilisation
    special_effect: Optional[str] = None  # Effet spécial
    effect_value: float = 0.0


@dataclass
class Boss:
    """Représente un boss à combattre."""
    boss_id: str
    name: str
    description: str
    emoji: str
    image_url: str
    
    # Stats
    max_hp: int
    attack: int
    defense: int
    speed: int
    
    # Difficulté et niveau
    difficulty: BossDifficulty
    level_required: int
    
    # Attaques du boss
    attacks: List[BossAttack] = field(default_factory=list)
    
    # Récompenses
    xp_reward: int = 100
    coins_reward: int = 1000
    drop_items: Dict[str, float] = field(default_factory=dict)  # item_id -> drop_chance
    guaranteed_drops: List[str] = field(default_factory=list)  # items garantis
    
    # Combat actuel
    current_hp: int = 0
    
    def __post_init__(self):
        if self.current_hp == 0:
            self.current_hp = self.max_hp
    
    def reset_hp(self) -> None:
        """Réinitialise les HP du boss."""
        self.current_hp = self.max_hp
    
    def take_damage(self, damage: int) -> int:
        """Inflige des dégâts au boss. Retourne les dégâts réels."""
        actual_damage = max(1, damage - self.defense // 3)
        self.current_hp = max(0, self.current_hp - actual_damage)
        return actual_damage
    
    def is_alive(self) -> bool:
        """Vérifie si le boss est en vie."""
        return self.current_hp > 0
    
    def get_hp_bar(self, length: int = 20) -> str:
        """Génère une barre de vie visuelle."""
        ratio = self.current_hp / self.max_hp
        filled = int(ratio * length)
        empty = length - filled
        
        if ratio > 0.5:
            bar_char = "🟩"
        elif ratio > 0.25:
            bar_char = "🟨"
        else:
            bar_char = "🟥"
        
        return bar_char * filled + "⬛" * empty
    
    def choose_attack(self) -> BossAttack:
        """Choisit une attaque aléatoire selon les probabilités."""
        import random
        
        if not self.attacks:
            return BossAttack(
                name="Attaque de base",
                emoji="👊",
                damage=self.attack,
                description="Une attaque normale"
            )
        
        total = sum(a.chance for a in self.attacks)
        rand = random.uniform(0, total)
        
        cumulative = 0
        for attack in self.attacks:
            cumulative += attack.chance
            if rand <= cumulative:
                return attack
        
        return self.attacks[0]
    
    def to_dict(self) -> dict:
        return {
            "boss_id": self.boss_id,
            "name": self.name,
            "description": self.description,
            "emoji": self.emoji,
            "image_url": self.image_url,
            "max_hp": self.max_hp,
            "attack": self.attack,
            "defense": self.defense,
            "speed": self.speed,
            "difficulty": self.difficulty.name,
            "level_required": self.level_required,
            "attacks": [
                {
                    "name": a.name,
                    "emoji": a.emoji,
                    "damage": a.damage,
                    "description": a.description,
                    "chance": a.chance,
                    "special_effect": a.special_effect,
                    "effect_value": a.effect_value
                } for a in self.attacks
            ],
            "xp_reward": self.xp_reward,
            "coins_reward": self.coins_reward,
            "drop_items": self.drop_items,
            "guaranteed_drops": self.guaranteed_drops
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Boss":
        attacks = [
            BossAttack(
                name=a["name"],
                emoji=a.get("emoji", "⚔️"),
                damage=a["damage"],
                description=a.get("description", ""),
                chance=a.get("chance", 1.0),
                special_effect=a.get("special_effect"),
                effect_value=a.get("effect_value", 0.0)
            ) for a in data.get("attacks", [])
        ]
        
        return cls(
            boss_id=data["boss_id"],
            name=data["name"],
            description=data.get("description", ""),
            emoji=data.get("emoji", "👹"),
            image_url=data.get("image_url", ""),
            max_hp=data["max_hp"],
            attack=data["attack"],
            defense=data.get("defense", 10),
            speed=data.get("speed", 10),
            difficulty=BossDifficulty[data.get("difficulty", "EASY")],
            level_required=data.get("level_required", 1),
            attacks=attacks,
            xp_reward=data.get("xp_reward", 100),
            coins_reward=data.get("coins_reward", 1000),
            drop_items=data.get("drop_items", {}),
            guaranteed_drops=data.get("guaranteed_drops", [])
        )


@dataclass
class CombatState:
    """État d'un combat en cours."""
    player_id: int
    boss: Boss
    turn: int = 1
    player_hp: int = 0
    player_max_hp: int = 0
    player_attack: int = 0
    player_defense: int = 0
    
    # Effets actifs
    player_buffs: Dict[str, int] = field(default_factory=dict)  # buff -> tours restants
    boss_debuffs: Dict[str, int] = field(default_factory=dict)
    player_dots: List[tuple] = field(default_factory=list)  # (damage, tours)
    
    # Cooldowns
    skill_cooldowns: Dict[str, int] = field(default_factory=dict)
    
    # Logs du combat
    combat_log: List[str] = field(default_factory=list)
    
    def add_log(self, message: str) -> None:
        """Ajoute un message au log."""
        self.combat_log.append(f"**Tour {self.turn}**: {message}")
        if len(self.combat_log) > 10:
            self.combat_log.pop(0)
    
    def apply_dots(self) -> int:
        """Applique les dégâts par tour. Retourne les dégâts totaux."""
        total_damage = 0
        new_dots = []
        for damage, turns in self.player_dots:
            total_damage += damage
            if turns > 1:
                new_dots.append((damage, turns - 1))
        self.player_dots = new_dots
        return total_damage
    
    def tick_cooldowns(self) -> None:
        """Réduit les cooldowns de 1."""
        for skill_id in list(self.skill_cooldowns.keys()):
            self.skill_cooldowns[skill_id] -= 1
            if self.skill_cooldowns[skill_id] <= 0:
                del self.skill_cooldowns[skill_id]
    
    def tick_buffs(self) -> None:
        """Réduit la durée des buffs de 1."""
        for buff in list(self.player_buffs.keys()):
            self.player_buffs[buff] -= 1
            if self.player_buffs[buff] <= 0:
                del self.player_buffs[buff]
        
        for debuff in list(self.boss_debuffs.keys()):
            self.boss_debuffs[debuff] -= 1
            if self.boss_debuffs[debuff] <= 0:
                del self.boss_debuffs[debuff]
