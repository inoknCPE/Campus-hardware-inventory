document.querySelectorAll('.password-toggle').forEach(function (toggle) {
    toggle.addEventListener('click', function () {
        var input = document.getElementById(toggle.getAttribute('aria-controls'));
        var showing = input.type === 'text';
        input.type = showing ? 'password' : 'text';
        toggle.setAttribute('aria-label', showing ? 'Show password' : 'Hide password');
        toggle.setAttribute('title', showing ? 'Show password' : 'Hide password');
    });
});

document.querySelectorAll('.item-selector').forEach(function (selector) {
    selector.addEventListener('change', function () {
        var quantity = document.getElementById(selector.getAttribute('data-quantity-id'));
        quantity.disabled = !selector.checked;
        if (selector.checked) {
            quantity.focus();
        }
    });
});
