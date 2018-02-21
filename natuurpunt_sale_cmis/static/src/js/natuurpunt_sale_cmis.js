/*---------------------------------------------------------
 * custom instance.web.ListView.List and template support
 * for alfresco 
 * listview has clickable link to alfresco document
 *---------------------------------------------------------*/

openerp.natuurpunt_sale_cmis = function(instance) {

// here you may tweak globals object, if any, and play with on_* or do_* callbacks on them

   var QWeb = instance.web.qweb;

   instance.web.ListView.List.include({
       render: function () {
            var template = (this.dataset.model == 'sale.order.attachment' ? 'Alfresco.ListView.rows' : 'ListView.rows');
            this.$current.empty().append(
                QWeb.render(template, _.extend({
                        render_cell: function () {
                            return self.render_cell.apply(self, arguments); }
                    }, this)));
            this.pad_table_to(4);
        },
    });

};

// vim:et fdc=0 fdl=0:
