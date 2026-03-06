"""
Fonctions statistiques from scratch.
Reference : Joel Grus, "Data Science From Scratch", chapitre 5.

IMPORTANT : N'importez pas numpy, pandas ou statistics pour ces fonctions.
Implementez-les avec du Python pur (listes, boucles, math).
"""

import math


def mean(xs: list[float]) -> float:
    """Retourne la moyenne d'une liste de nombres."""
    return sum(xs) / len(xs)


def _median_odd(xs: list[float]) -> float:
    """len(xs) est impair, la médiane est l'élément du milieu de la liste triée."""
    return sorted(xs)[len(xs) // 2]

def _median_even(xs: list[float]) -> float:
    """len(xs) est pair, la médiane est la moyenne des deux éléments du milieu de la liste triée."""
    sorted_xs = sorted(xs)
    mid = len(xs) // 2
    return (sorted_xs[mid - 1] + sorted_xs[mid]) / 2

def median(xs: list[float]) -> float:
    """Retourne la mediane d'une liste de nombres."""
    return _median_even(xs) if len(xs) % 2 == 0 else _median_odd(xs)


def variance(xs: list[float]) -> float:
    """Retourne la variance d'une liste de nombres."""
    # VOTRE CODE ICI
    raise NotImplementedError("Implementez variance() - voir Grus ch.5")


def standard_deviation(xs: list[float]) -> float:
    """Retourne l'ecart-type d'une liste de nombres."""
    # VOTRE CODE ICI
    raise NotImplementedError("Implementez standard_deviation() - voir Grus ch.5")


def covariance(xs: list[float], ys: list[float]) -> float:
    """Retourne la covariance entre deux series."""
    # VOTRE CODE ICI
    raise NotImplementedError("Implementez covariance() - voir Grus ch.5")


def correlation(xs: list[float], ys: list[float]) -> float:
    """
    Retourne le coefficient de correlation de Pearson entre deux series.
    Retourne 0 si l'une des series a un ecart-type nul.
    """
    # VOTRE CODE ICI
    raise NotImplementedError("Implementez correlation() - voir Grus ch.5")
