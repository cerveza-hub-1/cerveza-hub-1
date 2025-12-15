## 3.3.0 (2025-12-15)

### Feat

- **tests**: implementación tests de locusts de la WIS 101
- **tests**: Implementación tests de locusts de la WIS 101
- **tests**: add recommendations box test to verify dataset recommendations
- **tests**: add test for recommendations box in dataset listing
- **tests**: enhance locust tests with login functionality and DOI dataset view
- **requirements**: add Pillow and pyzbar to dependencies
- **tests**: enhance unit tests with mock datasets and additional fixtures fix(nlp): refactor NLP model loading to use caching fix(services): improve corpus data extraction logic and clean up variable names chore(requirements): specify versions for dependencies and remove duplicates
- **tests**: enhance unit tests for dataset validation and recommendation engine
- **flamappy**: se eliminaron y modificaron todos los archivos relacionados con flamapy

### Fix

- descarga de paquete en dockerfile.dev
- cambios en docker compose
- **dataset**: mas cambios en algunos tests
- **dataset**: cambios en algunos tests
- **dataset**: cambios en algunos tests
- **dataset**: se aplico el isort  y el black
- **dataset**: cambios en algunos tests
- **dataset**: remove unnecessary blank line in DataSetService
- **dataset**: add engine retraining in  DOI update
- **requirements**: remove unintended dependency deletions
- **services**:  Some functions were fixed
- **services**: improve metadata handling by providing default values for missing fields
- **services**: handle None values in metadata fields for robust text processing
- **conftest**: Fix coverage execution
- **dataset**: cuando subes con user1 ya no da fallo
- arreglado docker compose

### Refactor

- **tests**: remove unused imports and redundant wait function in test_selenium.py
- **services**: reorder import statement for nlp_utils and simplify combined_text construction refactor(tests): update test assertions to check for 'full_text_corpus' instead of 'text'
- **tests**: enhance test fixtures and improve dataset validation tests
- **services**: update CorpusRecord type hint and improve corpus data extraction logic
- **tests**: enhance mock classes and fixtures in test_unit.py
- **tests**: remove unused imports in test_unit.py
- clean up imports and improve formatting in multiple files

## 3.2.0 (2025-12-12)

### Feat

- **test**: Implementación tests de selenium WIS 101
- **test**: Implementación tests de selenium de WIS 101
- **newtypedataset**: se agregaron los test de carga
- **newtypedataset**: se agrego el intento de un csv incorrecto en selenium test
- **newtypedataset**: aplicado isort y black
- **newtypedataset**: se agregaron test unitarios de las funciones nuevas o modificadas
- merge branch 'feature_2FA_unit_tests' into trunk
- add profile testing behaviors including view, edit, and 2FA functionality
- merge branch 'feature_vagrant' into trunk
- add Ansible Syntax Check workflow and integrate into existing workflows
- **advancedsearch**: test de carga realizados
- **advancedsearch**: test de interfaz agregados
- **advancedsearch**: test de integracion añadidos
- **advancedsearch**: test unitario de explore agregados
- revert configurado dockerfile.dev
- configurado dockerfile.dev
- revert configurado docker-compose
- configurado docker-compose
- añadidos test de ranking dataset
- lint y sintaxis de commit corregido.
- **test**: implementación de tests unitarios de la WIS-101

### Fix

- **style**: Correción de estilo por fallo de workflow de lint
- lint fixed
- **csvmodel**: se recupero el routes
- **dataset**: se arreglo el test de selenium de datasets
- correct paths for Ansible playbook syntax check and linting
- **trunk**: subiendo todos los cambios nuevamente
- **advancedsearch**: formateando con black e isort
- **advancedsearch**: quitando unused variables de locustfile
- **advancedsearch**: quitando mas unused variables
- **advancedsearch**: quitando unused variables
- **explore**: se elimino un test de explore que estaba en dataset
- **explore**: reformateado para arreglar los erorres de lint8
- **explore**: se eliminaron todas las unused variables
- **explore**: arreglando unused variables
- **style**: corrección formato en app/modules/comment/tests/test_unit.py usando isort para cumplir estándares de lint
- **style**: corrección formato en app/modules/comment/tests/test_unit.py para cumplir estándares de lint
- chnage to do the commit change version with my user

### Refactor

- streamline GET requests in profile test behaviors for improved readability
- clean up whitespace and formatting in profile test behaviors
- improve code readability by formatting data dictionaries and enhancing error messages
- comment out 2FA verification test due to CI/CD failures
- comment out 2FA verification test due to CI/CD failures
- replace session expiration with refresh for profile in 2FA verification test
- replaces for improved session management in 2FA verification test
- streamline assertions and response handling in authentication and profile tests
- improve readability of test cases by formatting and organizing code
- simplify exception handling and assertions in Selenium and unit tests
- final AuthSeeder tests and Auth tests lint passed
- improve flash message handling and update messages for 2FA features detected at Auth tests
- simplify export options in dataset view by replacing dropdown with direct export button with format updated
- streamline Ansible installation steps in CI workflow
- enhance playbook structure and improve readability following lint checker

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
