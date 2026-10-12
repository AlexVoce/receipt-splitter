const people = [];

const receiptStep = document.querySelector("#receipt-step");
const peopleStep = document.querySelector("#people-step");
const splitStep = document.querySelector("#split-step");
const resultsStep = document.querySelector("#results-step");


function showStep(step) {
    receiptStep.hidden = true;
    peopleStep.hidden = true;
    splitStep.hidden = true;
    resultsStep.hidden = true;

    step.hidden = false;
}


function readItems() {
    const itemElements = document.querySelectorAll(".item");

    return Array.from(itemElements).map((element) => {
        return {
            description: element.querySelector(".description").value,
            price: Number(element.querySelector(".price").value),
        };
    });
}


document
    .querySelector("#receipt-continue")
    .addEventListener("click", () => {
        showStep(peopleStep);
    });


document
    .querySelector("#add-person")
    .addEventListener("click", addPerson);


document
    .querySelector("#person-name")
    .addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            addPerson();
        }
    });


function addPerson() {
    const input = document.querySelector("#person-name");
    const name = input.value.trim();

    if (!name) {
        return;
    }

    if (people.includes(name)) {
        return;
    }

    people.push(name);
    input.value = "";

    renderPeople();
}


function renderPeople() {
    const container = document.querySelector("#people-list");

    container.innerHTML = "";

    for (const person of people) {
        const chip = document.createElement("span");

        chip.className = "person-chip";
        chip.textContent = person;

        container.appendChild(chip);
    }
}


document
    .querySelector("#people-continue")
    .addEventListener("click", () => {

        if (people.length === 0) {
            alert("you need at least one person obvs.");
            return;
        }

        buildSplitScreen();
        showStep(splitStep);
    });


function buildSplitScreen() {
    const items = readItems();
    const container = document.querySelector("#split-items");

    container.innerHTML = "";

    items.forEach((item, itemIndex) => {

        const row = document.createElement("div");
        row.className = "split-item";

        const heading = document.createElement("div");

        heading.innerHTML = `
            <strong>${item.description}</strong>
            <span>£${item.price.toFixed(2)}</span>
        `;

        row.appendChild(heading);

        const buttons = document.createElement("div");
        buttons.className = "assignment-buttons";

        for (const person of people) {

            const button = document.createElement("button");

            button.type = "button";
            button.textContent = person;
            button.dataset.person = person;
            button.dataset.item = itemIndex;

            // Everyone shares every item by default.
            button.classList.add("selected");

            button.addEventListener("click", () => {
                button.classList.toggle("selected");
            });

            buttons.appendChild(button);
        }

        row.appendChild(buttons);
        container.appendChild(row);
    });
}


document
    .querySelector("#calculate")
    .addEventListener("click", calculateTotals);


function calculateTotals() {
    const items = readItems();

    const results = {};

    // Give each person a total and an empty item breakdown.
    for (const person of people) {
        results[person] = {
            total: 0,
            items: [],
        };
    }

    items.forEach((item, itemIndex) => {
        const selected = document.querySelectorAll(
            `.assignment-buttons button[data-item="${itemIndex}"].selected`
        );

        if (selected.length === 0) {
            return;
        }

        const share = item.price / selected.length;

        for (const button of selected) {
            const person = button.dataset.person;

            results[person].total += share;

            results[person].items.push({
                description: item.description,
                share: share,
            });
        }
    });

    renderResults(results);
    showStep(resultsStep);
}

function renderResults(results) {
    const container = document.querySelector("#results");

    container.innerHTML = "";

    for (const [person, result] of Object.entries(results)) {
        const personResult = document.createElement("div");
        personResult.className = "person-result";

        const summary = document.createElement("div");
        summary.className = "result-row";

        summary.innerHTML = `
            <span>${person}</span>
            <strong>£${result.total.toFixed(2)}</strong>
        `;

        const details = document.createElement("details");
        details.className = "breakdown";

        const detailsSummary = document.createElement("summary");
        detailsSummary.textContent = "Question me if you dare";

        details.appendChild(detailsSummary);

        const itemList = document.createElement("div");
        itemList.className = "breakdown-items";

        for (const item of result.items) {
            const itemRow = document.createElement("div");
            itemRow.className = "breakdown-item";

            itemRow.innerHTML = `
                <span>${item.description}</span>
                <span>£${item.share.toFixed(2)}</span>
            `;

            itemList.appendChild(itemRow);
        }

        details.appendChild(itemList);

        personResult.appendChild(summary);
        personResult.appendChild(details);

        container.appendChild(personResult);
    }
}