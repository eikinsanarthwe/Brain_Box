from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

class DeviceInfoMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Skip if no user is authenticated
        if not request.user.is_authenticated:
            return
        
        # Get user agent and IP address
        user_agent_string = request.META.get('HTTP_USER_AGENT', '')
        ip_address = self.get_client_ip(request)
        
        # Store in session
        request.session['user_agent'] = user_agent_string
        request.session['ip_address'] = ip_address
        request.session['last_activity'] = timezone.now().isoformat()
        
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip