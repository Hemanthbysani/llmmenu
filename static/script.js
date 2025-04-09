// JavaScript to dynamically update the total price based on selected items and quantities
document.addEventListener('DOMContentLoaded', function () {
    const checkboxes = document.querySelectorAll('.menu-item-checkbox');
    const quantities = document.querySelectorAll('.item-quantity');
    const totalPriceElement = document.getElementById('total-price');

    function updateTotalPrice() {
        let totalPrice = 0;
        checkboxes.forEach(function (checkbox, index) {
            if (checkbox.checked) {
                const price = parseFloat(checkbox.getAttribute('data-price'));
                const quantity = parseInt(quantities[index].value, 10);
                totalPrice += price * quantity;
            }
        });
        totalPriceElement.textContent = totalPrice.toFixed(2);
    }

    checkboxes.forEach(function (checkbox) {
        checkbox.addEventListener('change', updateTotalPrice);
    });
    quantities.forEach(function (quantity) {
        quantity.addEventListener('input', updateTotalPrice);
    });

    updateTotalPrice();
});
