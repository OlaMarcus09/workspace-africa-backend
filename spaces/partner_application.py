from rest_framework import generics, status
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings
from .models import PartnerSpace
from users.models import CustomUser
import secrets

class PartnerApplicationView(generics.CreateAPIView):
    permission_classes = []  # Allow unauthenticated access
    
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            
            # Check if email already exists
            if CustomUser.objects.filter(email=data.get('email')).exists():
                return Response(
                    {"error": "A user with this email already exists."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if space name already exists
            if PartnerSpace.objects.filter(name=data.get('spaceName')).exists():
                return Response(
                    {"error": "A space with this name already exists."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create temporary password
            temp_password = secrets.token_urlsafe(12)
            
            # Create user account
            user = CustomUser.objects.create_user(
                email=data.get('email'),
                username=data.get('email').split('@')[0],  # Use email prefix as username
                password=temp_password,
                first_name=data.get('fullName', '').split(' ')[0],
                last_name=' '.join(data.get('fullName', '').split(' ')[1:]),
                user_type=CustomUser.UserType.PARTNER
            )
            
            # Create partner space
            space = PartnerSpace.objects.create(
                name=data.get('spaceName'),
                address=data.get('spaceAddress'),
                amenities=data.get('amenities', ''),
                access_tier='STANDARD'  # Default to standard, can be upgraded later
            )
            
            # Link user to space
            user.managed_space = space
            user.save()
            
            # Send confirmation email (you can customize this)
            send_mail(
                'Workspace Africa Partner Application Received',
                f'''
                Hello {data.get('fullName')},
                
                Thank you for your interest in becoming a Workspace Africa partner!
                
                Your space "{data.get('spaceName')}" has been received and is under review.
                We'll contact you within 2 business days.
                
                Application Details:
                - Space: {data.get('spaceName')}
                - Address: {data.get('spaceAddress')}
                - City: {data.get('spaceCity', 'Ibadan')}
                - Amenities: {data.get('amenities', 'Not specified')}
                
                Once approved, you'll get:
                - ₦1,500 per member check-in
                - Real-time dashboard access
                - Monthly automated payouts
                
                Best regards,
                Workspace Africa Team
                ''',
                settings.DEFAULT_FROM_EMAIL,
                [data.get('email')],
                fail_silently=True,
            )
            
            # Send notification to admin (optional)
            send_mail(
                'New Partner Application - Workspace Africa',
                f'''
                New partner application received:
                
                Contact: {data.get('fullName')}
                Email: {data.get('email')}
                Phone: {data.get('phone', 'Not provided')}
                
                Space: {data.get('spaceName')}
                Address: {data.get('spaceAddress')}
                City: {data.get('spaceCity', 'Ibadan')}
                
                Business: {data.get('businessRegistration', 'Not provided')}
                Bank: {data.get('bankAccount', 'Not provided')}
                
                Please review in admin panel.
                ''',
                settings.DEFAULT_FROM_EMAIL,
                [settings.ADMIN_EMAIL],  # Set this in your settings
                fail_silently=True,
            )
            
            return Response(
                {
                    "message": "Application submitted successfully! We'll contact you within 2 business days.",
                    "application_id": user.id
                },
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return Response(
                {"error": f"Application failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
