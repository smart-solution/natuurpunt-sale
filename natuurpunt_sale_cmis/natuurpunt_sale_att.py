# -*- coding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
############################################################################## 

from openerp.osv import fields, osv
from openerp.tools.translate import _

class ir_attachment_type(osv.osv):
    _name = 'ir.attachment.type'

    _columns = {
        'name': fields.char('Document type', size=128, required=True),
    }

ir_attachment_type()

class sale_order_attachment(osv.osv):
    _name = 'sale.order.attachment'

    _columns = {
        'order_id': fields.many2one('sale.order', 'Sale order', select=True),
        'doc_type_id': fields.many2one('ir.attachment.type', 'Document type', select=True),
        'name': fields.char('file name', help="sale order attachment"),
        'attachment_id': fields.many2one('ir.attachment', 'CMIS Attachment',),
        'url': fields.related(
                'attachment_id',
                'url',
                type="char",
                relation="ir.attachment",
                string="URL",
                store=False)
    }

sale_order_attachment()

class sale_order(osv.osv):

        _inherit = "sale.order"

        _columns = {
            'attachment_ids': fields.one2many('sale.order.attachment', 'order_id', 'sale order attachment'),
        }

        def copy(self, cr, uid, ids, default=None, context=None):
            if not default:
                default = {}
            default.update({
                'attachment_ids': False,
            })
            return super(sale_order, self).copy(cr, uid, ids, default=default, context=context)

class sale_order_line_make_invoice(osv.osv_memory):

    _inherit="sale.order.line.make.invoice"

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        """
        link order to invoice
        """
        res = super(sale_order_line_make_invoice, self)._prepare_invoice(cr, uid, order, lines, context=context)
        res['order_id'] = order.id
        return res

class account_invoice(osv.osv):

        _inherit = "account.invoice"

        _columns = {
            'order_id': fields.many2one('sale.order', 'Sale order', select=True),
            'sale_order_attachment_ids': fields.related('order_id','attachment_ids', type='one2many', relation='sale.order.attachment', string='sale order attachment'),
        }

class ir_attachment(osv.osv):

    _inherit = 'ir.attachment'

    def create(self, cr, uid, vals, context=None):
        """Send the document to the CMIS server and create the attachment"""

        res = super(ir_attachment, self).create(cr, uid, vals, context)
        if vals['res_model'] == 'sale.order':
            sale_order_att_obj = self.pool.get('sale.order.attachment')
            att_vals = {
                'order_id': vals['res_id'],
                'name': vals['name'],
                'attachment_id': res,
            }
            sale_order_att_obj.create(cr,uid, att_vals, context)
        return res

    def unlink(self, cr, uid, ids, context=None):
        """Delete the cmis document when a ressource is deleted"""
        for att in self.browse(cr,uid, ids, context):
            if att.res_model == 'sale.order':
                sale_order_att_obj = self.pool.get('sale.order.attachment')
                domain = [('order_id','=',att.res_id),('name','=',att.name)]
                att_ids = sale_order_att_obj.search(cr,uid,domain)
                sale_order_att_obj.unlink(cr,uid, att_ids, context=context)
        res = super(ir_attachment, self).unlink(cr, uid, ids, context=context)
        return res

    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        return super(ir_attachment, self).copy(cr, uid, id, default, context=context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
