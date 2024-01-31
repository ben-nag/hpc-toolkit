class CustomMiddleware:
    '''
    Custom middleware to capture exeption information
    and store it in request meta, such that it is retrievable
    via front end html 
    '''
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        '''
        Function called when exception is raised
        '''
        request.META["ExceptionErr"] = str(exception)
        response = HttpResponse()
        response.status_code = 500
        response.content = "An internal server error occurred. Please try again later."
        response["X-Exception"] = str(exception)       
        return response



