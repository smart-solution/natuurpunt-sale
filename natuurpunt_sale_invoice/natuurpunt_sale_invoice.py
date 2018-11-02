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

from osv import osv, fields
from openerp.tools.translate import _

class account_invoice(osv.osv):

    _inherit = 'account.invoice'

    def view_origin_so(self, cr, uid, ids, context=None):
        view_id = self.pool.get('ir.ui.view').search(cr, uid, [('model','=','sale.order'),
                                                            ('name','=','sale.order.form')])

        sale_invoice_ids = self.pool.get('sale.invoice').search(cr,uid,[('invoice_id','in',ids)])
        sale_invoice = self.pool.get('sale.invoice').browse(cr,uid,sale_invoice_ids)[0]

# fill needed fields in context
        return {
            'type': 'ir.actions.act_window',
            'name': 'Brondocument',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': False,  #view_id[0],
            'res_model': 'sale.order',
            'target': 'current',
            'context': context,
            'res_id': sale_invoice.order_id.id,
            }

    def copy(self, cr, uid, id, default=None, context=None):
        res = super(account_invoice, self).copy(cr, uid, id, default=default, context=context)
        inv = self.browse(cr, uid, res)
        if inv.origin:
            raise osv.except_osv(_('Warning!'),_('You cannot duplicate an invoice with origin!'))
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

