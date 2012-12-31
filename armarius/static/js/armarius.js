var html = '';

function save(){
    var new_html = $('#page-content').html();

    if( html != new_html){
        $.ajax({
            url: $('#save-form').attr('action'),
            type: 'post',
            data: {
                content: new_html,
                old_title: $('input[name="old_title"]').val(),
                title: $('input[name="title"]').val(),
                success: function(){
                    html = new_html;
                }
            }
        });
    }
}

function urlize(){
    var nodelist = [],
        link_re = /(\bhttps?:\/\/[-A-Z0-9+&amp;@#\/%?=~_|!:,.;]+)/ig;

    $('#page-content').contents().each(function(){
        nodelist.push(this);
    });

    while( nodelist.length > 0 ){
        var node = nodelist.pop();

        if( node.nodeName != 'A' && node.nodeName != 'a' ){
            var contents = $(node).contents();
            contents.filter(function(){ return this.nodeName == '#text' }).
                replaceWith(function(){
                    return this.textContent.replace(link_re, '<a href="$1">$1</a>');
                });

            contents.filter(function(){ return this.nodeName != '#text' })
                .each(function(){
                    nodelist.push(this);
                });
        }
    }
}

$(function(){
    $('textarea').focus();
    $('input[name=q]').focus();

    // ckeditor configuration
    CKEDITOR.plugins.addExternal( 'timestamp', plugin_addr );
    CKEDITOR.config.extraPlugins = 'timestamp';
    CKEDITOR.config.toolbar =
        [
        { name: 'clipboard', items : [ 'Cut','Copy','Paste','PasteText','PasteFromWord','-','Undo','Redo' ] },
        { name: 'editing', items : [ 'Find','Replace','-','SelectAll','-','SpellChecker', 'Scayt' ] },
        { name: 'insert', items : [ 'Image','Flash','Table','HorizontalRule','Smiley','SpecialChar' ] },
        { name: 'tools', items : [ 'Maximize', 'ShowBlocks','-','About' ] },
        '/',
        { name: 'basicstyles', items : [ 'Bold','Italic','Underline','Strike','Subscript','Superscript','-','RemoveFormat' ] },
        { name: 'paragraph', items : [ 'NumberedList','BulletedList','-','Outdent','Indent','-','Blockquote'] },
        { name: 'links', items : [ 'Link','Unlink','Anchor' ] },
        { name: 'styles', items : [ 'Format'] },
        { name: 'colors', items : [ 'TextColor','BGColor' ] },
        ];
    CKEDITOR.disableAutoInline = true;

    // edit buttons
    var interval = null;
    $('.edit').click(function(){
        $('#page-content').attr('contentEditable', true);
        CKEDITOR.inline( 'page-content' );

        html = $('#page-content').html();

        interval = window.setInterval(save, 5000);

        $('.save').toggle();
        $('.edit').toggle();

        return false;
    });
    $('.save').click(function(){
        $('#page-content').attr('contentEditable', false);
        CKEDITOR.instances['page-content'].destroy();

        $('.save').toggle();
        $('.edit').toggle();

        if( interval ) clearInterval(interval);

        urlize();
        save();

        return false;
    });
});
