document.addEventListener('DOMContentLoaded', function() {
    let itemsAndTypes = {};

    const itemDropdownTemplate = document.getElementById('itemDropdown');
    const foremanDropdownTemplate = document.getElementById('foremanDropdown');
    const addRowBtn = document.getElementById('addRowBtn');
    const inventoryBody = document.getElementById('inventoryBody');
    const submitBtn = document.getElementById('submitBtn');
    const suggestionsList = document.getElementById('suggestions');

    // Fetch items and types from server
    fetch('/get_items_and_types')
        .then(response => response.json())
        .then(data => {
            itemsAndTypes = data.items_and_types;
            // Populate item dropdown template
            populateDropdown(itemDropdownTemplate, Object.keys(itemsAndTypes));
        })
        .catch(error => {
            console.error('Error fetching items and types:', error);
        });

    // Fetch foremen from server
    fetch('/get_foremen')
        .then(response => response.json())
        .then(data => {
            populateDropdown(foremanDropdownTemplate, data.foremen);
        })
        .catch(error => {
            console.error('Error fetching foremen:', error);
        });

    function populateDropdown(dropdown, options) {
        options.forEach(optionValue => {
            const option = document.createElement('option');
            option.value = optionValue;
            option.textContent = optionValue;
            dropdown.appendChild(option);
        });
    }

    function updateTypeOptions(selectElement) {
        const selectedItem = selectElement.value;
        const row = selectElement.closest('tr');
        const typeDropdown = row.querySelector('.type-dropdown');
        const types = itemsAndTypes[selectedItem] || [];

        // Clear the type dropdown
        typeDropdown.innerHTML = '';

        // Populate type dropdown with new options
        types.forEach(type => {
            const option = document.createElement('option');
            option.value = type;
            option.textContent = type;
            typeDropdown.appendChild(option);
        });
    }

    addRowBtn.addEventListener('click', function() {
        const newRow = document.createElement('tr');
        newRow.innerHTML = `
            <td data-label="Date"><input type="date" value="${new Date().toISOString().split('T')[0]}" required></td>
            <td data-label="Name"><input type="text" placeholder="Enter name" oninput="searchWorker(this.value, this.nextElementSibling)" required><ul class="suggestions"></ul></td>
            <td data-label="Your Foreman">
                <select class="foreman-dropdown" required>
                    <option value="">Select foreman</option>
                    ${foremanDropdownTemplate.innerHTML}
                </select>
            </td>
            <td data-label="Item Name/Color">
                <select class="item-dropdown" required onchange="updateTypeOptions(this)">
                    <option value="">Select item</option>
                    ${itemDropdownTemplate.innerHTML}
                </select>
            </td>
            <td data-label="Type">
                <select class="type-dropdown">
                    <option value="">Select type</option>
                </select>
            </td>
            <td data-label="Quantity"><input type="number" placeholder="Quantity" required></td>
            <td data-label="Action"><button class="deleteRowBtn">Delete</button></td>
        `;
        inventoryBody.appendChild(newRow);

        // Add event listener for the delete button
        newRow.querySelector('.deleteRowBtn').addEventListener('click', function() {
            deleteRow(newRow);
        });

        // Add event listener for the search worker input
        newRow.querySelector('input[oninput="searchWorker(this.value, this.nextElementSibling)"]').addEventListener('input', function() {
            searchWorker(this.value, this.nextElementSibling);
        });
    });

    function deleteRow(row) {
        if (inventoryBody.rows.length > 1) {
            row.remove();
        } else {
            alert('At least one row must remain.');
        }
    }

    submitBtn.addEventListener('click', function() {
        const rows = inventoryBody.querySelectorAll('tr');
        const data = [];
        let valid = true;

        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            const rowData = {};
            rowData.date = cells[0].querySelector('input').value;
            rowData.name = cells[1].querySelector('input').value;
            rowData.foreman = cells[2].querySelector('select').value;
            rowData.item = cells[3].querySelector('select').value;
            rowData.type = cells[4].querySelector('select').value;
            rowData.quantity = cells[5].querySelector('input').value;

            if (!rowData.date || !rowData.name || !rowData.foreman || !rowData.item || (!rowData.type && itemsAndTypes[rowData.item].length > 0) || !rowData.quantity) {
                valid = false;
                alert('Please fill out all fields.');
                return false;
            }

            data.push(rowData);
        });

        if (!valid) return;

        fetch('/submit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ data: data })
        }).then(response => response.json())
          .then(result => {
              if (result.status === 'success') {
                  alert('Data submitted successfully!');
                  // Clear all rows except the first one
                  while (inventoryBody.rows.length > 1) {
                      inventoryBody.deleteRow(1);
                  }
                  // Reset the first row
                  const firstRow = inventoryBody.rows[0];
                  firstRow.querySelectorAll('input').forEach(input => input.value = '');
                  firstRow.querySelectorAll('select').forEach(select => select.selectedIndex = 0);
              } else {
                  alert('Error submitting data.');
              }
          })
          .catch(error => {
              console.error('Error submitting data:', error);
          });
    });

    window.updateTypeOptions = function(selectElement) {
        const selectedItem = selectElement.value;
        const row = selectElement.closest('tr');
        const typeDropdown = row.querySelector('.type-dropdown');
        const types = itemsAndTypes[selectedItem] || [];

        // Clear the type dropdown
        typeDropdown.innerHTML = '';

        // Populate type dropdown with new options
        types.forEach(type => {
            const option = document.createElement('option');
            option.value = type;
            option.textContent = type;
            typeDropdown.appendChild(option);
        });
    };

    // Add event listener to the initial delete button
    document.querySelectorAll('.deleteRowBtn').forEach(button => {
        button.addEventListener('click', function() {
            deleteRow(button.closest('tr'));
        });
    });

    // Function to search for workers
    window.searchWorker = function(query, suggestionsElement) {
        fetch(`/search?q=${query}&type=name`)
            .then(response => response.json())
            .then(data => {
                suggestionsElement.innerHTML = '';
                if (data.length > 0) {
                    data.forEach(item => {
                        const li = document.createElement('li');
                        li.textContent = item;
                        li.addEventListener('click', function() {
                            document.getElementById('nameInput').value = item;
                            suggestionsElement.innerHTML = '';
                        });
                        suggestionsElement.appendChild(li);
                    });
                }
            })
            .catch(error => {
                console.error('Error searching for workers:', error);
            });
    };

    // Modal functionality
    const passwordModal = document.getElementById('passwordModal');
    const passwordInput = document.getElementById('passwordInput');
    const confirmPasswordBtn = document.getElementById('confirmPasswordBtn');
    const span = document.getElementsByClassName('close')[0];

    let action = ''; // To keep track of whether we're loading or downloading

    document.getElementById('loadStockBtn').addEventListener('click', function() {
        action = 'load';
        passwordModal.style.display = 'block';
    });

    document.getElementById('downloadStockBtn').addEventListener('click', function() {
        action = 'download';
        passwordModal.style.display = 'block';
    });

    confirmPasswordBtn.addEventListener('click', function() {
        if (passwordInput.value === '0000') {
            passwordModal.style.display = 'none';
            passwordInput.value = '';
            if (action === 'load') {
                loadStockData();
            } else if (action === 'download') {
                downloadStockData();
            }
        } else {
            alert('Incorrect password');
        }
    });

    span.onclick = function() {
        passwordModal.style.display = 'none';
    };

    window.onclick = function(event) {
        if (event.target === passwordModal) {
            passwordModal.style.display = 'none';
        }
    };

    function loadStockData() {
        fetch('/load_stock')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    alert('Stock data loaded successfully!');
                } else {
                    alert('Error loading stock data.');
                }
            })
            .catch(error => {
                console.error('Error loading stock data:', error);
            });
    }

    function downloadStockData() {
        fetch('/download_stock', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                alert('Stock data downloaded successfully!');
            } else {
                alert('Error downloading stock data.');
            }
        })
        .catch(error => {
            console.error('Error downloading stock data:', error);
        });
    }
});
