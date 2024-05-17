const ExternalHtmlPlugin = {
    id: 'external-html',
    init: function(deck) {
        function fetchAndInsertHTML(element, url) {
            fetch(url)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok ' + response.statusText);
                    }
                    return response.text();
                })
                .then(data => {
                    const tempDiv = document.createElement('div');
                    tempDiv.innerHTML = data;
                    // Replace the placeholder div with the fetched content
                    while (tempDiv.firstChild) {
                        element.parentNode.insertBefore(tempDiv.firstChild, element);
                    }
                    element.parentNode.removeChild(element);
                    if (typeof MathJax !== 'undefined') {
                        MathJax.typesetPromise([element]).then(() => {
                            deck.sync(); // Reinitialize fragments
                        });
                    } else {
                        deck.sync(); // Reinitialize fragments
                    }
                })
                .catch(error => console.error('Error loading HTML:', error));
        }

        function replacePlaceholdersWithHTML() {
            const placeholders = document.querySelectorAll('[data-external-html]');
            placeholders.forEach(placeholder => {
                const url = placeholder.getAttribute('data-external-html');
                if (!placeholder.hasAttribute('data-loaded')) {
                    fetchAndInsertHTML(placeholder, url);
                    placeholder.setAttribute('data-loaded', 'true');
                }
            });
        }

        deck.on('ready', function(event) {
            replacePlaceholdersWithHTML();
        });

        deck.on('slidechanged', function(event) {
            const currentSlide = event.currentSlide;
            const placeholders = currentSlide.querySelectorAll('[data-external-html]');
            placeholders.forEach(placeholder => {
                const url = placeholder.getAttribute('data-external-html');
                if (!placeholder.hasAttribute('data-loaded')) {
                    fetchAndInsertHTML(placeholder, url);
                    placeholder.setAttribute('data-loaded', 'true');
                } else {
                    if (typeof MathJax !== 'undefined') {
                        MathJax.typesetPromise([placeholder]).then(() => {
                            deck.sync(); // Reinitialize fragments
                        });
                    }
                }
            });
        });
    }
};

Reveal.registerPlugin('external-html', ExternalHtmlPlugin);
