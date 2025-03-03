class HttpResponse:
    @staticmethod
    def success(data, message=""):
        return {"success": True, "message": message, "data": data}

    @staticmethod
    def error(message, code, details=None):
        return {"success": False, "message": message, "code": code, "details": details}
