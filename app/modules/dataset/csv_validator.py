def validate_csv_content(file_content: str):
    import csv

    # 1. Limpiar BOM
    file_content = file_content.lstrip("\ufeff")

    try:
        sniffer = csv.Sniffer()
        lines = file_content.splitlines()
        sample = "\n".join(lines[:10])
        try:
            dialect = sniffer.sniff(sample, delimiters=[",", ";", "\t"])
        except csv.Error:
            dialect = csv.excel
        reader = csv.reader(lines, dialect)

        # 3. Ignorar filas vacías
        rows = [row for row in reader if any(cell.strip() for cell in row)]
        if len(rows) == 0:
            return False, {"message": "CSV file is empty"}

        # 4. Validar cabecera
        expected_header = ["id", "name", "brand", "style", "alcohol", "ibu", "origin"]
        header = [cell.strip().lower() for cell in rows[0]]
        if header != expected_header:
            return False, {
                "message": "Invalid CSV header",
                "expected": expected_header,
                "found": header,
            }

        # 5. Validar filas
        for i, row in enumerate(rows[1:], start=2):
            if len(row) != len(expected_header):
                return False, {
                    "message": "Invalid CSV format",
                    "error": f"Row {i} has {len(row)} columns but expected {len(expected_header)}.",
                    "row": row,
                }

            # Validar alcohol
            try:
                alcohol = float(row[4])
                if not (0 <= alcohol <= 100):
                    return False, {
                        "message": f"Invalid alcohol value in row {i}",
                        "value": row[4],
                    }
            except ValueError:
                return False, {
                    "message": f"Alcohol must be a decimal number in row {i}",
                    "value": row[4],
                }

            # Validar ibu
            try:
                ibu = int(row[5])
                if not (0 <= ibu <= 100):
                    return False, {
                        "message": f"Invalid IBU value in row {i}",
                        "value": row[5],
                    }
            except ValueError:
                return False, {
                    "message": f"IBU must be an integer in row {i}",
                    "value": row[5],
                }

    except Exception as e:
        return False, {"message": f"Invalid CSV format: {e}"}

    return True, None
