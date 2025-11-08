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
################################
from rest_framework.views import APIView   ###new Updated
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
###########################################################################################################################################################
######################################################(new update the password update code)#########################################################################
    ########################################################################
    # Update Password (requires old password)
    ########################################################################
    @action(detail=False, methods=['put'], serializer_class=UpdatePasswordSerializer, permission_classes=[])
    def password(self, request):
        """
        Update user password using email and old password
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'message': 'Password updated successfully!'
        }, status=status.HTTP_200_OK)

    ########################################################################
    # Forgot Password (reset with email only)
    ########################################################################
    @action(detail=False, methods=['put'], serializer_class=ForgotPasswordSerializer, permission_classes=[])
    def forgot_password(self, request):
        """
        Reset user password using email only
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'message': 'Password reset successfully!'
        }, status=status.HTTP_200_OK)
    ##################################################################################
    @action(detail=False, methods=['delete'], permission_classes=[IsAuthenticated])
    def delete_account(self, request):
        """
        Delete the currently authenticated user's account
        """
        user = request.user
        user.delete()

        return Response({
            'message': 'Your account has been deleted successfully.'
        }, status=status.HTTP_200_OK)
#########################################################################################################################################################################
#########################################################################################################################################################################
    @action(detail=False, methods=['get'])
    def details(self, request):
        """
        Get current user details with profile
        """
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data, status=status.HTTP_200_OK)
####################################################################################################################################################################
####################################################################################################################################################################
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
# Category ViewSet
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        # Allow all authenticated users to view categories
        if request.user.is_authenticated:
            return super().list(request, *args, **kwargs)
        return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)
#################################################################################################################
#################################################################################################################
# LostItem ViewSet
class LostItemViewSet(viewsets.ModelViewSet):
    serializer_class = LostItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Admin users see all lost items
        if user.user_type == 'admin':
            return LostItem.objects.all()

        # Resident users
        if user.user_type == 'resident':
            user_items = LostItem.objects.filter(user=user)
            if user_items.exists():
                # If resident has posted before, show only their items
                return user_items
            else:
                # If resident has not posted yet, show all lost items
                return LostItem.objects.all()

        # Other users can see all items (customize if needed)
        return LostItem.objects.all()

    def perform_create(self, serializer):
        # Save the current user as the owner of the lost item
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def my_lost_items(self, request):
        # Return all lost items created by the current user
        items = LostItem.objects.filter(user=request.user)
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_found(self, request, pk=None):
        # Allow marking item as found if the user owns it or is admin
        item = self.get_object()
        if item.user != request.user and request.user.user_type != 'admin':
            return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)
        
        item.status = 'found'
        item.save()
        return Response({"detail": "Item marked as found."})
#################################################################################################################
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
#######################################################################################################################################################################
class MyItemsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        if user.user_type != 'resident':
            return Response({"detail": "Access denied. Only residents can access this."}, status=403)
        serializer = UserItemsSerializer(user)
        return Response(serializer.data)
#########################################################################################################################################################################
class ClaimViewSet(viewsets.ModelViewSet):
    serializer_class = ClaimSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'admin':
            return Claim.objects.all()
        return Claim.objects.filter(user=user)
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
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def manual_image_search(request):
    import re, time
    from django.db.models import Q

    start_time = time.time()

    try:
        serializer = ManualImageSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # --- Extract parameters ---
        search_query = data.get('search_query', '').strip()
        search_type = data.get('search_type', 'all').lower()
        color_filters = data.get('color_filters', '').strip()
        category_filters = data.get('category_filters', '').strip()
        max_results = data.get('max_results', 100)

        # --- Split filters ---
        search_terms = [s.strip().lower() for s in re.split(r'[, ]+', search_query) if s.strip()]
        color_terms = [c.strip().lower() for c in re.split(r'[, ]+', color_filters) if c.strip()]
        category_terms = [c.strip().lower() for c in re.split(r'[, ]+', category_filters) if c.strip()]

        # --- Admin check ---
        is_admin = request.user.is_staff or request.user.is_superuser

        # --- Base QuerySets ---
        if is_admin:
            lost_base = LostItem.objects.select_related('category', 'user').all()
            found_base = FoundItem.objects.select_related('category', 'user').all()
        else:
            lost_base = LostItem.objects.select_related('category', 'user').filter(user=request.user)
            found_base = FoundItem.objects.select_related('category', 'user').filter(user=request.user)

        # --- Filtering function ---
        def apply_filters(qs, search_terms, color_terms, category_terms, is_lost=True):
            q_objects = Q()

            # Search terms
            for term in search_terms:
                q_objects |= (
                    Q(title__icontains=term) |
                    Q(description__icontains=term) |
                    Q(search_tags__icontains=term) |
                    Q(color_tags__icontains=term) |
                    Q(material_tags__icontains=term) |
                    Q(brand__icontains=term) |
                    Q(color__icontains=term) |
                    Q(size__icontains=term)
                )
                if is_lost:
                    q_objects |= Q(lost_location__icontains=term)
                else:
                    q_objects |= Q(found_location__icontains=term)

            # Color filters (optional)
            if color_terms:
                color_q = Q()
                for color_term in color_terms:
                    color_q |= Q(color_tags__icontains=color_term) | Q(color__icontains=color_term)
                q_objects &= color_q

            # Category filter (strict)
            if category_terms:
                category_q = Q()
                for cat_term in category_terms:
                    category_q |= Q(category__name__iexact=cat_term)
                q_objects &= category_q

            return qs.filter(q_objects).distinct()

        # --- STEP 1: Initial results (before search) strictly by type ---
        if search_type == 'lost':
            initial_results = list(lost_base.order_by('-created_at')[:max_results])
        elif search_type == 'found':
            initial_results = list(found_base.order_by('-created_at')[:max_results])
        else:  # all
            initial_results = list(lost_base.order_by('-created_at')[:max_results]) + \
                              list(found_base.order_by('-created_at')[:max_results])

        # --- STEP 2: Apply filters ---
        if search_terms or color_terms or category_terms:
            if search_type == 'lost':
                filtered_results = apply_filters(lost_base, search_terms, color_terms, category_terms, is_lost=True).order_by('-created_at')[:max_results]
            elif search_type == 'found':
                filtered_results = apply_filters(found_base, search_terms, color_terms, category_terms, is_lost=False).order_by('-created_at')[:max_results]
            else:  # all
                lost_results = apply_filters(lost_base, search_terms, color_terms, category_terms, is_lost=True).order_by('-created_at')[:max_results]
                found_results = apply_filters(found_base, search_terms, color_terms, category_terms, is_lost=False).order_by('-created_at')[:max_results]
                filtered_results = list(lost_results) + list(found_results)
        else:
            filtered_results = initial_results  # if no filters, show initial results

        # --- Serialize filtered results ---
        lost_data = LostItemSerializer([obj for obj in filtered_results if isinstance(obj, LostItem)], many=True, context={'request': request}).data
        found_data = FoundItemSerializer([obj for obj in filtered_results if isinstance(obj, FoundItem)], many=True, context={'request': request}).data
        results_data = lost_data + found_data

        # --- Serialize initial results ---
        initial_lost_data = LostItemSerializer([obj for obj in initial_results if isinstance(obj, LostItem)], many=True, context={'request': request}).data
        initial_found_data = FoundItemSerializer([obj for obj in initial_results if isinstance(obj, FoundItem)], many=True, context={'request': request}).data
        initial_data = initial_lost_data + initial_found_data

        # --- Log search ---
        ImageSearchLog.objects.create(
            user=request.user,
            search_type=search_type,
            search_query=search_query or 'N/A',
            color_filters=color_filters,
            category_filters=category_filters,
            results_count=len(results_data),
            search_duration=round(time.time() - start_time, 3)
        )

        # --- Response ---
        return Response({
            "success": True,
            "message": f"Found {len(results_data)} item(s)" if results_data else "No items found.",
            "count": len(results_data),
            "results": results_data,
            "initial_results": initial_data,
            "search_metadata": {
                "query": search_query or "All Items",
                "type": search_type,
                "filters_applied": {
                    "colors": color_filters or "None",
                    "categories": category_filters or "None"
                },
                "results_count": len(results_data),
                "initial_count": len(initial_data),
                "search_duration_seconds": round(time.time() - start_time, 3),
                "max_results": max_results,
                "is_admin": is_admin
            }
        }, status=200)

    except Exception as e:
        logger.error(f"Manual image search error: {e}", exc_info=True)
        return Response({
            "success": False,
            "message": "An error occurred during search.",
            "error": str(e)
        }, status=500)
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
################################################################################################################################

