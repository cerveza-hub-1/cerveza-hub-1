import requests

BASE_URL = "http://localhost:5001/fakenodo"


def main():
    # 1. Crear deposition
    print("➡️ Creando deposition...")
    payload = {"metadata": {"title": "Mi dataset"}, "files": ["file1.csv"]}
    resp = requests.post(f"{BASE_URL}/depositions", json=payload)
    deposition = resp.json()
    dep_id = deposition["id"]
    print("Deposition creada:", deposition, "\n")

    # 2. Editar metadatos
    print("➡️ Editando metadatos...")
    update_payload = {"metadata": {"description": "Descripción actualizada"}}
    resp = requests.patch(f"{BASE_URL}/depositions/{dep_id}/metadata", json=update_payload)
    print("Deposition actualizada:", resp.json(), "\n")

    # 3. Publicar deposition (primera vez)
    print("➡️ Publicando deposition (versión inicial)...")
    resp = requests.post(f"{BASE_URL}/depositions/{dep_id}/publish")
    record = resp.json()
    print("Record publicado:", record, "\n")

    # 4. Publicar de nuevo (simular nueva versión con archivos)
    print("➡️ Publicando de nuevo (nueva versión)...")
    resp = requests.post(f"{BASE_URL}/depositions/{dep_id}/publish")
    record = resp.json()
    print("Record actualizado con nueva versión:", record, "\n")

    # 5. Consultar record
    print("➡️ Consultando record...")
    resp = requests.get(f"{BASE_URL}/records/{dep_id}")
    print("Record consultado:", resp.json(), "\n")

    # 6. Listar todas las versiones
    print("➡️ Listando todas las versiones...")
    resp = requests.get(f"{BASE_URL}/records/{dep_id}/versions")
    print("Versiones:", resp.json(), "\n")


if __name__ == "__main__":
    main()
