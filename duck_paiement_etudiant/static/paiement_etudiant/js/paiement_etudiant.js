/**
 * Created by paulguichon on 03/02/15.
 */
(function($){
    $(document).ready(function(){
        function show_hide(num, val){
            var champs_banque = ['num_cheque', 'nom_banque' ];
            var champs_virement = ['date', 'date_virement' ];
            if(val == 'V'){
                $.each(champs_virement, function(index, value){
                    $('#div_id_paiements-'+num+'-'+value).show();
                });
                $.each(champs_banque, function(index, value){
                    $('#div_id_paiements-'+num+'-'+value).hide();
                });
            }
            else {
                $.each(champs_virement, function(index, value){
                    $('#div_id_paiements-'+num+'-'+value).hide();
                });
                $.each(champs_banque, function(index, value){
                    $('#div_id_paiements-'+num+'-'+value).show();
                });
            }
        }
       $("select[id*='-type']").each(function(){
           var num = $(this).attr('id').split('-').slice(-2)[0];
           show_hide(num, $(this).val());
           $(this).change(function(){
              show_hide(num, $(this).val());
           });
       });
    });
})(jQuery);