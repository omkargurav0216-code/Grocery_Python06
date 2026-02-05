document.addEventListener('DOMContentLoaded', () => {
    // --- New Order Calculation ---
    const qtyInputs = document.querySelectorAll('.qty-input');
    const totalDisplay = document.getElementById('total-display');

    if (qtyInputs.length > 0 && totalDisplay) {
        function calculateTotal() {
            let total = 0;
            qtyInputs.forEach(input => {
                const qty = parseFloat(input.value) || 0;
                const price = parseFloat(input.getAttribute('data-price')) || 0;

                // Visual feedback for selected items
                const card = input.closest('.card');
                if (qty > 0) {
                    card.classList.add('active-selection');
                } else {
                    card.classList.remove('active-selection');
                }

                total += qty * price;
            });
            totalDisplay.textContent = total.toFixed(2);
        }

        qtyInputs.forEach(input => {
            input.addEventListener('input', calculateTotal);
        });
    }

    // --- Product Search ---
    const searchInput = document.getElementById('product-search');
    if (searchInput) {
        searchInput.addEventListener('keyup', (e) => {
            const term = e.target.value.toLowerCase();
            const cards = document.querySelectorAll('.product-grid .card');
            let hasResults = false;

            cards.forEach(card => {
                const name = card.querySelector('div:first-child').innerText.toLowerCase();
                if (name.includes(term)) {
                    card.style.display = '';
                    hasResults = true;
                } else {
                    card.style.display = 'none';
                }
            });

            // Optional: Handle empty state if we added an empty state element
        });
    }

    // --- Active Nav Highlighting (Fallback if Jinja fails or for dynamic changes) ---
    // (Jinja handles most of this, but we can double check)
});
