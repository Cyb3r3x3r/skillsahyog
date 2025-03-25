let currentText = 0; // Index for the phrases
const texts = ["sharing skills", "helping others"];
const textElement = document.getElementById('dynamic-text');
const typingSpeed = 100; // Speed of typing
const clearingSpeed = 50; // Speed of clearing text
const changeInterval = 1500; // Time to wait before changing the text

// Function to type out the text
function typeText(text, index) {
    let i = 0;
    textElement.textContent = ""; // Clear existing text
    // Disable cursor blinking animation while typing
    textElement.style.animation = 'none';
    
    const typingInterval = setInterval(() => {
        textElement.textContent += text.charAt(i);
        i++;
        if (i === text.length) {
            clearInterval(typingInterval);
            // Re-enable the cursor blink after typing is complete
            textElement.style.animation = 'blinkCaret 0.75s step-end infinite';
            setTimeout(() => clearText(), changeInterval);
        }
    }, typingSpeed);
}

// Function to clear the text
function clearText() {
    let i = textElement.textContent.length;
    const clearingInterval = setInterval(() => {
        textElement.textContent = textElement.textContent.slice(0, i - 1);
        i--;
        if (i === 0) {
            clearInterval(clearingInterval);
            currentText = (currentText + 1) % texts.length; // Toggle between texts
            typeText(texts[currentText], currentText);
        }
    }, clearingSpeed);
}

// Start the typing effect on load
typeText(texts[currentText], currentText);

