$(function() {
    $('#btnSignUp').click(function() {
        $.ajax({
            url: FLASK_URLS.signUp,
            type: 'POST',
            data: $('#signupForm').serialize(),
            dataType: 'json',  // tells jQuery to expect JSON
            success: function(res) {
                if (res.message) {
                    alert(res.message);
                    window.location.href = FLASK_URLS.showSignIn;
                } else {
                    alert(res.error);
                }
            },
            error: function(xhr) {
                console.error(xhr.responseText);
                alert('Signup failed: ' + xhr.responseText);
            }
        });
    });
});
