const passphraseElement = document.getElementById('passphrase');
const copyIcon = document.getElementById('copyIcon');
const generateBtn = document.getElementById('generateBtn');

async function generatePassphrase() {
    try {
        const classification = document.querySelector('input[name="classification"]:checked').value;
        const response = await fetch(`/api/v1/rng?classification=${encodeURIComponent(classification)}`);
        if (!response.ok) {
            throw new Error('Failed to fetch passphrase');
        }
        const data = await response.json();
        passphraseElement.textContent = data.passphrase;
    } catch (error) {
        console.error('Error generating passphrase:', error);
        passphraseElement.textContent = 'Error generating passphrase';
    }
}

function copyToClipboard() {
    const text = passphraseElement.textContent;
    navigator.clipboard.writeText(text).then(() => {
        const originalIcon = copyIcon.querySelector('img').src;
        copyIcon.querySelector('img').src = 'images/tick-icon.svg'; // Replace with tick icon

        // Trigger flash circle animation
        const flashCircle = copyIcon.querySelector('.flash-circle');
        flashCircle.classList.add('active');
        setTimeout(() => {
            flashCircle.classList.remove('active');
        }, 200);
        setTimeout(() => {
            copyIcon.querySelector('img').src = originalIcon;
        }, 1500);
    }).catch(err => {
        console.error('Failed to copy text: ', err);
    });
}

generateBtn.addEventListener('click', generatePassphrase);
copyIcon.addEventListener('click', copyToClipboard);