import sys
import KSR as KSR

def dumpObj(obj):           # List all obj attributes and methods
    # Function to print all attributes and methods of an object for debugging purposes
    for attr in dir(obj):
        KSR.info("obj attr = %s" % attr)
        if (attr != "Status"):
            KSR.info(" type = %s\n" % type(getattr(obj, attr)))
        else:
            KSR.info("\n")
    return 1

def mod_init():
    # Initialization function called when the module is loaded
    KSR.info("===== from Python mod init\n")
    return kamailio()

class kamailio:
    def __init__(self):
        # Constructor to initialize the kamailio class
        KSR.info('===== kamailio.__init__\n')
        self.userStatus = {}  # Dictionary to track user statuses

    def child_init(self, rank):
        # Function to initialize child processes (currently not used)
        return 0

    def ksr_request_route(self, msg):
        # Function to handle SIP requests
        if (msg.Method == "REGISTER"):
            # Handle REGISTER requests
            KSR.info("REGISTER R-URI: " + KSR.pv.get("$ru") + "\n")
            KSR.info("To: " + KSR.pv.get("$tu") + " Contact: " + KSR.hdr.get("Contact") +"\n")

            if (KSR.pv.get("$fd") != "acme.pt"):
                # Reject requests from domains outside acme.pt
                KSR.info("Fora do dominio acme.pt \n")
                KSR.sl.send_reply(403, "DOMINIO INVALIDO")
                return -1

            # Update user status to Available
            self.userStatus[KSR.pv.get("$fu")] = "Available"
            KSR.info("Estado de " + KSR.pv.get("$fu") + " esta Available \n")
            KSR.registrar.save('location', 0)
            return 1

        if (msg.Method == "INVITE"):
            # Handle INVITE requests
            KSR.info("INVITE R-URI: " + KSR.pv.get("$ru") + "\n")
            KSR.info("From: " + KSR.pv.get("$fu") + "\n")
            KSR.info("To: " + KSR.pv.get("$tu") + "\n")

            if (KSR.pv.get("$fd") != "acme.pt"):
                # Reject requests from domains outside acme.pt
                KSR.info("Fora do dominio acme.pt \n")
                KSR.sl.send_reply(403, "DOMINIO INVALIDO")
                return -1

            if (KSR.pv.get("$td") != "acme.pt"):
                # Reject requests to destinations outside acme.pt
                KSR.info("Fora do dominio acme.pt \n")
                KSR.sl.send_reply(403, "DOMINIO INVALIDO")
                return -1

            if KSR.pv.get("$ru") == "sip:conferencia@acme.pt":
                # Redirect to conference room
                KSR.info("A ir para a sala de conferências! \n")
                self.userStatus[KSR.pv.get("$fu")] = "InConference"
                KSR.info("Estado de " + KSR.pv.get("$fu") + " alterado para InConference \n")
                KSR.pv.sets("$ru", "sip:conferencia@127.0.0.1:5090")
                KSR.rr.record_route()
                KSR.tm.t_relay()
                return 1

            if KSR.registrar.lookup("location") != 1:
                # Reject if the recipient is not registered
                KSR.info("Destino não se disponível \n")
                KSR.sl.send_reply(404, "Destinatário não se disponível")
                return -1

            if self.userStatus.get(KSR.pv.get("$tu")) == "Occupied":
                # Redirect to busy announcement server if the destination is occupied
                KSR.info("Encaminhado para o servidor de anúncios \n")
                self.userStatus[KSR.pv.get("$fu")] = "Occupied"
                KSR.info("Estado de " + KSR.pv.get("$fu") + " alterado para Occupied \n")
                KSR.pv.sets("$ru", "sip:busyann@127.0.0.1:5070")
                KSR.rr.record_route()
                KSR.tm.t_relay()
                return 1

            if self.userStatus.get(KSR.pv.get("$tu")) == "inConference":
                # Redirect to conference announcement server if the destination is in conference
                KSR.info("Encaminhado para o servidor de anúncios! \n")
                KSR.pv.sets("$ru", "sip:inconference@127.0.0.1:5080")
                KSR.rr.record_route()
                KSR.tm.t_relay()
                return 1

            # Normal call handling
            self.userStatus[KSR.pv.get("$fu")] = "Occupied"
            self.userStatus[KSR.pv.get("$tu")] = "Occupied"
            KSR.info("Estado de " + KSR.pv.get("$fu") + " e de " + KSR.pv.get("$tu") + " alterado para Occupied \n")
            KSR.rr.record_route()
            KSR.tm.t_relay()
            return 1

        if (msg.Method == "ACK"):
            # Handle ACK requests
            KSR.info("ACK R-URI: " + KSR.pv.get("$ru") + "\n")
            KSR.tm.t_relay()
            return 1

        if (msg.Method == "CANCEL"):
            # Handle CANCEL requests
            KSR.info("CANCEL R-URI: " + KSR.pv.get("$ru") + "\n")
            KSR.registrar.lookup("location")
            KSR.tm.t_relay()
            return 1

        if (msg.Method == "BYE"):
            # Handle BYE requests
            KSR.info("BYE R-URI: " + KSR.pv.get("$ru") + "\n")
            self.userStatus[KSR.pv.get("$fu")] = "Available"
            self.userStatus[KSR.pv.get("$tu")] = "Available"
            KSR.info("Estado de " + KSR.pv.get("$fu") + " e de " + KSR.pv.get("$tu") + " alterado para Available \n")
            KSR.registrar.lookup("location")
            KSR.tm.t_relay()
            return 1

        if (msg.Method == "MESSAGE"):
            # Handle MESSAGE requests
            KSR.info("MESSAGE R-URI: " + KSR.pv.get("$ru") + "\n")
            KSR.info("From: " + KSR.pv.get("$fu") + " To:" + KSR.pv.get("$tu") + "\n")
            if (KSR.pv.get("$rd") == "a.pt"):
                if (KSR.registrar.lookup("location") == 1):
                    KSR.info("lookup changed R-URI: " + KSR.pv.get("$ru") + "\n")
                    KSR.tm.t_relay()
                else:
                    KSR.sl.send_reply(404, "Not found")
            else:
                KSR.tm.t_relay()
            return 1

    def ksr_reply_route(self, msg):
        # Handle SIP reply messages
        reply_code = int(KSR.pv.get("$rs"))
        KSR.info("Código de resposta obtido: " + str(KSR.pv.get("$rs")) + "\n")

        if 400 <= reply_code <= 499:
            # Mark users as available if the session was rejected
            KSR.info("Sessão rejeitada\n")
            self.userStatus[KSR.pv.get("$fu")] = "Available"
            self.userStatus[KSR.pv.get("$tu")] = "Available"
            KSR.info("Estado de " + KSR.pv.get("$fu") + " e de " + KSR.pv.get("$tu") + " alterado para Available \n")
            KSR.tm.t_relay()
            return -1

        return 1

    def ksr_onsend_route(self, msg):
        # Placeholder for handling messages being sent
        return 1

    def ksr_onreply_route_INVITE(self, msg):
        # Placeholder for handling replies to INVITE messages
        return 0

    def ksr_failure_route_INVITE(self, msg):
        # Placeholder for handling failures in INVITE transactions
        return 1
