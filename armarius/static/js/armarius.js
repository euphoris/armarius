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
    $('.edit').click(function(){
        $('#page-content').attr('contentEditable', true);
        CKEDITOR.inline( 'page-content' );

        $('.save').toggle();
        $('.edit').toggle();

        return false;
    });
    $('.save').click(function(){
        $('#page-content').attr('contentEditable', false);
        CKEDITOR.instances['page-content'].destroy();

        $('.save').toggle();
        $('.edit').toggle();

        $.ajax({
            url: $('#save-form').attr('action'),
            type: 'post',
            data: {
                content: $('#page-content').html(),
                old_title: $('input[name="old_title"]').val(),
                title: $('input[name="title"]').val()
            }
        });
        return false;
    });
});
