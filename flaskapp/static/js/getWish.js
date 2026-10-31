$(function() {
    $.ajax({
        url: FLASK_URLS.getWish,
        type: 'GET',
        success: function(res) {
            try {
                var wishObj = JSON.parse(res);
                $('.jumbotron').empty(); // clear old wishes

                $.each(wishObj, function(index, value) {
                    var wish = $('<div class="list-group">')
                        .append($('<a class="list-group-item active">')
                            .append($('<h4 class="list-group-item-heading">').text(value.Title))
                            .append($('<p class="list-group-item-text">').text(value.Description))
                        );
                    $('.jumbotron').append(wish);
                });
            } catch (e) {
                console.error('Failed to parse wishes:', e);
                alert('Failed to load wishes. Please refresh the page.');
            }
        },
        error: function(error) {
            console.error(error);
            alert('Failed to load wishes. Please refresh the page.');
        }
    });
});
