#!/usr/bin/env python3
"""
Manuelle Verifizierung der ISBN-Checksummen
Berechnet die korrekte Prüfziffer für die Test-ISBNs
"""

def calculate_isbn13_check_digit(isbn12):
    """Berechnet die ISBN-13 Prüfziffer aus den ersten 12 Ziffern."""
    digits = [int(d) for d in isbn12]
    weights = [1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3]
    checksum = sum(d * w for d, w in zip(digits, weights))
    check_digit = (10 - (checksum % 10)) % 10
    return check_digit

def calculate_isbn10_check_digit(isbn9):
    """Berechnet die ISBN-10 Prüfziffer aus den ersten 9 Ziffern."""
    digits = [int(d) for d in isbn9]
    weights = [10, 9, 8, 7, 6, 5, 4, 3, 2]
    checksum = sum(d * w for d, w in zip(digits, weights))
    check_digit = (11 - (checksum % 11)) % 11
    if check_digit == 10:
        return 'X'
    return str(check_digit)

print("=" * 80)
print("ISBN PRÜFZIFFERN-BERECHNUNG")
print("=" * 80)
print()

# Teste die angegebenen ISBNs
print("Test 1: ISBN-13 '9783423282388' - 'Der Gesang der Flusskrebse'")
isbn12 = "978342328238"
calculated = calculate_isbn13_check_digit(isbn12)
print(f"  Erste 12 Ziffern: {isbn12}")
print(f"  Berechnete Prüfziffer: {calculated}")
print(f"  Angegebene Prüfziffer: 8")
print(f"  Korrekte ISBN-13: {isbn12}{calculated}")
print()

print("Test 2: ISBN-10 '3423282380'")
isbn9 = "342328238"
calculated = calculate_isbn10_check_digit(isbn9)
print(f"  Erste 9 Ziffern: {isbn9}")
print(f"  Berechnete Prüfziffer: {calculated}")
print(f"  Angegebene Prüfziffer: 0")
print(f"  Korrekte ISBN-10: {isbn9}{calculated}")
print()

# Generiere einige bekannte gültige Test-ISBNs
print("=" * 80)
print("BEKANNTE GÜLTIGE ISBNs ZUM TESTEN")
print("=" * 80)
print()

# Diese ISBNs sind definitiv gültig (aus Online-Quellen)
valid_isbns = [
    ("9780306406157", "ISBN-13 Beispiel aus Wikipedia"),
    ("0306406152", "ISBN-10 Beispiel aus Wikipedia"),
    ("9783161484100", "ISBN-13 zufälliges Beispiel"),
]

print("Gültige Test-ISBNs:")
for isbn, desc in valid_isbns:
    print(f"  {isbn} - {desc}")

print()
print("=" * 80)