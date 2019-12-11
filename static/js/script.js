var img_template = "https://babel.hathitrust.org/cgi/imgsrv/thumbnail?id=uc1.b3921033;seq=26;width=250;rotation=0"

function create_image(id, seq=10, width=250) {
    
    url = `https://babel.hathitrust.org/cgi/imgsrv/thumbnail?id=${id};seq=${seq};width=${width};rotation=0`;
    link = `https://babel.hathitrust.org/cgi/pt?id=${id}&view=1up&seq=${seq}`
    $img = $('<img>').attr('src', url)
    $a = $('<a target="_blank">').attr('href', link).append($img).attr('tabindex', '-1')
    
    return $a;
}

function get_stats() {
    
}

function id_encode(htid) {
    libid = htid.substr(0,htid.indexOf('.'));
    volid = htid.substr(htid.indexOf('.')+1);
    volid_clean = volid.replace(":", "+").replace("/", "=").replace(".", ",");
    return `${libid}.${volid_clean}`;
}

function id_decode(htid) {
    return htid.replace("+", ":").replace("=", "/").replace(",", ".");
}

function css_escape(htid) {
    clean_htid = id_encode(htid);
    return clean_htid.replace(/\./g, '-A').replace(/\$/g, '-B')
        .replace(/\,/g, '-C').replace(/\+/g, '-D')
        .replace(/\=/g, '-E').replace(/\_/g, '-F')
}

function css_unescape(htid) {
    unescaped = htid.replace(/-A/g, '.').replace(/-B/g, '$').replace(/-C/g, ',')
                    .replace(/-D/g, '+').replace(/-E/g,'=').replace(/-F/g,'_')
    return id_decode(unescaped)
}

function draw_vol(vol, target, appendTo="#main", isTarget=false) {
        // an htid that can be in a css name (a-z, A-Z, -, _)
        var htid_css = css_escape(vol.htid);
    
        el = $(blurb_template).attr('id', vol.htid).data('htid', vol.htid);
        $(appendTo).append(el).append("<hr />");
    
        fields = ['title', 'author', 'oclc_num', 'description', 'rights_date_used', 
                  'date', 'isbn', 'issn', 'lccn', 'page_count'];
    
        $.each(fields, function(i, field) {
            el.find('span.' + field).text(vol[field]);
            fieldline = el.find(`.${field}-line`);
            if (isTarget === true) {
                return;
            }
            if ((vol[field] === target[field]) & 
                       ((vol[field] == null) | (vol[field] == false))
                      ) {
                fieldline.addClass('text-muted');
            } else if (vol[field] === target[field]) {
                fieldline.addClass('text-success');
            } else if ((field === 'page_count') && (Math.abs(vol[field] - target[field]) < 10)) {
                fieldline.addClass('text-warning');
            } else {
                fieldline.addClass('text-danger');
            }
                                      
        });
    
    
        el.find('select.judgment')
            .attr('name', 'judgment-'+htid_css)
            .focus(function() {
                    var form = $('form');
                    var el = $(this).parents('.blurb');
                    var offsetTop = el.offset().top;
                    $('html, body').scrollTop(offsetTop);
                    el.find("button.imagelink").trigger("click");
                $(".urlsubmit").text(form.attr('action') + '?' + form.serialize());
                
            });
    
    
        el.find('.notes').attr('name', 'notes-'+htid_css);
        
        el.find("button.imagelink").on('click', function() {
            var that = $(this);
            var el = that.parents('.blurb');
            that.hide();
            
            that.parents(".image-box").css('height', '204px');
            el.data('first', 10);
            el.data('last', 13);
            
            $.each([10,11, 12, 13], function(i,seq) { 
                $img = create_image(vol.htid, seq, 150);
                that.parent().append($img);
            });
            
            el.find(".image-controls").show();
            
            el.find(".prependImage").on('click', function() {
                for (i = 0; i < 2; i++) {
                    n = el.data('first') - 1;
                    if (n > 0) {
                        $img = create_image(vol.htid, n, 150);
                        that.parent().prepend($img);
                        el.data('first', n);
                    }
                }
            });
            
            el.find(".appendImage").on('click', function() {
                for (i = 0; i < 2; i++) {
                    n = el.data('last') + 1;
                    $img = create_image(vol.htid, n, 150);
                    that.parent().append($img);
                    el.data('last', n);
                }
                
            });
        });  
    
    $( "input[type='text'], select" ).change(function() {
            var form = $('form');
            $(".urlsubmit").text(form.attr('action') + '?' + form.serialize());
        });
    
    if (isTarget === true) {
        el.find(".ratings").hide();
        el.addClass("targetVol");
        el.find("button.imagelink").trigger("click");
        el.find(".image-box").css('height', '408px');
    }
}

$(document).ready(function() {
     blurb_template = $('#blurb-template').html(); //fyi, global because I'm rushing
    var search = new URLSearchParams(location.search);
    
    if (search.has('htid') === true) {
        var htid, clean_htid, target, data;
        htid = css_unescape(search.get('htid'));
        clean_htid = id_encode(htid);
        $.getJSON( "data/"+clean_htid+".json", function(data) {
            $('title').text("Evaluation: " + data.target.title)
            $.each(data.data, function (i,vol) {
                draw_vol(vol, data.target);
            });
            
            $('.targetId').attr('value', htid);
            draw_vol(data.target, false, "#sidebar", true);
        });
    };
    
    if (search.has('name') === true) {
        $('.name-field').attr('value', search.get('name'));
    };
    
    $('html, body').scrollTop();
    
});
