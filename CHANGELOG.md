## 3.1.0 (2025-12-11)

### Feat

- add new workflow for automatic release
- add unit tests for zenodo
- merge trunk on feature_fakenodo_tests
- **fakenodo**: add sidebar navigation link for Fakenodo section
- **fakenodo**: enhance record management and user interface; improve file upload handling and display
- **fakenodo**: enhance record handling and view functionality; add record URL retrieval
- **fakenodo**: update routes and error handling; add index template
- **csvvalidator**: now the csvvalidator check the header and columns values

### Fix

- close version on .cz.toml
- rename tests files of zenodo and fakenodo due to problems with the CI
- **conflicts**: Resolución conflictos con trunk
- **fakenodo**: add null checks for dataset and metadata before accessing DOI
- **lint**: Arreglar fallo de formato usando black para que no falle el CI de Lint
- **url**: corregir la URL para visualizar datasets en despliegue
- **trunk**: isort and black aplicated
- **csvsearch**: now csv is correctly searched

### Refactor

- change name of release and tag workflow
- reformat zenodo unit test file
- clean up code formatting and improve readability
- refact tests fakenodo with black

## v3.0.0 (2025-12-07)

### Feat

- **csv**: implementación inicial del dataset
- **fakenodo**: add basic javascript file

### Fix

- **csv**: se ha modificado la estructura del file1
- **gitignore**: ignore app.log.[0-9]
- **dataset**: delete logs
- **csvds**: reformat with black and isort again
- **newdatatype**: unused dependencies
- seeders fixed
- **newtypedataset**: isort aplicado
- **newtypedataset**: archivos invalidos

## v2.0.0 (2025-11-27)

### Feat

- wis 98
- corrected lint errorrs
- testing ranking datasets
- **dataset**: enhance dataset view with recommendations and comments section
- **dataset**: add comment and ranking endpoints, enhance dataset routes with detailed docstrings
- **nlp**: add step to download NLTK and spaCy models in CI workflows
- **nlp**: add post-installation script to download NLTK and spaCy resources
- **nlp**: implement RecommendationEngine and dataset similarity functionality
- **nlp**: implement text processing functions for HTML removal, contraction expansion, and lemmatization
- **zenodo**: integrate fakenodo for local testing
- link names in ranking done
- **design**: Añadir hook de validación de uso de Conventional commit
- **tools**: Implementación del hook para comprobar la redacción de mensajes de commit
- frontend for ranking datasets done
- backend for ranking datasets from feature_task_9
- ranking backend completed without testing
- add filters in the repositories file
- add new filters inputs in frontend
- add Selenium IDE generated test for viewing datasets in public profile
- add view datasets in public profile test
- ranking dataset backend
- **data, views**: Compaginar la clase Comment con la clase Dataset y modelado de vistas
- **models**: Crear objeto Comment
- update user profile link and conditional controls in summary
- add public profile route to display user data and datasets
- add 2FA verification and enablement templates for user authentication
- implement 2FA functionality with QR code generation and verification (backend)
- add 2FA fields and encryption methods to UserProfile model
- **ci**: Añadir todos los cambios relativos al modelo CI/CD

### Fix

- reformated test_selenium
- clean up whitespace and formatting in dataset routes
- clean up imports and ensure consistent formatting in services.py and requirements.txt
- **nlp**: correct indentation in lemmatizer function and ensure newline at end of file
- **zenodo**: correct typo in zenodo service
- services.py reformatted

### Refactor

- remove unused import from repositories.py
- reorder import statements in dataset services and test files
- reformat file app/modeules/dataset/service.py
- lint corrections in dataset services
- comment out drop_table command for notepad in migration script
- remove commented-out login logic in the login route
