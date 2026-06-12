from __future__ import annotations

import unittest

from app.services.arrondissement import postcode_for_point


class TestPostcodeForPoint(unittest.TestCase):
    def test_landmarks(self) -> None:
        cases = {
            (48.8611, 2.3358): "75001",  # Louvre pyramid
            (48.8530, 2.3499): "75004",  # Notre-Dame
            (48.8584, 2.2945): "75007",  # Eiffel Tower
            (48.8628, 2.2879): "75016",  # Trocadéro (derived is 75016, never 75116)
            (48.8867, 2.3431): "75018",  # Sacré-Cœur
            (48.8638, 2.3885): "75020",  # Père-Lachaise
        }
        for (lat, lng), expected in cases.items():
            self.assertEqual(postcode_for_point(lat, lng), expected, msg=f"({lat}, {lng})")

    def test_outside_paris_returns_none(self) -> None:
        cases = [
            (48.8924, 2.2361),  # La Défense
            (48.8138, 2.3858),  # Le Kremlin-Bicêtre, just across the périphérique
            (45.7640, 4.8357),  # Lyon
        ]
        for lat, lng in cases:
            self.assertIsNone(postcode_for_point(lat, lng), msg=f"({lat}, {lng})")
