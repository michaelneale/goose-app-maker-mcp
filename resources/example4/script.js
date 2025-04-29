// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the app
    initFlowerList();
    displayCurrentDate();
    
    // Log that the app is ready
    console.log('Flower List App is ready!');
});

// Flower list functionality
function initFlowerList() {
    const getFlowersBtn = document.getElementById('get-flowers-btn');
    const flowerList = document.getElementById('flower-list');
    const loadingElement = document.getElementById('loading');
    
    // Add event listener for the get flowers button
    getFlowersBtn.addEventListener('click', getRandomFlowers);
    
    // Function to get random flowers
    async function getRandomFlowers() {
        // Show loading state
        flowerList.innerHTML = '';
        loadingElement.classList.remove('hidden');
        
        try {
            // Request a list of random flowers from Goose
            const flowers = await gooseRequestList('Give me a list of 10 random beautiful flowers with their scientific names in parentheses. Format each entry as "Common Name (Scientific Name)"');
            
            // Hide loading state
            loadingElement.classList.add('hidden');
            
            // Display the flowers
            displayFlowers(flowers);
        } catch (error) {
            console.error('Error:', error);
            
            // Hide loading state
            loadingElement.classList.add('hidden');
            
            // Show error message
            flowerList.innerHTML = `
                <li style="color: var(--accent-red); border-left-color: var(--accent-red);">
                    Error loading flowers: ${error.message}
                </li>
            `;
            
            // Report the error to Goose
            try {
                await reportError(`Error getting flower list: ${error.message}`);
            } catch (reportError) {
                console.error('Failed to report error:', reportError);
            }
        }
    }
    
    // Function to display flowers in the list
    function displayFlowers(flowers) {
        // Clear the list
        flowerList.innerHTML = '';
        
        if (!Array.isArray(flowers) || flowers.length === 0) {
            flowerList.innerHTML = '<li class="placeholder">No flowers found. Try again!</li>';
            return;
        }
        
        // Add each flower to the list
        flowers.forEach(flower => {
            const li = document.createElement('li');
            li.textContent = flower;
            flowerList.appendChild(li);
            
            // Add a small animation delay for each item
            const delay = Array.from(flowerList.children).indexOf(li) * 100;
            li.style.animation = `fadeIn 0.5s ease ${delay}ms forwards`;
            li.style.opacity = '0';
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

// Add a CSS animation for the fade-in effect
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
`;
document.head.appendChild(style);