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
    const messageInput = document.getElementById('goose-message');
    const sendButton = document.getElementById('goose-send-btn');
    const clearButton = document.getElementById('goose-clear-btn');
    const responseContainer = document.getElementById('goose-response');
    const formatSelect = document.getElementById('response-format');
    
    // Add event listeners
    sendButton.addEventListener('click', sendMessage);
    clearButton.addEventListener('click', clearResponse);
    
    async function sendMessage() {
        const message = messageInput.value.trim();
        const format = formatSelect ? formatSelect.value : 'list';
        
        if (!message) {
            showError('Please enter a message');
            return;
        }
        
        // Clear previous response and show loading
        responseContainer.innerHTML = '<div class="loading-message">Sending request...</div>';
        
        try {
            let response;
            
            // Use the appropriate request function based on the selected format
            switch (format) {
                case 'text':
                    response = await gooseRequestText(message);
                    displayTextResponse(response);
                    break;
                    
                case 'table':
                    // Define columns for the table based on the query
                    const tableColumns = determineTableColumns(message);
                    response = await gooseRequestTable(message, tableColumns);
                    displayTableResponse(response);
                    break;
                    
                case 'list':
                default:
                    response = await gooseRequestList(message);
                    displayListResponse(response);
                    break;
            }
            
        } catch (error) {
            console.error('Error:', error);
            showError(`Error: ${error.message}`);
        }
    }
    
    function displayTextResponse(text) {
        responseContainer.innerHTML = `<div class="text-response">${text}</div>`;
    }
    
    function displayListResponse(items) {
        if (!Array.isArray(items) || items.length === 0) {
            responseContainer.innerHTML = '<div class="empty-response">No items returned</div>';
            return;
        }
        
        const list = document.createElement('ul');
        list.className = 'response-list';
        
        items.forEach(item => {
            const li = document.createElement('li');
            li.textContent = item;
            list.appendChild(li);
        });
        
        responseContainer.innerHTML = '';
        responseContainer.appendChild(list);
    }
    
    function displayTableResponse(tableData) {
        if (!tableData || !tableData.columns || !tableData.rows || tableData.rows.length === 0) {
            responseContainer.innerHTML = '<div class="empty-response">No table data returned</div>';
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
        
        responseContainer.innerHTML = '';
        responseContainer.appendChild(table);
    }
    
    function showError(message) {
        responseContainer.innerHTML = `<div class="error-message">${message}</div>`;
    }
    
    function clearResponse() {
        responseContainer.innerHTML = '';
    }
    
    // Helper function to determine appropriate table columns based on the query
    function determineTableColumns(query) {
        // Default columns if we can't determine better ones
        const defaultColumns = ["Item", "Description"];
        
        // Common column patterns based on query keywords
        if (/compar(e|ison)|vs\.?|versus/i.test(query)) {
            return ["Feature", "Option 1", "Option 2"];
        } else if (/pros?\s+and\s+cons/i.test(query)) {
            return ["Item", "Pros", "Cons"];
        } else if (/advantages|benefits/i.test(query)) {
            return ["Item", "Advantages", "Disadvantages"];
        } else if (/price|cost|budget/i.test(query)) {
            return ["Item", "Price", "Description"];
        } else if (/stat(s|istics)|data|numbers/i.test(query)) {
            return ["Metric", "Value", "Notes"];
        } else if (/schedule|time|agenda/i.test(query)) {
            return ["Time", "Activity", "Details"];
        } else if (/recipe|ingredient/i.test(query)) {
            return ["Ingredient", "Amount", "Notes"];
        } else if (/rank|rating|score/i.test(query)) {
            return ["Rank", "Item", "Score"];
        }
        
        return defaultColumns;
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