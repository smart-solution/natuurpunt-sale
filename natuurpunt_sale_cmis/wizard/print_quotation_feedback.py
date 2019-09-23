# coding: utf-8
from osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc

WARNING_TYPES = [('warning','Warning'),('info','Information'),('error','Error')]

class print_quotation_feedback(osv.osv_memory):
    _name = 'print.quotation.feedback'
    _description = 'feedback print quotation'
    _columns = {
        'type': fields.selection(WARNING_TYPES, string='Type', readonly=True),
        'title': fields.char(string="Title", size=100, readonly=True),
        'message': fields.text(string="Message", readonly=True),
        'sale_order_id': fields.integer(readonly=True),
    }
    _req_name = 'title'

    def _get_view_id(self, cr, uid):
        """Get the view id
        @return: view id, or False if no view found
        """
        res = self.pool.get('ir.model.data').get_object_reference(cr, uid,
                'natuurpunt_sale_cmis', 'print_quotation_feedback_view')
        return res and res[1] or False

    def message(self, cr, uid, id, context):
        message = self.browse(cr, uid, id)
        message_type = [t[1]for t in WARNING_TYPES if message.type == t[0]][0]
        print '%s: %s' % (_(message_type), _(message.title))
        res = {
               'name': '%s: %s' % (_(message_type), _(message.title)),
               'view_type': 'form',
               'view_mode': 'form',
               'view_id': self._get_view_id(cr, uid),
               'res_model': 'print.quotation.feedback',
               'domain': [],
               'context': context,
               'type': 'ir.actions.act_window',
               'target': 'new',
               'res_id': message.id
        }
        return res

    def print_quotation(self, cr, uid, ids, context=None):
        for message in self.browse(cr, uid, ids):
            sale_order_id = message.sale_order_id
            return self.pool.get('sale.order').create_print_quotation(cr,uid,[sale_order_id])
        
    def warning(self, cr, uid, title, message, sale_order_id, context=None):
        id = self.create(cr, uid, {'title': title, 'message': message, 'type': 'warning', 'sale_order_id': sale_order_id })
        res = self.message(cr, uid, id, context)
        return res

    def info(self, cr, uid, title, message, sale_order_id, context=None):
        id = self.create(cr, uid, {'title': title, 'message': message, 'type': 'info', 'sale_order_id': sale_order_id })
        res = self.message(cr, uid, id, context)
        return res

    def error(self, cr, uid, title, message, sale_order_id, context=None):
        id = self.create(cr, uid, {'title': title, 'message': message, 'type': 'error', 'sale_order_id': sale_order_id })
        res = self.message(cr, uid, id, context)
        return res
