class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Django admin uses inline styles/scripts; its templates and CSRF controls
        # are maintained by Django. The public office UI requires no inline code.
        if not request.path.startswith('/admin/'):
            response['Content-Security-Policy'] = (
                "default-src 'self'; script-src 'self'; style-src 'self'; "
                "img-src 'self' data:; font-src 'self'; connect-src 'self'; "
                "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
            )
        if request.user.is_authenticated or request.path.startswith('/entrar/'):
            response['Cache-Control'] = 'no-store, private'
        response['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        return response
