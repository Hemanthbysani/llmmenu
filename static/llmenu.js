document.addEventListener('DOMContentLoaded', function () {
    const chatBody = document.getElementById('chat-body');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    
    // Add loading indicator
    const createLoadingIndicator = () => {
        const loadingElement = document.createElement('div');
        loadingElement.classList.add('chat-message', 'bot', 'loading');
        loadingElement.textContent = "Thinking";
        
        // Add animated dots
        const dots = document.createElement('span');
        dots.classList.add('loading-dots');
        loadingElement.appendChild(dots);
        
        chatBody.appendChild(loadingElement);
        chatBody.scrollTop = chatBody.scrollHeight;
        
        // Animate the dots
        let dotCount = 0;
        const dotInterval = setInterval(() => {
            dots.textContent = '.'.repeat(dotCount % 4);
            dotCount++;
        }, 300);
        
        return { element: loadingElement, interval: dotInterval };
    };

    function appendMessage(content, sender) {
        // Remove any existing loading indicators
        const loadingIndicators = document.querySelectorAll('.loading');
        loadingIndicators.forEach(indicator => {
            // Clear any intervals associated with the loading indicator
            if (indicator.interval) {
                clearInterval(indicator.interval);
            }
            indicator.remove();
        });
        
        const messageElement = document.createElement('div');
        messageElement.classList.add('chat-message', sender);
        
        // Handle message formatting
        if (sender === 'bot') {
            // Use regex to find items with prices for highlighting
            const regex = /(\w+(?:\s+\w+)*)\s*:\s*\$(\d+(?:\.\d{1,2})?)/g;
            let formattedContent = content.replace(regex, '<strong>$1: $$$2</strong>');
            
            // Convert URLs to links
            formattedContent = formattedContent.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
            
            messageElement.innerHTML = formattedContent;
        } else {
            messageElement.textContent = content;
        }
        
        chatBody.appendChild(messageElement);
        
        // Smooth scroll to the latest message
        setTimeout(() => {
            messageElement.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }, 100);
    }

    async function sendMessage() {
        const message = userInput.value.trim();
        if (message) {
            appendMessage(message, 'user');
            userInput.value = '';
            userInput.focus();
            
            // Add loading indicator
            const { element: loadingIndicator, interval } = createLoadingIndicator();
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ message: message })
                });
                
                // Clear the loading indicator interval
                clearInterval(interval);
                
                const data = await response.json();
                appendMessage(data.response, 'bot');
            } catch (error) {
                console.error('Error:', error);
                // Clear the loading indicator interval
                clearInterval(interval);
                // Remove the loading indicator
                loadingIndicator.remove();
                appendMessage("Sorry, I couldn't process your request. Please try again later.", 'bot');
            }
        }
    }

    sendButton.addEventListener('click', sendMessage);
    
    // Add button animation on click
    sendButton.addEventListener('mousedown', function() {
        this.style.transform = 'scale(0.95)';
    });
    
    sendButton.addEventListener('mouseup', function() {
        this.style.transform = '';
    });

    userInput.addEventListener('keypress', function (event) {
        if (event.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Add click event listeners for menu items to allow quick ordering suggestions
    document.querySelectorAll('.menu-list-item').forEach(item => {
        item.addEventListener('click', function() {
            const itemName = this.querySelector('.menu-item-name').textContent;
            userInput.value = `I'd like to order ${itemName}`;
            userInput.focus();
        });
    });
    
    // Focus the input field on page load
    userInput.focus();
});
