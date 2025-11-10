document.addEventListener('DOMContentLoaded', () => {
    setupFilters();
    send_query();
});

function setupFilters() {
    const showBtn = document.getElementById("show-more-filters");
    const hideBtn = document.getElementById("hide-more-filters");
    const panel = document.getElementById("extra-filters");
    const clearExtra = document.getElementById("clear-extra-filters");

    if (showBtn) {
        showBtn.addEventListener("click", () => {
            panel.style.display = "block";
            showBtn.style.display = "none";
            hideBtn.style.display = "block";
        });
    }
    if (hideBtn) {
        hideBtn.addEventListener("click", () => {
            panel.style.display = "none";
            hideBtn.style.display = "none";
            showBtn.style.display = "block";
        });
    }

    // Cuando se limpia el panel, disparar búsqueda
    if (clearExtra) {
        clearExtra.addEventListener("click", () => {
            const inputs = panel.querySelectorAll("input, textarea, select");
            inputs.forEach(i => {
                if (i.type === "checkbox" || i.type === "radio") i.checked = false;
                else i.value = "";
            });
            document.getElementById('query').dispatchEvent(new Event('input', {bubbles: true}));
        });
    }
}

function send_query() {
    console.log("send query...")

    document.getElementById('results').innerHTML = '';
    document.getElementById("results_not_found").style.display = "none";

    const filters = document.querySelectorAll('#filters input, #filters select, #filters [type="radio"]');

    filters.forEach(filter => {
        filter.addEventListener('input', () => {
            const csrfTokenElem = document.getElementById('csrf_token');
            const csrfToken = csrfTokenElem ? csrfTokenElem.value : "";

            const searchCriteria = {
                csrf_token: csrfToken,
                query: document.querySelector('#query')?.value || "",
                publication_type: document.querySelector('#publication_type')?.value || "any",
                sorting: document.querySelector('[name="sorting"]:checked') ? document.querySelector('[name="sorting"]:checked').value : "newest",

                // nuevos campos
                description: document.querySelector('#filter_description')?.value || "",
                authors: document.querySelector('#filter_authors')?.value || "",
                affiliation: document.querySelector('#filter_affiliation')?.value || "",
                orcid: document.querySelector('#filter_orcid')?.value || "",
                csv_filename: document.querySelector('#filter_csv_filename')?.value || "",
                csv_title: document.querySelector('#filter_csv_title')?.value || "",
                publication_doi: document.querySelector('#filter_publication_doi')?.value || "",
                tags: document.querySelector('#filter_tags')?.value || ""
            };

            // envia a la ruta actual para evitar problemas con url_prefix
            const endpoint = window.location.pathname || '/explore';

            fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(searchCriteria),
            })
                .then(response => response.json())
                .then(data => {
                    renderResults(data);
                })
                .catch(err => {
                    console.error("Error fetching datasets:", err);
                });
        });
    });
}

function renderResults(data) {
    console.log(data);
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '';

    // results counter
    const resultCount = data.length;
    const resultText = resultCount === 1 ? 'dataset' : 'datasets';
    document.getElementById('results_number').textContent = `${resultCount} ${resultText} found`;

    const notFound = document.getElementById("results_not_found");
    if (resultCount === 0) {
        notFound.style.display = "block";
        return;
    } else {
        notFound.style.display = "none";
    }

    data.forEach(dataset => {
        let card = document.createElement('div');
        card.className = 'col-12';
        card.innerHTML = `
            <div class="card">
                <div class="card-body">
                    <div class="d-flex align-items-center justify-content-between">
                        <h3><a href="${dataset.url}">${dataset.title}</a></h3>
                        <div>
                            <span class="badge bg-primary" style="cursor: pointer;" onclick="set_publication_type_as_query('${dataset.publication_type}')">${dataset.publication_type}</span>
                        </div>
                    </div>
                    <p class="text-secondary">${formatDate(dataset.created_at)}</p>

                    <div class="row mb-2">
                        <div class="col-md-4 col-12">
                            <span class=" text-secondary">Description</span>
                        </div>
                        <div class="col-md-8 col-12">
                            <p class="card-text">${dataset.description || ''}</p>
                        </div>
                    </div>

                    <div class="row mb-2">
                        <div class="col-md-4 col-12">
                            <span class=" text-secondary">Authors</span>
                        </div>
                        <div class="col-md-8 col-12">
                            ${dataset.authors.map(author => `<p class="p-0 m-0">${author.name}${author.affiliation ? ` (${author.affiliation})` : ''}${author.orcid ? ` (${author.orcid})` : ''}</p>`).join('')}
                        </div>
                    </div>

                    <div class="row mb-2">
                        <div class="col-md-4 col-12">
                            <span class=" text-secondary">Tags</span>
                        </div>
                        <div class="col-md-8 col-12">
                            ${Array.isArray(dataset.tags) ? dataset.tags.map(tag => `<span class="badge bg-primary me-1" style="cursor: pointer;" onclick="set_tag_as_query('${tag}')">${tag}</span>`).join('') : ''}
                        </div>
                    </div>

                    <div class="row">
                        <div class="col-md-4 col-12"></div>
                        <div class="col-md-8 col-12">
                            <a href="${dataset.url}" class="btn btn-outline-primary btn-sm" style="border-radius: 5px;">View dataset</a>
                            <a href="/dataset/download/${dataset.id}" class="btn btn-outline-primary btn-sm" style="border-radius: 5px;">Download (${dataset.total_size_in_human_format})</a>
                        </div>
                    </div>
                </div>
            </div>
        `;
        resultsDiv.appendChild(card);
    });
}


function formatDate(dateString) {
    const options = {day: 'numeric', month: 'long', year: 'numeric', hour: 'numeric', minute: 'numeric'};
    const date = new Date(dateString);
    return date.toLocaleString('en-US', options);
}

function set_tag_as_query(tagName) {
    const queryInput = document.getElementById('query');
    queryInput.value = tagName.trim();
    queryInput.dispatchEvent(new Event('input', {bubbles: true}));
}

function set_publication_type_as_query(publicationType) {
    const publicationTypeSelect = document.getElementById('publication_type');
    for (let i = 0; i < publicationTypeSelect.options.length; i++) {
        if (publicationTypeSelect.options[i].text === publicationType.trim()) {
            // Set the value of the select to the value of the matching option
            publicationTypeSelect.value = publicationTypeSelect.options[i].value;
            break;
        }
    }
    publicationTypeSelect.dispatchEvent(new Event('input', {bubbles: true}));
}

document.getElementById('clear-filters').addEventListener('click', clearFilters);

function clearFilters() {
    // 🔹 Reset the main search query
    let queryInput = document.querySelector('#query');
    queryInput.value = "";

    // 🔹 Reset the publication type to default
    let publicationTypeSelect = document.querySelector('#publication_type');
    publicationTypeSelect.value = "any";

    // 🔹 Reset the sorting option
    let sortingOptions = document.querySelectorAll('[name="sorting"]');
    sortingOptions.forEach(option => {
        option.checked = option.value === "newest";
    });

    // 🔹 Reset extra filters
    const extraPanel = document.getElementById("extra-filters");
    const extraInputs = extraPanel.querySelectorAll("input, textarea, select");
    extraInputs.forEach(i => {
        if (i.type === "checkbox" || i.type === "radio") i.checked = false;
        else i.value = "";
    });

    // 🔹 Hide extra filters panel if visible
    extraPanel.style.display = "none";
    document.getElementById("hide-more-filters").style.display = "none";
    document.getElementById("show-more-filters").style.display = "block";

    // 🔹 Trigger search
    queryInput.dispatchEvent(new Event('input', { bubbles: true }));
}

document.addEventListener('DOMContentLoaded', () => {

    //let queryInput = document.querySelector('#query');
    //queryInput.dispatchEvent(new Event('input', {bubbles: true}));

    let urlParams = new URLSearchParams(window.location.search);
    let queryParam = urlParams.get('query');

    if (queryParam && queryParam.trim() !== '') {

        const queryInput = document.getElementById('query');
        queryInput.value = queryParam
        queryInput.dispatchEvent(new Event('input', {bubbles: true}));
        console.log("throw event");

    } else {
        const queryInput = document.getElementById('query');
        queryInput.dispatchEvent(new Event('input', {bubbles: true}));
    }
});