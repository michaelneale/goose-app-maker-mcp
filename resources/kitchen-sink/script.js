// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the app
    initGooseApi();
    initCounter();
    initColorChanger();
    initTodoList();
    displayCurrentDate();
    
    // Log that the app is ready
    console.log('Goose App Maker Demo is ready!');
});

// Goose API functionality
function initGooseApi() {
    // Text response elements
    const textMessageInput = document.getElementById('text-message');
    const textSendButton = document.getElementById('text-send-btn');
    const textClearButton = document.getElementById('text-clear-btn');
    const textResponseContainer = document.getElementById('text-response');
    
    // List response elements
    const listMessageInput = document.getElementById('list-message');
    const listSendButton = document.getElementById('list-send-btn');
    const listClearButton = document.getElementById('list-clear-btn');
    const listResponseContainer = document.getElementById('list-response');
    
    // Table response elements
    const tableMessageInput = document.getElementById('table-message');
    const tableSendButton = document.getElementById('table-send-btn');
    const tableClearButton = document.getElementById('table-clear-btn');
    const tableResponseContainer = document.getElementById('table-response');
    
    // Add event listeners for text response
    textSendButton.addEventListener('click', () => sendTextMessage(textMessageInput, textResponseContainer));
    textClearButton.addEventListener('click', () => clearResponse(textResponseContainer));
    
    // Add event listeners for list response
    listSendButton.addEventListener('click', () => sendListMessage(listMessageInput, listResponseContainer));
    listClearButton.addEventListener('click', () => clearResponse(listResponseContainer));
    
    // Add event listeners for table response
    tableSendButton.addEventListener('click', () => sendTableMessage(tableMessageInput, tableResponseContainer));
    tableClearButton.addEventListener('click', () => clearResponse(tableResponseContainer));
    
    // Text response handler
    async function sendTextMessage(input, container) {
        const message = input.value.trim();
        
        if (!message) {
            showError(container, 'Please enter a message');
            return;
        }
        
        // Show loading
        container.innerHTML = '<div class="loading-message">Sending request...</div>';
        
        try {
            const response = await gooseRequestText(message);
            displayTextResponse(container, response);
        } catch (error) {
            console.error('Error:', error);
            showError(container, `Error: ${error.message}`);
        }
    }
    
    // List response handler
    async function sendListMessage(input, container) {
        const message = input.value.trim();
        
        if (!message) {
            showError(container, 'Please enter a message');
            return;
        }
        
        // Show loading
        container.innerHTML = '<div class="loading-message">Sending request...</div>';
        
        try {
            const response = await gooseRequestList(message);
            displayListResponse(container, response);
        } catch (error) {
            console.error('Error:', error);
            showError(container, `Error: ${error.message}`);
        }
    }
    
    // Table response handler
    async function sendTableMessage(input, container) {
        const message = input.value.trim();
        
        if (!message) {
            showError(container, 'Please enter a message');
            return;
        }
        
        // Show loading
        container.innerHTML = '<div class="loading-message">Sending request...</div>';
        
        try {
            // Define columns based on the type of query
            const columns = ["Feature", "Description", "Notes"];
            const response = await gooseRequestTable(message, columns);
            displayTableResponse(container, response);
        } catch (error) {
            console.error('Error:', error);
            showError(container, `Error: ${error.message}`);
        }
    }
    
    // Display functions
    function displayTextResponse(container, text) {
        container.innerHTML = `<div class="text-response">${text}</div>`;
    }
    
    function displayListResponse(container, items) {
        if (!Array.isArray(items) || items.length === 0) {
            container.innerHTML = '<div class="empty-response">No items returned</div>';
            return;
        }
        
        const list = document.createElement('ul');
        list.className = 'response-list';
        
        items.forEach(item => {
            const li = document.createElement('li');
            li.textContent = item;
            list.appendChild(li);
        });
        
        container.innerHTML = '';
        container.appendChild(list);
    }
    
    function displayTableResponse(container, tableData) {
        if (!tableData || !tableData.columns || !tableData.rows || tableData.rows.length === 0) {
            container.innerHTML = '<div class="empty-response">No table data returned</div>';
            return;
        }
        
        const table = document.createElement('table');
        table.className = 'response-table';
        
        // Create header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        
        tableData.columns.forEach(column => {
            const th = document.createElement('th');
            th.textContent = column;
            headerRow.appendChild(th);
        });
        
        thead.appendChild(headerRow);
        table.appendChild(thead);
        
        // Create body
        const tbody = document.createElement('tbody');
        
        tableData.rows.forEach(row => {
            const tr = document.createElement('tr');
            
            row.forEach(cell => {
                const td = document.createElement('td');
                td.textContent = cell;
                tr.appendChild(td);
            });
            
            tbody.appendChild(tr);
        });
        
        table.appendChild(tbody);
        
        container.innerHTML = '';
        container.appendChild(table);
    }
    
    function showError(container, message) {
        container.innerHTML = `<div class="error-message">${message}</div>`;
    }
    
    function clearResponse(container) {
        container.innerHTML = '';
    }
}

// Counter functionality
function initCounter() {
    const decreaseBtn = document.getElementById('decrease-btn');
    const increaseBtn = document.getElementById('increase-btn');
    const resetBtn = document.getElementById('reset-btn');
    const counterValue = document.getElementById('counter-value');
    
    let count = 0;
    
    // Update the counter display
    function updateCounter() {
        counterValue.textContent = count;
        
        // Change color based on value
        if (count < 0) {
            counterValue.style.color = '#e74c3c'; // Red for negative
        } else if (count > 0) {
            counterValue.style.color = '#2ecc71'; // Green for positive
        } else {
            counterValue.style.color = '#333'; // Default for zero
        }
    }
    
    // Event listeners for buttons
    decreaseBtn.addEventListener('click', function() {
        count--;
        updateCounter();
    });
    
    increaseBtn.addEventListener('click', function() {
        count++;
        updateCounter();
    });
    
    resetBtn.addEventListener('click', function() {
        count = 0;
        updateCounter();
    });
}

// Color changer functionality
function initColorChanger() {
    const colorBox = document.getElementById('color-box');
    const colorButtons = document.querySelectorAll('.color-btn');
    
    colorButtons.forEach(button => {
        button.addEventListener('click', function() {
            const color = this.getAttribute('data-color');
            colorBox.style.backgroundColor = color;
            
            // Adjust text color for better visibility
            const textColor = getContrastColor(color);
            colorBox.querySelector('p').style.color = textColor;
        });
    });
}

// Helper function to determine contrasting text color
function getContrastColor(hexColor) {
    // Convert hex to RGB
    const r = parseInt(hexColor.substr(1, 2), 16);
    const g = parseInt(hexColor.substr(3, 2), 16);
    const b = parseInt(hexColor.substr(5, 2), 16);
    
    // Calculate luminance
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
    
    // Return black for bright colors, white for dark colors
    return luminance > 0.5 ? '#000000' : '#ffffff';
}

// Todo list functionality
function initTodoList() {
    const todoInput = document.getElementById('todo-input');
    const addTodoBtn = document.getElementById('add-todo-btn');
    const todoList = document.getElementById('todo-list');
    
    // Load todos from localStorage
    let todos = JSON.parse(localStorage.getItem('gooseAppTodos')) || [];
    
    // Render initial todos
    renderTodos();
    
    // Add new todo
    addTodoBtn.addEventListener('click', addTodo);
    todoInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            addTodo();
        }
    });
    
    function addTodo() {
        const todoText = todoInput.value.trim();
        if (todoText) {
            todos.push({
                id: Date.now(),
                text: todoText,
                completed: false
            });
            
            todoInput.value = '';
            saveTodos();
            renderTodos();
        }
    }
    
    function toggleTodo(id) {
        todos = todos.map(todo => {
            if (todo.id === id) {
                return { ...todo, completed: !todo.completed };
            }
            return todo;
        });
        
        saveTodos();
        renderTodos();
    }
    
    function deleteTodo(id) {
        todos = todos.filter(todo => todo.id !== id);
        saveTodos();
        renderTodos();
    }
    
    function saveTodos() {
        localStorage.setItem('gooseAppTodos', JSON.stringify(todos));
    }
    
    function renderTodos() {
        todoList.innerHTML = '';
        
        if (todos.length === 0) {
            const emptyMessage = document.createElement('li');
            emptyMessage.textContent = 'No tasks yet. Add one above!';
            emptyMessage.style.textAlign = 'center';
            emptyMessage.style.fontStyle = 'italic';
            emptyMessage.style.color = '#7f8c8d';
            todoList.appendChild(emptyMessage);
            return;
        }
        
        todos.forEach(todo => {
            const todoItem = document.createElement('li');
            todoItem.className = `todo-item ${todo.completed ? 'completed' : ''}`;
            
            const todoText = document.createElement('span');
            todoText.textContent = todo.text;
            
            const todoActions = document.createElement('div');
            todoActions.className = 'todo-actions';
            
            const toggleBtn = document.createElement('button');
            toggleBtn.className = 'todo-toggle';
            toggleBtn.textContent = todo.completed ? 'Undo' : 'Complete';
            toggleBtn.addEventListener('click', () => toggleTodo(todo.id));
            
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'todo-delete';
            deleteBtn.textContent = 'Delete';
            deleteBtn.addEventListener('click', () => deleteTodo(todo.id));
            
            todoActions.appendChild(toggleBtn);
            todoActions.appendChild(deleteBtn);
            
            todoItem.appendChild(todoText);
            todoItem.appendChild(todoActions);
            
            todoList.appendChild(todoItem);
        });
    }
}

// Display current date in footer
function displayCurrentDate() {
    const dateElement = document.getElementById('current-date');
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    const currentDate = new Date().toLocaleDateString(undefined, options);
    dateElement.textContent = currentDate;
}