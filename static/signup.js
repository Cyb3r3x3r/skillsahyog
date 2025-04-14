document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('form');
    const passwordInput = document.getElementById('password');
    const rePasswordInput = document.getElementById('re-password');

    form.addEventListener('submit', function (event) {
        const password = passwordInput.value;
        const rePassword = rePasswordInput.value;

        const passwordCriteria = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,16}$/;

        if (!passwordCriteria.test(password)) {
            alert('Password must contain at least 1 uppercase letter, 1 lowercase letter, 1 number, 1 special character, and be 8-16 characters long.');
            event.preventDefault();
            return;
        }

        if (password !== rePassword) {
            alert('Passwords do not match.');
            event.preventDefault();
            return;
        }
    });
});
