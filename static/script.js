// Load selected values from localStorage, or use an empty array if nothing is stored
let selectedValues = JSON.parse(localStorage.getItem('selectedValues') || '[]');
// Store the currently selected document's ID
let currentDocId = null;

// Fetch the list of documents from the backend
async function fetchDocuments() {
    const res = await fetch('/api/documents');
    return await res.json();
}

// Fetch the rows (values) for a specific document by its ID
async function fetchRows(docId) {
    const res = await fetch(`/api/rows/${docId}`);
    return await res.json(); // returns array of row names
}

// Show the modal for the selected document
async function displayModal() {
    if (!currentDocId) return; // Exit if no document is selected
    const rows = await fetchRows(currentDocId); // Get the rows for the current document

    // If not all rows are already selected, select all by default and save to localStorage
    if (!rows.every(row => selectedValues.includes(row))) {
        selectedValues = rows.slice(); // Select all rows
        localStorage.setItem('selectedValues', JSON.stringify(selectedValues)); // Persist selection
    }

    const modalBody = document.getElementById('modalBody'); // Get the modal body element
    modalBody.innerHTML = ''; // Clear previous content

    // For each row, create a div with the row name, a checkbox, and a delete button
    rows.forEach(rowName => {
        const row = document.createElement('div');
        row.className = 'toggle-row';
        row.innerHTML = `
            <span>${rowName}</span>
            <input type="checkbox" ${selectedValues.includes(rowName) ? 'checked' : ''} data-name="${rowName}">
            <button class="delete-btn" data-name="${rowName}">Delete</button>
        `;
        // When the checkbox is toggled, update selectedValues and localStorage, then log
        row.querySelector('input').addEventListener('change', (e) => {
            if (e.target.checked) {
                if (!selectedValues.includes(rowName)) selectedValues.push(rowName); // Add if checked
            } else {
                selectedValues = selectedValues.filter(val => val !== rowName); // Remove if unchecked
            }
            localStorage.setItem('selectedValues', JSON.stringify(selectedValues)); // Persist selection
            // Log after change
            console.log(`Selected for Document ${currentDocId}:`, selectedValues);
        });
        // When the delete button is clicked, remove the row from selectedValues, update localStorage, re-render, and log
        row.querySelector('.delete-btn').addEventListener('click', () => {
            selectedValues = selectedValues.filter(val => val !== rowName); // Remove row
            localStorage.setItem('selectedValues', JSON.stringify(selectedValues)); // Persist selection
            displayModal(); // Re-render modal
            // Log after delete
            console.log(`Selected for Document ${currentDocId}:`, selectedValues);
        });
        modalBody.appendChild(row); // Add the row to the modal body
    });

    // Handle "Select All" button logic
    document.getElementById('selectAllBtn').onclick = () => {
        if (selectedValues.length === rows.length) {
            selectedValues = []; // Deselect all if all are selected
        } else {
            selectedValues = rows.slice(); // Select all
        }
        localStorage.setItem('selectedValues', JSON.stringify(selectedValues)); // Persist selection
        displayModal(); // Re-render modal
        // Log after select all
        console.log(`Selected for Document ${currentDocId}:`, selectedValues);
    };

    // Log the selected values when the modal opens
    console.log(`Selected for Document ${currentDocId}:`, selectedValues);

    // Show the modal
    document.getElementById('modal').style.display = 'block';
}

// When the page loads, fetch documents and populate the dropdown
document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm) {
        uploadForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const fileInput = document.getElementById('fileInput');
            if (!fileInput.files.length) return;
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();
            document.getElementById('uploadResult').innerText = result.message || result.error;
        });
    }
    fetchDocuments().then(items => {
        const dropdown = document.getElementById('docDropdown'); // Get the dropdown element
        dropdown.innerHTML = '<option value="">--Select--</option>'; // Add default option
        items.forEach(item => {
            const option = document.createElement('option'); // Create an option for each document
            option.value = item.id;
            option.textContent = item.name;
            dropdown.appendChild(option); // Add option to dropdown
        });
        // When the dropdown value changes, set currentDocId and show the modal
        dropdown.addEventListener('change', (e) => {
            currentDocId = e.target.value;
            displayModal();
        });
    });

    function processSelectedValues() {
    // This function can be called anywhere to use the current selected values
    console.log("Processing selected values for Document", currentDocId, ":", selectedValues);
    // You can add your custom logic here, for example:
    // send selectedValues to the backend, filter data, etc.
}
    // Close the modal when the close button is clicked
    document.getElementById('closeModal').onclick = () => {
        document.getElementById('modal').style.display = 'none';
    };
    // Close the modal when clicking outside the modal content
    window.onclick = (event) => {
        if (event.target == document.getElementById('modal')) {
            document.getElementById('modal').style.display = 'none';
        }
    };
});