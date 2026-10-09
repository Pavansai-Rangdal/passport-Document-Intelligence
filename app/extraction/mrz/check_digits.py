"""MRZ check digit validation according to ICAO Doc 9303."""

from typing import Any


class MRZCheckDigitValidator:
    """Validates MRZ check digits according to ICAO specifications."""

    # Character mapping for check digit calculation
    CHAR_MAP = {
        **{str(i): i for i in range(10)},
        **{chr(65 + i): 10 + i for i in range(26)},  # A-Z -> 10-35
        "<": 0,
    }

    @staticmethod
    def calculate_check_digit(data: str) -> int:
        """Calculate check digit for given data string."""
        total = 0
        weights = [7, 3, 1]

        for i, char in enumerate(data.upper()):
            value = MRZCheckDigitValidator.CHAR_MAP.get(char, 0)
            weight = weights[i % 3]
            total += value * weight

        return total % 10

    @staticmethod
    def validate_check_digit(data: str, check_digit: str) -> bool:
        """Validate check digit against data."""
        calculated = MRZCheckDigitValidator.calculate_check_digit(data)
        expected = int(check_digit) if check_digit.isdigit() else 0
        return calculated == expected

    @staticmethod
    def validate_td3_line1(line: str) -> dict[str, Any]:
        """Validate TD3 line 1 check digit."""
        # TD3 format: P<USA<SURNAME<<GIVEN<NAMES<<<<<<<<<<<<<<<<<<<
        # Check digit is at position 44 (last character)
        if len(line) != 44:
            return {"valid": False, "reason": f"Line length must be 44, got {len(line)}"}

        data = line[:43]
        check_digit = line[43]

        valid = MRZCheckDigitValidator.validate_check_digit(data, check_digit)
        return {
            "valid": valid,
            "calculated": MRZCheckDigitValidator.calculate_check_digit(data),
            "provided": int(check_digit) if check_digit.isdigit() else 0,
        }

    @staticmethod
    def validate_td3_line2(line: str) -> dict[str, Any]:
        """Validate TD3 line 2 check digits."""
        # TD3 format: A12345678<USA8001018M2501019<<<<<<<<<<<<<<04
        # Check digits at positions 10, 20, 28, 43
        if len(line) != 44:
            return {"valid": False, "reason": f"Line length must be 44, got {len(line)}"}

        results = []

        # Check digit 1: positions 0-9
        data1 = line[:9]
        check1 = line[9]
        results.append(
            {
                "position": 10,
                "valid": MRZCheckDigitValidator.validate_check_digit(data1, check1),
                "calculated": MRZCheckDigitValidator.calculate_check_digit(data1),
                "provided": int(check1) if check1.isdigit() else 0,
            }
        )

        # Check digit 2: positions 0-19
        data2 = line[:19]
        check2 = line[19]
        results.append(
            {
                "position": 20,
                "valid": MRZCheckDigitValidator.validate_check_digit(data2, check2),
                "calculated": MRZCheckDigitValidator.calculate_check_digit(data2),
                "provided": int(check2) if check2.isdigit() else 0,
            }
        )

        # Check digit 3: positions 21-27 (birth date)
        data3 = line[21:28]
        check3 = line[28]
        results.append(
            {
                "position": 29,
                "valid": MRZCheckDigitValidator.validate_check_digit(data3, check3),
                "calculated": MRZCheckDigitValidator.calculate_check_digit(data3),
                "provided": int(check3) if check3.isdigit() else 0,
            }
        )

        # Check digit 4: positions 21-42 (composite)
        data4 = line[21:43]
        check4 = line[43]
        results.append(
            {
                "position": 44,
                "valid": MRZCheckDigitValidator.validate_check_digit(data4, check4),
                "calculated": MRZCheckDigitValidator.calculate_check_digit(data4),
                "provided": int(check4) if check4.isdigit() else 0,
            }
        )

        all_valid = all(r["valid"] for r in results)
        return {"valid": all_valid, "checks": results}

    @staticmethod
    def validate_td1(lines: list[str]) -> dict[str, Any]:
        """Validate TD1 (ID card) MRZ check digits."""
        if len(lines) != 3:
            return {"valid": False, "reason": f"TD1 requires 3 lines, got {len(lines)}"}

        results = []

        # Line 1: I<UTO<ERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<
        if len(lines[0]) == 30:
            data = lines[0][:29]
            check = lines[0][29]
            results.append(
                {
                    "line": 1,
                    "valid": MRZCheckDigitValidator.validate_check_digit(data, check),
                    "calculated": MRZCheckDigitValidator.calculate_check_digit(data),
                    "provided": int(check) if check.isdigit() else 0,
                }
            )

        # Line 2: A12345678<UTO8001018F2501019<<<<<<<<<<<<<
        if len(lines[1]) == 30:
            # Check digit at position 10
            data1 = lines[1][:9]
            check1 = lines[1][9]
            results.append(
                {
                    "line": 2,
                    "position": 10,
                    "valid": MRZCheckDigitValidator.validate_check_digit(data1, check1),
                    "calculated": MRZCheckDigitValidator.calculate_check_digit(data1),
                    "provided": int(check1) if check1.isdigit() else 0,
                }
            )

            # Check digit at position 20
            data2 = lines[1][:19]
            check2 = lines[1][19]
            results.append(
                {
                    "line": 2,
                    "position": 20,
                    "valid": MRZCheckDigitValidator.validate_check_digit(data2, check2),
                    "calculated": MRZCheckDigitValidator.calculate_check_digit(data2),
                    "provided": int(check2) if check2.isdigit() else 0,
                }
            )

        # Line 3: 1234567890<UTO8001018M2501019<<<<<<<<<<<<<<00
        if len(lines[2]) == 30:
            # Check digit at position 8
            data1 = lines[2][:7]
            check1 = lines[2][7]
            results.append(
                {
                    "line": 3,
                    "position": 8,
                    "valid": MRZCheckDigitValidator.validate_check_digit(data1, check1),
                    "calculated": MRZCheckDigitValidator.calculate_check_digit(data1),
                    "provided": int(check1) if check1.isdigit() else 0,
                }
            )

            # Check digit at position 18
            data2 = lines[2][:17]
            check2 = lines[2][17]
            results.append(
                {
                    "line": 3,
                    "position": 18,
                    "valid": MRZCheckDigitValidator.validate_check_digit(data2, check2),
                    "calculated": MRZCheckDigitValidator.calculate_check_digit(data2),
                    "provided": int(check2) if check2.isdigit() else 0,
                }
            )

            # Check digit at position 28
            data3 = lines[2][:27]
            check3 = lines[2][27]
            results.append(
                {
                    "line": 3,
                    "position": 28,
                    "valid": MRZCheckDigitValidator.validate_check_digit(data3, check3),
                    "calculated": MRZCheckDigitValidator.calculate_check_digit(data3),
                    "provided": int(check3) if check3.isdigit() else 0,
                }
            )

        all_valid = all(r["valid"] for r in results)
        return {"valid": all_valid, "checks": results}
