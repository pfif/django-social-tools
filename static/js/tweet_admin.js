(function($) {

    $(document).ready(function() {

        function setSelectOptions(data) {
            $('#tweet-msgs').html('<option></option>');
            for(var x=0; x<data.length; x++) {
                var msg = data[x].copy;
                var option = $('<option></option>').attr('value', msg).text(msg);
                $('#tweet-msgs').append(option);
            }
        }

        var tweet_pk;
        var handle;

        $('.send_tweet').on('click', function(e) {

            // This is a bit horrible but will grab the account text so we can get
            //the particular id for this to filter messages against
            var account = $(this).parent().parent().parent().prev().prev().prev().prev().text();
            var account_id = account.match(/\((\d+)\)/)[1];
            tweet_pk = $(this).closest('td').prevAll(':last').find('.action-select').val();
            handle = $(this).closest('td').prevAll(':eq(4)').find('a').text();

            // reset modal form
            $('#tweet-msg').val('');
            $('#tweet-log').html('');
            $('.modal-tweet').val('Send');

            // TODO: you should be ashamed! pass as obj instead and undupe this!
            if($(this).data('msgtype') == 'tryagain') {
                $.getJSON('/api/messages/?type=f&account=' + account_id, setSelectOptions);
            } else {
                $.getJSON('/api/messages/?type=s&account=' + account_id, setSelectOptions);
            }

            $('#myModal').modal();
        });

        $('#tweet-msgs').on('change', function(e) {
            $('#tweet-msg').val('@' + handle + ' ' + $('#tweet-msgs').val());
        });

        $('.modal-tweet').on('click', function(e) {
            var msg = $('#tweet-msg').val();
            $(this).parentsUntil('#modal').find('#tweet-log').load('/send-tweet/?msg=' + escape(msg) + '&tweet_pk=' + tweet_pk);
        });

        var textareaPlaceholder = 'Add an internal note (not public)';
        $('#result_list .vLargeTextField').attr('placeholder', textareaPlaceholder);

    });

})(django.jQuery);
