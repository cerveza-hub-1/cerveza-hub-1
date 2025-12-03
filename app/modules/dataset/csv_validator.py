def validate_csv_content(file_content: str):
    import csv

    # 1. Limpiar BOM
    file_content = file_content.lstrip("\ufeff")

    try:
        # 2. Detectar dialecto (delimitador automático)
        sniffer = csv.Sniffer()
        lines = file_content.splitlines()
        sample = "\n".join(lines[:10])  # suficiente para detectar
        try:
            dialect = sniffer.sniff(sample, delimiters=[',',';','\t'])
        except csv.Error:
            dialect = csv.excel  # fallback si no detecta
        reader = csv.reader(lines, dialect)

        # 3. Ignorar filas vacías
        rows = [row for row in reader if any(cell.strip() for cell in row)]
        if len(rows) == 0:
            return False, {"message": "CSV file is empty"}

        # 4. Validar columnas
        expected_cols = len(rows[0])
        if expected_cols == 0:
            return False, {"message": "CSV header is invalid"}

        for i, row in enumerate(rows, start=1):
            if len(row) != expected_cols:
                return False, {
                    "message": "Invalid CSV format",
                    "error": f"Row {i} has {len(row)} columns but expected {expected_cols}.",
                    "row": row,
                }

    except Exception as e:
        return False, {"message": f"Invalid CSV format: {e}"}

    return True, None
