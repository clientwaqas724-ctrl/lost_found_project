from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q
from django.shortcuts import render
from django.contrib import messages
from django.db.models import Count
from rest_framework import status, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes
import logging
from rest_framework.permissions import AllowAny
logger = logging.getLogger(__name__)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import generics, permissions, status
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q, Count
import time
from django.shortcuts import render
from django.contrib import messages
import logging
from .serializers import *
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import generics, permissions, status
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from django.utils import timezone
################################################################################################################################
from .models import (
    User,
    Category,
    LostItem,
    FoundItem, 
    Claim, 
    Notification,
    ImageSearchLog   
)
################################################################################################################################
from .serializers import *
#####################################################################################
##############################################################################################################################################################
#########################################################################################################################################################
def home(request):
    context = {
        
    }
    # Render the HTML template index.html with the data in the context variable
    return render(request, 'home.html', context=context)
###########################################################################################################################################################
#############################################################################################################################################################
class AuthViewSet(viewsets.GenericViewSet):
    """
    Authentication ViewSet for user registration and login
    """
    permission_classes = [AllowAny]
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action == 'register':
            return RegisterSerializer
        elif self.action == 'login':
            return LoginSerializer
        elif self.action == 'update_password':
            return UpdatePasswordSerializer
        return RegisterSerializer

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """
        User registration endpoint with automatic token creation
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Get tokens after user creation
        tokens_serializer = self.get_serializer(user)
        
        return Response({
            'message': 'User registered successfully!',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'user_type': user.user_type,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone_number': user.phone_number,
                'tower_number': user.tower_number,
                'room_number': user.room_number,
                'profile_image': user.profile_image.url if user.profile_image else None,
            },
            'tokens': tokens_serializer.get_tokens(user)
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """
        User login endpoint using email and password with automatic token creation
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        return Response({
            'message': 'Login successful!',
            'user': validated_data['user'],
            'tokens': validated_data['tokens'],
            'redirect_url': validated_data['redirect_url']
        }, status=status.HTTP_200_OK)
###########################################################################
# Custom Permissions
class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.user_type == 'admin':
            return True
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return obj == request.user

class IsAdminOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.user_type == 'admin'
#################################################################################################################################################
#################################################################################################################################################
class UserProfileViewSet(viewsets.GenericViewSet,
                        mixins.RetrieveModelMixin,
                        mixins.UpdateModelMixin):
    """
    User Profile ViewSet for managing user profile
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """
        Get or update current user profile
        """
        if request.method == 'GET':
            serializer = self.get_serializer(self.get_object())
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        elif request.method in ['PUT', 'PATCH']:
            partial = request.method == 'PATCH'
            serializer = self.get_serializer(
                self.get_object(), 
                data=request.data, 
                partial=partial
            )
            serializer.is_valid(raise_exception=True)
            
            # Handle file upload separately
            if 'profile_image' in request.FILES:
                serializer.validated_data['profile_image'] = request.FILES['profile_image']
            
            self.perform_update(serializer)
            
            return Response({
                'message': 'Profile updated successfully!',
                'user': serializer.data
            }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['put'], serializer_class=UpdatePasswordSerializer)
    def password(self, request):
        """
        Update user password
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        return Response({
            'message': 'Password updated successfully!'
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def details(self, request):
        """
        Get current user details with profile
        """
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data, status=status.HTTP_200_OK)

    def perform_update(self, serializer):
        serializer.save()

#################################################################################################################################################
#################################################################################################################################################
# Additional convenience views for backward compatibility

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    """
    Get current authenticated user details (for backward compatibility)
    """
    from .serializers import UserProfileSerializer
    user = request.user
    serializer = UserProfileSerializer(user)
    return Response(serializer.data, status=status.HTTP_200_OK)
###############################################################################
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_users(request):
    """
    Get all users API (alternative implementation)
    """
    from .serializers import UserListSerializer
    
    users = User.objects.filter(is_active=True)
    
    # Apply filters
    tower_number = request.GET.get('tower_number')
    user_type = request.GET.get('user_type')
    
    if tower_number:
        users = users.filter(tower_number=tower_number)
    if user_type:
        users = users.filter(user_type=user_type)
    
    serializer = UserListSerializer(users, many=True)
    return Response({
        'count': users.count(),
        'users': serializer.data
    }, status=status.HTTP_200_OK)
##################################
#################################################################################################################################################
#################################################################################################################################################
#####################################################################################
#Category ViewSet
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        """
        Allow all authenticated users to view categories (list/retrieve),
        but only admins can create, update, or delete categories.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]  # all logged-in users can view
        else:
            permission_classes = [IsAuthenticated, IsAdminOnly]  # only admins can modify
        return [permission() for permission in permission_classes]
#####################################################################################
# LostItem ViewSet
class LostItemViewSet(viewsets.ModelViewSet):
    serializer_class = LostItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'admin':
            return LostItem.objects.all()
        return LostItem.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def my_lost_items(self, request):
        items = LostItem.objects.filter(user=request.user)
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_found(self, request, pk=None):
        item = self.get_object()
        if item.user != request.user and request.user.user_type != 'admin':
            return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)
        
        item.status = 'found'
        item.save()
        return Response({"detail": "Item marked as found."})

#####################################################################################
# FoundItem ViewSet
class FoundItemViewSet(viewsets.ModelViewSet):
    serializer_class = FoundItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'user_type', None) == 'admin':
            return FoundItem.objects.all()
        return FoundItem.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def my_found_items(self, request):
        items = FoundItem.objects.filter(user=request.user)
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_returned(self, request, pk=None):
        item = self.get_object()
        user = request.user
        if item.user != user and getattr(user, 'user_type', None) != 'admin':
            return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)
        item.status = 'returned'
        item.save()
        return Response({"detail": "Item marked as returned."})


#####################################################################################
# Claim ViewSet
class ClaimViewSet(viewsets.ModelViewSet):
    serializer_class = ClaimSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'admin':
            return Claim.objects.all()
        return Claim.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOnly])
    def approve_claim(self, request, pk=None):
        claim = self.get_object()
        claim.status = 'approved'
        claim.resolved_at = timezone.now()
        claim.save()
        
        # Update found item status
        claim.found_item.status = 'returned'
        claim.found_item.save()
        
        return Response({"detail": "Claim approved successfully."})

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOnly])
    def reject_claim(self, request, pk=None):
        claim = self.get_object()
        claim.status = 'rejected'
        claim.resolved_at = timezone.now()
        claim.save()
        return Response({"detail": "Claim rejected."})

#####################################################################################
# Notification ViewSet
class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({"unread_count": count})

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({"detail": "Notification marked as read."})

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"detail": "All notifications marked as read."})


#####################################################################################
# Manual Image Search API
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def manual_image_search(request):
    """
    Fast manual image classification and search API
    Uses text-based search on tags, colors, materials, and categories
    """
    serializer = ManualImageSearchSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    start_time = time.time()
    data = serializer.validated_data
    
    # Build search query
    search_query = data['search_query']
    search_type = data['search_type']
    color_filters = data.get('color_filters', '')
    category_filters = data.get('category_filters', '')
    max_results = data.get('max_results', 50)

    # Split search terms
    search_terms = [term.strip().lower() for term in search_query.split(',') if term.strip()]
    
    # Start with appropriate model
    if search_type == 'lost':
        queryset = LostItem.objects.all()
    else:
        queryset = FoundItem.objects.all()

    # Apply search filters
    if search_terms:
        # Create Q objects for each search term across multiple fields
        q_objects = Q()
        for term in search_terms:
            q_objects |= (
                Q(title__icontains=term) |
                Q(description__icontains=term) |
                Q(search_tags__icontains=term) |
                Q(brand__icontains=term) |
                Q(color__icontains=term) |
                Q(category__name__icontains=term)
            )
        queryset = queryset.filter(q_objects)

    # Apply color filters
    if color_filters:
        color_terms = [color.strip().lower() for color in color_filters.split(',') if color.strip()]
        color_q = Q()
        for color in color_terms:
            color_q |= Q(color_tags__icontains=color) | Q(color__icontains=color)
        queryset = queryset.filter(color_q)

    # Apply category filters
    if category_filters:
        category_terms = [cat.strip().lower() for cat in category_filters.split(',') if cat.strip()]
        category_q = Q()
        for category in category_terms:
            category_q |= Q(category__name__icontains=category)
        queryset = queryset.filter(category_q)

    # Exclude user's own items from search results
    if search_type == 'lost':
        queryset = queryset.exclude(user=request.user)
    else:
        queryset = queryset.exclude(user=request.user)

    # Get results
    results = queryset[:max_results]
    search_duration = time.time() - start_time

    # Log the search
    ImageSearchLog.objects.create(
        user=request.user,
        search_type=search_type,
        search_query=search_query,
        color_filters=color_filters,
        category_filters=category_filters,
        results_count=len(results),
        search_duration=search_duration
    )

    # Serialize results
    if search_type == 'lost':
        serializer_class = LostItemSerializer
    else:
        serializer_class = FoundItemSerializer

    results_data = serializer_class(results, many=True, context={'request': request}).data

    return Response({
        'search_metadata': {
            'query': search_query,
            'type': search_type,
            'filters_applied': {
                'colors': color_filters,
                'categories': category_filters
            },
            'results_count': len(results),
            'search_duration_seconds': round(search_duration, 3),
            'max_results': max_results
        },
        'results': results_data
    })

#####################################################################################
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_dashboard(request):
    """User dashboard statistics and recent activities"""
    user = request.user

    # Basic stats for the logged-in user
    stats = {
        'total_lost_items': LostItem.objects.filter(user=user).count(),
        'total_found_items': FoundItem.objects.filter(user=user).count(),
        'total_claims': Claim.objects.filter(user=user).count(),
        'pending_claims': Claim.objects.filter(user=user, status='pending').count(),
        'approved_claims': Claim.objects.filter(user=user, status='approved').count(),
        # Remove total_users if not needed for user-level dashboard
        # 'total_users': User.objects.count()  # <- Only include if serializer expects it
    }

    # Recent activities
    recent_lost = LostItem.objects.filter(user=user).order_by('-created_at')[:5]
    recent_found = FoundItem.objects.filter(user=user).order_by('-created_at')[:5]
    recent_claims = Claim.objects.filter(user=user).order_by('-created_at')[:5]

    recent_activities = []

    for item in recent_lost:
        recent_activities.append({
            'type': 'lost_item',
            'title': item.title,
            'status': item.status,
            'date': item.created_at,
            'id': item.id
        })

    for item in recent_found:
        recent_activities.append({
            'type': 'found_item',
            'title': item.title,
            'status': item.status,
            'date': item.created_at,
            'id': item.id
        })

    for claim in recent_claims:
        recent_activities.append({
            'type': 'claim',
            'title': f"Claim for {claim.found_item.title}" if claim.found_item else "Claim",
            'status': claim.status,
            'date': claim.created_at,
            'id': claim.id
        })

    # Sort activities by most recent
    recent_activities.sort(key=lambda x: x['date'], reverse=True)
    recent_activities = recent_activities[:10]

    stats['recent_activities'] = recent_activities
    stats['unread_notifications'] = Notification.objects.filter(user=user, is_read=False).count()

    # ✅ Safe serializer call (for dict data, use `data=` instead of `instance=`)
    serializer = DashboardStatsSerializer(data=stats)
    serializer.is_valid(raise_exception=False)

    return Response(serializer.data)
#####################################################################################
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminOnly])
def admin_dashboard(request):
    """Admin dashboard with comprehensive statistics"""
    
    stats = {
        'total_lost_items': LostItem.objects.count(),
        'total_found_items': FoundItem.objects.count(),
        'total_claims': Claim.objects.count(),
        'pending_claims': Claim.objects.filter(status='pending').count(),
        'approved_claims': Claim.objects.filter(status='approved').count(),
        'total_users': User.objects.count(),
        'verified_lost_items': LostItem.objects.filter(is_verified=True).count(),
        'verified_found_items': FoundItem.objects.filter(is_verified=True).count(),
        'returned_items': FoundItem.objects.filter(status='returned').count(),
        'claimed_items': Claim.objects.filter(status='approved').count(),
        'user_registrations_today': User.objects.filter(
            created_at__date=timezone.now().date()
        ).count(),
    }
    
    # Recent activities across the system
    recent_lost = LostItem.objects.all().order_by('-created_at')[:5]
    recent_found = FoundItem.objects.all().order_by('-created_at')[:5]
    recent_claims = Claim.objects.all().order_by('-created_at')[:5]
    recent_users = User.objects.all().order_by('-created_at')[:5]
    
    recent_activities = []
    
    for item in recent_lost:
        recent_activities.append({
            'type': 'lost_item',
            'title': item.title,
            'user': item.user.username,
            'status': item.status,
            'date': item.created_at,
            'id': item.id
        })
    
    for item in recent_found:
        recent_activities.append({
            'type': 'found_item',
            'title': item.title,
            'user': item.user.username,
            'status': item.status,
            'date': item.created_at,
            'id': item.id
        })
    
    for claim in recent_claims:
        recent_activities.append({
            'type': 'claim',
            'title': f"Claim by {claim.user.username}",
            'status': claim.status,
            'date': claim.created_at,
            'id': claim.id
        })
    
    for user in recent_users:
        recent_activities.append({
            'type': 'user_registration',
            'title': f"New user: {user.username}",
            'user_type': user.user_type,
            'date': user.created_at,
            'id': user.id
        })
    
    # Sort by date
    recent_activities.sort(key=lambda x: x['date'], reverse=True)
    recent_activities = recent_activities[:15]
    
    stats['recent_activities'] = recent_activities
    
    serializer = AdminDashboardStatsSerializer(stats)
    return Response(serializer.data)

#####################################################################################
# Item Verification APIs (Admin only)
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminOnly])
def verify_lost_item(request, item_id):
    try:
        item = LostItem.objects.get(id=item_id)
        item.is_verified = True
        item.save()
        
        # Create notification for user
        Notification.objects.create(
            user=item.user,
            notification_type='system',
            title='Item Verified',
            message=f'Your lost item "{item.title}" has been verified by admin.',
            lost_item=item
        )
        
        return Response({"detail": "Item verified successfully."})
    except LostItem.DoesNotExist:
        return Response({"detail": "Item not found."}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminOnly])
def verify_found_item(request, item_id):
    try:
        item = FoundItem.objects.get(id=item_id)
        item.is_verified = True
        item.save()
        
        # Create notification for user
        Notification.objects.create(
            user=item.user,
            notification_type='system',
            title='Item Verified',
            message=f'Your found item "{item.title}" has been verified by admin.',
            found_item=item
        )
        
        return Response({"detail": "Item verified successfully."})
    except FoundItem.DoesNotExist:

        return Response({"detail": "Item not found."}, status=status.HTTP_404_NOT_FOUND)
