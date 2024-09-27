import math
import os
from enum import Enum
from fractions import Fraction
from typing import Tuple, List, Optional

import yedextended as yed


class Phase(Enum):
    CHECK = "check"
    NIGHT = "night"
    VOTE = "vote"


class GameState:
    def __init__(self, unrevealed_town_count: int, revealed_town_count: int, unrevealed_mafia_count: int,
                 revealed_mafia_count: int, has_sheriff: bool, sheriff_revealed: bool, phase: Phase):
        self.unrevealed_town_count = unrevealed_town_count
        self.revealed_town_count = revealed_town_count
        self.unrevealed_mafia_count = unrevealed_mafia_count
        self.revealed_mafia_count = revealed_mafia_count
        self.has_sheriff = has_sheriff
        self.sheriff_revealed = sheriff_revealed
        self.phase = phase

    def is_game_over(self) -> Tuple[bool, Optional[bool]]:
        # Победа мафии
        if self.unrevealed_town_count + self.revealed_town_count + self.has_sheriff == self.unrevealed_mafia_count + self.revealed_mafia_count:
            return True, False
        # Победа мирных
        if self.unrevealed_mafia_count + self.revealed_mafia_count == 0:
            return True, True
        return False, None

    def get_next_states(self) -> List[Tuple['GameState', Fraction, str]]:
        next_states: List[tuple[GameState, Fraction, str]] = []
        total_count = (self.unrevealed_town_count + self.revealed_town_count + self.unrevealed_mafia_count +
                       self.revealed_mafia_count + (1 if self.has_sheriff else 0))
        if total_count <= 7 and self.has_sheriff:
            self.sheriff_revealed = True
        total_unrevealed_count = self.unrevealed_town_count + self.unrevealed_mafia_count
        if self.phase == Phase.CHECK:
            if self.has_sheriff:  # Шериф проверяет случайного игрока
                if self.unrevealed_town_count > 0:
                    new_state = GameState(self.unrevealed_town_count - 1, self.revealed_town_count + 1,
                                          self.unrevealed_mafia_count, self.revealed_mafia_count, self.has_sheriff,
                                          self.sheriff_revealed, Phase.NIGHT)
                    next_states.append(
                        (new_state,
                         Fraction(self.unrevealed_town_count, total_unrevealed_count),
                         "Шериф проверяет мирного"))
                if self.unrevealed_mafia_count > 0:
                    new_state = GameState(self.unrevealed_town_count, self.revealed_town_count,
                                          self.unrevealed_mafia_count - 1, self.revealed_mafia_count + 1,
                                          self.has_sheriff, self.sheriff_revealed, Phase.NIGHT)
                    next_states.append(
                        (new_state,
                         Fraction(self.unrevealed_mafia_count, total_unrevealed_count),
                         "Шериф проверяет мафию"))
            else:  # Пропускаем фазу проверки
                new_state = GameState(self.unrevealed_town_count, self.revealed_town_count, self.unrevealed_mafia_count,
                                      self.revealed_mafia_count, self.has_sheriff, self.sheriff_revealed, Phase.NIGHT)
                next_states.append((new_state, Fraction(1), "Фаза проверки пропущена"))

        elif self.phase == Phase.NIGHT:
            if self.sheriff_revealed:  # Мафия стреляет в шерифа, если он вскрыт
                if self.has_sheriff:
                    new_state = GameState(self.unrevealed_town_count, self.revealed_town_count,
                                          self.unrevealed_mafia_count, self.revealed_mafia_count, False,
                                          self.sheriff_revealed, Phase.VOTE)
                    next_states.append((new_state, Fraction(1), "Мафия стреляет в шерифа"))
                else:  # Далее мафия стреляет в проверенных мирных
                    if self.revealed_town_count > 0:
                        new_state = GameState(self.unrevealed_town_count, self.revealed_town_count - 1,
                                              self.unrevealed_mafia_count, self.revealed_mafia_count,
                                              self.has_sheriff, self.sheriff_revealed, Phase.VOTE)
                        next_states.append((new_state, Fraction(1), "Мафия стреляет в проверенного мирного"))
                    else:
                        new_state = GameState(self.unrevealed_town_count - 1, self.revealed_town_count,
                                              self.unrevealed_mafia_count, self.revealed_mafia_count,
                                              self.has_sheriff, self.sheriff_revealed, Phase.VOTE)
                        next_states.append((new_state, Fraction(1), "Мафия стреляет в мирного"))
            else:  # Мафия стреляет в случайную немафию
                total_town_count = self.unrevealed_town_count + 1 + self.revealed_town_count
                if self.has_sheriff:
                    new_state = GameState(self.unrevealed_town_count, self.revealed_town_count,
                                          self.unrevealed_mafia_count, self.revealed_mafia_count, False,
                                          True, Phase.VOTE)
                    next_states.append(
                        (new_state, Fraction(1, total_town_count),
                         "Мафия стреляет в шерифа"))
                if self.unrevealed_town_count > 0:
                    new_state = GameState(self.unrevealed_town_count - 1, self.revealed_town_count,
                                          self.unrevealed_mafia_count, self.revealed_mafia_count, self.has_sheriff,
                                          self.sheriff_revealed, Phase.VOTE)
                    next_states.append((
                        new_state, Fraction(self.unrevealed_town_count, total_town_count),
                        "Мафия стреляет в мирного"))
                if self.revealed_town_count > 0:
                    new_state = GameState(self.unrevealed_town_count, self.revealed_town_count - 1,
                                          self.unrevealed_mafia_count, self.revealed_mafia_count,
                                          self.has_sheriff, self.sheriff_revealed, Phase.VOTE)
                    next_states.append((new_state, Fraction(self.revealed_town_count, total_town_count),
                                        "Мафия стреляет в проверенного мирного"))

        elif self.phase == Phase.VOTE:
            if self.sheriff_revealed:
                if self.revealed_mafia_count > 0:
                    new_state = GameState(self.unrevealed_town_count, self.revealed_town_count,
                                          self.unrevealed_mafia_count, self.revealed_mafia_count - 1,
                                          self.has_sheriff, self.sheriff_revealed, Phase.CHECK)
                    next_states.append(
                        (new_state, Fraction(1), "Голосование: проверенная мафия"))
                else:
                    new_state = GameState(self.unrevealed_town_count, self.revealed_town_count,
                                          self.unrevealed_mafia_count - 1, self.revealed_mafia_count,
                                          self.has_sheriff, self.sheriff_revealed, Phase.CHECK)
                    next_states.append(
                        (new_state, Fraction(self.unrevealed_mafia_count,
                                             total_unrevealed_count),
                         "Голосование: мафия"))

                    new_state = GameState(self.unrevealed_town_count - 1, self.revealed_town_count,
                                          self.unrevealed_mafia_count, self.revealed_mafia_count,
                                          self.has_sheriff, self.sheriff_revealed, Phase.CHECK)
                    next_states.append(
                        (
                            new_state, Fraction(self.unrevealed_town_count, total_unrevealed_count),
                            "Голосование: мирный"))
            else:
                new_state = GameState(self.unrevealed_town_count, self.revealed_town_count,
                                      self.unrevealed_mafia_count - 1, self.revealed_mafia_count,
                                      self.has_sheriff, self.sheriff_revealed, Phase.CHECK)
                next_states.append(
                    (new_state, Fraction(self.unrevealed_mafia_count,
                                         total_count),
                     "Голосование: мафия"))

                new_state = GameState(self.unrevealed_town_count, self.revealed_town_count,
                                      self.unrevealed_mafia_count, self.revealed_mafia_count - 1,
                                      self.has_sheriff, self.sheriff_revealed, Phase.CHECK)
                next_states.append(
                    (new_state, Fraction(self.revealed_mafia_count,
                                         total_count),
                     "Голосование: проверенная мафия"))

                new_state = GameState(self.unrevealed_town_count - 1, self.revealed_town_count,
                                      self.unrevealed_mafia_count, self.revealed_mafia_count,
                                      self.has_sheriff, self.sheriff_revealed, Phase.CHECK)
                next_states.append(
                    (
                        new_state, Fraction(self.unrevealed_town_count, total_count),
                        "Голосование: мирный"))

                new_state = GameState(self.unrevealed_town_count, self.revealed_town_count,
                                      self.unrevealed_mafia_count, self.revealed_mafia_count,
                                      self.has_sheriff, True, Phase.VOTE)
                next_states.append(
                    (
                        new_state, Fraction(1 + self.revealed_town_count, total_count),
                        "Голосование: шериф или проверенный мирный"))

        return next_states

    def __repr__(self):
        return (f'GameState({self.unrevealed_town_count}, '
                f'{self.revealed_town_count}, '
                f'{self.unrevealed_mafia_count}, '
                f'{self.revealed_mafia_count}, '
                f'{self.has_sheriff}, '
                f'{self.sheriff_revealed}, '
                f'{self.phase})')


def get_win_probability(state: GameState) -> Fraction:
    game_over, is_town_win = state.is_game_over()
    if game_over:
        return Fraction(1) if is_town_win else Fraction(0)
    # state_tuple = (
    #     state.unrevealed_town_count, state.revealed_town_count, state.unrevealed_mafia_count,
    #     state.revealed_mafia_count,
    #     state.has_sheriff, state.sheriff_revealed, state.phase)
    # if state_tuple in cache:
    #     return cache[state_tuple]

    next_states = state.get_next_states()
    probs = [prob * get_win_probability(next_state) for next_state, prob, _ in
             filter(lambda it: it[1] != 0, next_states)]
    win_prob = Fraction(0)
    for prob in probs:
        win_prob += prob
    return win_prob


# Инициализация начального состояния
initial_state = GameState(6, 0, 3, 0, True, False, Phase.CHECK)

# Расчет вероятности победы мирных
win_probability = get_win_probability(initial_state)
print(f"Probability of town winning: {win_probability}")

def sigmoid(x):
  return 1 / (1 + math.exp(-x))

def create_node(state: GameState, graph: yed.Graph) -> yed.Node:
    game_over, is_town_win = state.is_game_over()
    if game_over:
        node = graph.add_node(str(Fraction(1) if is_town_win else Fraction(0)))
        node.shape_fill = '#ff0000' if is_town_win else '#000000'
        return node

    next_states = state.get_next_states()
    if sum(map(lambda it: it[1], next_states)) != 1:
        print(state, sum(map(lambda it: it[1], next_states)) )
    probs = [prob * get_win_probability(next_state) for next_state, prob, _ in
             filter(lambda it: it[1] != 0, next_states)]
    win_prob = sum(probs)
    children = []
    for next_state, prob, msg in filter(lambda it: it[1] != 0, next_states):
        children.append((create_node(next_state, graph), prob, msg))
    node = graph.add_node(str(win_prob))
    node.shape_fill = "#" + hex(min(255, int(255 * 1.5 * sigmoid(win_prob))))[2:] + "0000"
    for child, prob, msg in children:
        edge = graph.add_edge(node, child)
        edge.add_label(f'{msg} ({prob})')
    return node


def node_counter() -> str:
    global counter
    s = str(counter)
    counter += 1
    return s


counter = 0
graph = yed.Graph()
create_node(initial_state, graph)
os.remove("temp.graphml")
graph.persist_graph("temp.graphml", pretty_print=True)
