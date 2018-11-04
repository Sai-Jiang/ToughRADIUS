#!/usr/bin/env python
#coding=utf-8
import time
import traceback
from toughlib import utils, apiutils
from toughlib import logger
from toughlib.permit import permit
from toughradius.manage.api.apibase import ApiHandler
from toughradius.manage import models


@permit.route(r"/api/v1/customer/ticket")
class BillingQueryHandler(ApiHandler):

    def get(self):
        self.post()

    def post(self):
        try:
            request = self.parse_form_request()
        except apiutils.SignError, err:
            return self.render_sign_err(err)
        except Exception as err:
            return self.render_parse_err(err)

        try:
            node_id = self.get_argument('node_id', None)
            account_number = self.get_argument('account_number', None)
            framed_ipaddr = self.get_argument('framed_ipaddr', None)
            mac_addr = self.get_argument('mac_addr', None)
            query_begin_time = self.get_argument('query_begin_time', None)
            query_end_time = self.get_argument('query_end_time', None)
            opr_nodes = self.get_opr_nodes()

            _query = self.db.query(
                models.TrTicket.id,
                models.TrTicket.account_number,
                models.TrTicket.nas_addr,
                models.TrTicket.acct_session_id,
                models.TrTicket.acct_start_time,
                models.TrTicket.acct_stop_time,
                models.TrTicket.acct_input_octets,
                models.TrTicket.acct_output_octets,
                models.TrTicket.acct_input_gigawords,
                models.TrTicket.acct_output_gigawords,
                models.TrTicket.framed_ipaddr,
                models.TrTicket.mac_addr,
                models.TrTicket.nas_port_id,
                models.TrCustomer.node_id,
                models.TrCustomer.realname
            ).filter(
                models.TrTicket.account_number == models.TrAccount.account_number,
                models.TrCustomer.customer_id == models.TrAccount.customer_id
            )
            if node_id:
                _query = _query.filter(models.TrCustomer.node_id == node_id)
            else:
                _query = _query.filter(models.TrCustomer.node_id.in_([i.id for i in opr_nodes]))
            if account_number:
                _query = _query.filter(models.TrTicket.account_number.like('%' + account_number + '%'))
            if framed_ipaddr:
                _query = _query.filter(models.TrTicket.framed_ipaddr == framed_ipaddr)
            if mac_addr:
                _query = _query.filter(models.TrTicket.mac_addr == mac_addr)
            if query_begin_time:
                _query = _query.filter(models.TrTicket.acct_start_time >= query_begin_time)
            if query_end_time:
                _query = _query.filter(models.TrTicket.acct_stop_time <= query_end_time)
            _query = _query.order_by(models.TrTicket.acct_start_time.desc())

            ticket = _query.first()
            ticket_data = None

            if ticket:
                ticket_data = {
                        "realname": ticket.realname,
                        "account_number": ticket.account_number,
                        "framed_ipaddr": ticket.framed_ipaddr,
                        "nas_addr": ticket.nas_addr,
                        "acct_start_time": ticket.acct_start_time,
                        "acct_stop_time": ticket.acct_stop_time,
                        "input": utils.bbgb2mb(ticket.acct_input_octets, ticket.acct_input_gigawords),
                        "output": utils.bbgb2mb(ticket.acct_output_octets, ticket.acct_output_gigawords),
                        "mac_addr": ticket.mac_addr,
                        "nas_port_id": ticket.nas_port_id}

            self.render_success(ticket=ticket_data)

            # ticket_data = []
            # if _query:
            #     ticket_data = [{
            #             "realname": ticket.realname,
            #             "account_number": ticket.account_number,
            #             "framed_ipaddr": ticket.framed_ipaddr,
            #             "nas_addr": ticket.nas_addr,
            #             "acct_start_time": ticket.acct_start_time,
            #             "acct_stop_time": ticket.acct_stop_time,
            #             "input": utils.bbgb2mb(ticket.acct_input_octets, ticket.acct_input_gigawords),
            #             "output": utils.bbgb2mb(ticket.acct_output_octets, ticket.acct_output_gigawords),
            #             "mac_addr": ticket.mac_addr,
            #             "nas_port_id": ticket.nas_port_id} for ticket in _query]
            #
            # self.render_success(ticket=ticket_data)
        except Exception as err:
            logger.error(u"api query online error, %s" % utils.safeunicode(traceback.format_exc()))
            self.render_result(code=1, msg=u"api error")