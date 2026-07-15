"""
NEXUS Simulator — Identifier Factory
Generates realistic Indian identifiers:
  - Phone numbers (Indian format)
  - Vehicle registrations (KA-xx-xx-xxxx)
  - Aadhaar (12-digit fake)
  - DL numbers (KA-format fake)
  - Bank account stubs
  - UPI IDs
All identifiers are tracked to avoid duplicates within a simulation run.
"""
from __future__ import annotations
import random
import string
from typing import Set

from simulator.config.constants import KARNATAKA_RTO_CODES


class IdentifierFactory:
    """
    Generates unique fake identifiers for the simulation.
    All generated IDs are tracked in sets to prevent duplicates.
    """

    def __init__(self, rng: random.Random) -> None:
        self.rng = rng
        self._used_phones: Set[str] = set()
        self._used_vehicles: Set[str] = set()
        self._used_aadhaar: Set[str] = set()
        self._used_dl: Set[str] = set()
        self._used_accounts: Set[str] = set()

    def phone(self) -> str:
        """10-digit Indian mobile number starting with 6-9."""
        while True:
            prefix = self.rng.choice(["6", "7", "8", "9"])
            rest = "".join(str(self.rng.randint(0, 9)) for _ in range(9))
            number = prefix + rest
            if number not in self._used_phones:
                self._used_phones.add(number)
                return number

    def vehicle_registration(self, rto_code: str | None = None) -> str:
        """Karnataka vehicle registration in KA-xx-xx-xxxx format."""
        while True:
            rto = rto_code or self.rng.choice(KARNATAKA_RTO_CODES)
            series = self.rng.choice(list(string.ascii_uppercase))
            series2 = self.rng.choice(list(string.ascii_uppercase))
            number = f"{self.rng.randint(1000, 9999)}"
            reg = f"{rto} {series}{series2} {number}"
            if reg not in self._used_vehicles:
                self._used_vehicles.add(reg)
                return reg

    def aadhaar(self) -> str:
        """12-digit fake Aadhaar number. First digit 2-9 (not 0 or 1)."""
        while True:
            first = str(self.rng.randint(2, 9))
            rest = "".join(str(self.rng.randint(0, 9)) for _ in range(11))
            uid = first + rest
            if uid not in self._used_aadhaar:
                self._used_aadhaar.add(uid)
                return uid

    def dl_number(self, rto_code: str | None = None) -> str:
        """Karnataka DL number in KA-XX-YYYY-NNNNNNN format."""
        while True:
            rto = (rto_code or self.rng.choice(KARNATAKA_RTO_CODES)).replace("KA-", "")
            year = self.rng.randint(2005, 2024)
            seq = self.rng.randint(1000000, 9999999)
            dl = f"KA{rto.replace('-','')}{year}{seq}"
            if dl not in self._used_dl:
                self._used_dl.add(dl)
                return dl

    def bank_account(self) -> str:
        """11–16 digit fake bank account number."""
        while True:
            length = self.rng.randint(11, 16)
            account = "".join(str(self.rng.randint(0, 9)) for _ in range(length))
            if account not in self._used_accounts:
                self._used_accounts.add(account)
                return account

    def ifsc(self) -> str:
        """Sample IFSC code."""
        banks = ["SBIN", "CNRB", "UBIN", "HDFC", "ICIC", "KARB", "VIJB", "CORP", "BKID"]
        bank = self.rng.choice(banks)
        branch = "0" + "".join(str(self.rng.randint(0, 9)) for _ in range(5))
        return f"{bank}{branch}"

    def upi_id(self, name: str, phone: str) -> str:
        """Generate a UPI ID."""
        style = self.rng.randint(0, 2)
        if style == 0:
            return f"{phone}@upi"
        elif style == 1:
            cleaned = name.lower().replace(" ", "")[:8]
            return f"{cleaned}@{self.rng.choice(['okaxis', 'oksbi', 'okhdfcbank', 'ybl'])}"
        else:
            return f"{phone}@{self.rng.choice(['paytm', 'gpay', 'phonepe'])}"

    def case_number(self, district_code: str, year: int, sequence: int) -> str:
        """FIR case number in Karnataka format: KA/DIST/YEAR/NNNN"""
        return f"KA/{district_code}/{year}/{sequence:05d}"
