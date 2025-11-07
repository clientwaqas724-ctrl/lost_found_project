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
import logging
import traceback
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
logger = logging.getLogger(__name__)
User = get_user_model()
from .models import *
#####################################################################################
# Remove the problematic import and use these instead:
from .models import ImageFeature, generate_image_fingerprint, find_similar_images, LostItem, FoundItem
from django.shortcuts import get_object_or_404  # Add this import
import numpy as np
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
# ✅ Import your models and serializers
from lost_found_app1.models import LostItem, FoundItem, Category, ImageSearchLog
from lost_found_app1.serializers import (
    LostItemSerializer,
    FoundItemSerializer,
    ManualImageSearchSerializer,
)
##############################################################################################################################################################
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
# from .models import ImageFeature, generate_image_embedding, LostItem, FoundItem ####========> new updated
# import numpy as np  ##############==> new updated==>
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
    ############################################################################################################################
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
    ##############################################################################################################################
    @action(detail=False, methods=['get'])
    def details(self, request):
        """
        Get current user details with profile
        """
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data, status=status.HTTP_200_OK)
    ###############################################################################################################################
    def perform_update(self, serializer):
        serializer.save()
########################################################################################################################################################################################################
#####################################################################################################################################################################################################
#####################################################################Additional convenience views for backward compatibility####################################################################
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
# ===========================================
# CATEGORY VIEWSET
# ===========================================
class CategoryViewSet(viewsets.ModelViewSet):
    """
    Category management viewset.
    - All authenticated users can list/retrieve categories.
    - Only admins can create/update/delete.
    """
    queryset = Category.objects.all().order_by('id')  # ✅ Fix UnorderedObjectListWarning
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsAdminOnly]
        return [permission() for permission in permission_classes]
###################################################################################################################################################################################################
##############################################################################################################################################################################################
class LostItemViewSet(viewsets.ModelViewSet):
    serializer_class = LostItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = LostItem.objects.select_related('user', 'category').order_by('-created_at')
        if user.user_type == 'admin':
            return qs
        return qs.filter(user=user)

    def get_serializer_context(self):
        """✅ Ensure serializer always gets request context"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def create(self, request, *args, **kwargs):
        logger.info("LostItemViewSet.create() called")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = serializer.save()  # user auto-handled by serializer now

        return Response({
            "success": True,
            "message": "Lost item added successfully!",
            "data": self.get_serializer(item).data
        }, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        """✅ Show lost items (Admin=All, Resident=Own)"""
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page or queryset, many=True)
        if page:
            return self.get_paginated_response(serializer.data)
        return Response({
            "success": True,
            "count": queryset.count(),
            "data": serializer.data
        })

    @action(detail=False, methods=['get'])
    def my_lost_items(self, request):
        user = request.user
        items = LostItem.objects.filter(user=user).order_by('-created_at')
        serializer = self.get_serializer(items, many=True)
        return Response({
            "success": True,
            "message": "My lost items retrieved successfully.",
            "count": items.count(),
            "data": serializer.data
        })
#######################################################################################################################################################################################################
###################################################################################################################################################################################################
class FoundItemViewSet(viewsets.ModelViewSet):
    """
    Found item management.
    - Admin can view all items.
    - Resident sees only their own.
    - Consistent JSON response format.
    """
    serializer_class = FoundItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        base_qs = FoundItem.objects.select_related('user', 'category').order_by('-created_at')

        if getattr(user, 'user_type', '') == 'admin':
            return base_qs
        else:
            return base_qs.filter(user=user)

    def create(self, request, *args, **kwargs):
        """
        Create a new found item with user auto-assigned.
        """
        try:
            logger.info(f"=== FOUND ITEM CREATE === User: {request.user.username}")

            if not request.user.is_authenticated:
                return Response(
                    {"success": False, "message": "User not authenticated."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                logger.warning(f"Validation errors: {serializer.errors}")
                return Response(
                    {
                        "success": False,
                        "message": "Please fix the validation errors below.",
                        "errors": serializer.errors,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # ✅ Assign logged-in user automatically
            found_item = serializer.save(user=request.user)

            response_serializer = self.get_serializer(found_item)
            logger.info(f"Found item created successfully (ID: {found_item.id})")

            return Response(
                {
                    "success": True,
                    "message": "Found item added successfully!",
                    "data": response_serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.error(f"Error creating found item: {str(e)}")
            logger.error(traceback.format_exc())
            return Response(
                {
                    "success": False,
                    "message": "Failed to add found item.",
                    "error": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def list(self, request, *args, **kwargs):
        """
        Consistent response for listing found items.
        """
        try:
            queryset = self.filter_queryset(self.get_queryset())
            logger.info(f"Listing items for: {request.user.username}")

            if not queryset.exists():
                return Response(
                    {
                        "success": True,
                        "message": "No found items available.",
                        "data": [],
                    },
                    status=status.HTTP_200_OK,
                )

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                paginated_data = self.get_paginated_response(serializer.data).data
                # ✅ Wrap pagination result into a consistent structure
                return Response(
                    {
                        "success": True,
                        "message": "Found items retrieved successfully.",
                        "data": paginated_data,
                    },
                    status=status.HTTP_200_OK,
                )

            serializer = self.get_serializer(queryset, many=True)
            return Response(
                {
                    "success": True,
                    "message": "Found items retrieved successfully.",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error listing found items: {str(e)}")
            logger.error(traceback.format_exc())
            return Response(
                {
                    "success": False,
                    "message": "Failed to load found items.",
                    "error": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=['get'])
    def my_found_items(self, request):
        """
        Resident: show own found items
        Admin: show all
        """
        try:
            user = request.user
            if getattr(user, 'user_type', '') == 'admin':
                items = FoundItem.objects.all().order_by('-created_at')
            else:
                items = FoundItem.objects.filter(user=user).order_by('-created_at')

            serializer = self.get_serializer(items, many=True)
            return Response(
                {
                    "success": True,
                    "message": "Found items retrieved successfully.",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error in my_found_items: {str(e)}")
            return Response(
                {
                    "success": False,
                    "message": "Failed to load found items.",
                    "error": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=['post'])
    def mark_returned(self, request, pk=None):
        """
        Mark item as returned (owner or admin only).
        """
        try:
            item = self.get_object()
            user = request.user

            if item.user != user and getattr(user, 'user_type', '') != 'admin':
                return Response(
                    {
                        "success": False,
                        "message": "Not authorized to mark this item as returned.",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            item.status = 'returned'
            item.save()

            return Response(
                {
                    "success": True,
                    "message": "Item marked as returned successfully.",
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error marking item as returned: {str(e)}")
            return Response(
                {
                    "success": False,
                    "message": "Failed to mark item as returned.",
                    "error": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
######################################################################################################################################################################################################
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


##################################################################################################################################################################################################
##################################################################################################################################################################################################
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def manual_image_search(request):
    """
    Smart Manual Image Search API
    ----------------------------------------------------
    ✅ Unified Lost + Found search
    ✅ Works with category, color & keyword filters
    ✅ Returns valid serialized results
    ✅ Handles missing or invalid categories gracefully
    ✅ Logs every search for analytics
    """
    start_time = time.time()

    try:
        serializer = ManualImageSearchSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        search_query = (data.get('search_query') or '').strip()
        search_type = (data.get('search_type') or 'all').strip().lower()
        color_filters = (data.get('color_filters') or '').strip()
        category_filters = (data.get('category_filters') or '').strip()
        max_results = data.get('max_results', 50)

        # Clean & split inputs
        search_terms = [t.strip().lower() for t in re.split(r'[, ]+', search_query) if t.strip()]
        color_terms = [c.strip().lower() for c in re.split(r'[, ]+', color_filters) if c.strip()]
        category_terms = [c.strip().lower() for c in re.split(r'[, ]+', category_filters) if c.strip()]

        matched_category = None
        message = "Results found successfully."

        # ---------------------------------------------------------------
        # CATEGORY VALIDATION
        # ---------------------------------------------------------------
        if category_filters and category_filters.lower() != 'all':
            matched_category = Category.objects.filter(name__iexact=category_filters).first()
            if not matched_category:
                return Response({
                    "count": 0,
                    "results": [],
                    "message": f"Category '{category_filters}' does not exist.",
                    "search_metadata": {"results_count": 0}
                }, status=status.HTTP_200_OK)

        # ---------------------------------------------------------------
        # QUERY BUILDER (Reusable for Lost/Found)
        # ---------------------------------------------------------------
        def build_query(model_qs, is_lost=True):
            q = Q()

            # General search terms
            for term in search_terms:
                q |= (
                    Q(title__icontains=term)
                    | Q(description__icontains=term)
                    | Q(search_tags__icontains=term)
                    | Q(color_tags__icontains=term)
                    | Q(material_tags__icontains=term)
                    | Q(brand__icontains=term)
                    | Q(color__icontains=term)
                    | Q(size__icontains=term)
                    | Q(category__name__icontains=term)
                )
                # Include location field based on model
                if is_lost:
                    q |= Q(lost_location__icontains=term)
                else:
                    q |= Q(found_location__icontains=term)

            # Color filters
            if color_terms:
                color_q = Q()
                for c in color_terms:
                    color_q |= Q(color__icontains=c) | Q(color_tags__icontains=c)
                q &= color_q

            # Category filters
            if matched_category:
                q &= Q(category=matched_category)
            elif category_terms:
                cat_q = Q()
                for cat in category_terms:
                    cat_q |= Q(category__name__iexact=cat)
                q &= cat_q

            return model_qs.filter(q).distinct()

        # ---------------------------------------------------------------
        # PERFORM SEARCH
        # ---------------------------------------------------------------
        lost_qs, found_qs = LostItem.objects.none(), FoundItem.objects.none()

        if search_type == 'lost':
            lost_qs = build_query(LostItem.objects.all(), is_lost=True)
        elif search_type == 'found':
            found_qs = build_query(FoundItem.objects.all(), is_lost=False)
        else:  # 'all'
            lost_qs = build_query(LostItem.objects.all(), is_lost=True)
            found_qs = build_query(FoundItem.objects.all(), is_lost=False)

        # ---------------------------------------------------------------
        # COMBINE & SORT RESULTS
        # ---------------------------------------------------------------
        results = list(lost_qs[:max_results]) + list(found_qs[:max_results])
        results = sorted(results, key=lambda x: getattr(x, "created_at", 0), reverse=True)
        results = results[:max_results]

        # ---------------------------------------------------------------
        # SERIALIZE RESULTS
        # ---------------------------------------------------------------
        lost_data = LostItemSerializer(
            [r for r in results if isinstance(r, LostItem)],
            many=True, context={'request': request}
        ).data

        found_data = FoundItemSerializer(
            [r for r in results if isinstance(r, FoundItem)],
            many=True, context={'request': request}
        ).data

        results_data = lost_data + found_data
        search_duration = round(time.time() - start_time, 3)

        # ---------------------------------------------------------------
        # SAVE SEARCH LOG
        # ---------------------------------------------------------------
        ImageSearchLog.objects.create(
            user=request.user,
            search_type=search_type,
            search_query=search_query or 'N/A',
            color_filters=color_filters,
            category_filters=category_filters,
            results_count=len(results_data),
            search_duration=search_duration
        )

        # ---------------------------------------------------------------
        # FINAL RESPONSE
        # ---------------------------------------------------------------
        return Response({
            "count": len(results_data),
            "results": results_data,
            "message": message if results_data else "No results found.",
            "search_metadata": {
                "query": search_query or "N/A",
                "type": search_type,
                "filters_applied": {
                    "colors": color_filters or "N/A",
                    "categories": category_filters or "N/A"
                },
                "category_exists": bool(matched_category),
                "results_count": len(results_data),
                "search_duration_seconds": search_duration,
                "max_results": max_results
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "error": str(e),
            "message": "An unexpected error occurred during search."
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
##########################################################################################################################################################################################
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_dashboard(request):
    """
    User dashboard for residents.
    Shows only the user's own Lost & Found items and related stats.
    If a resident user has not added any Lost or Found items, those lists are not shown.
    """
    user = request.user

    # ✅ Only allow for resident users
    if not hasattr(user, 'role') or user.role.lower() != 'resident':
        return Response({"detail": "Access restricted. Only resident users can view this dashboard."},
                        status=status.HTTP_403_FORBIDDEN)

    # --- Base statistics ---
    stats = {
        'total_lost_items': LostItem.objects.filter(user=user).count(),
        'total_found_items': FoundItem.objects.filter(user=user).count(),
        'total_claims': Claim.objects.filter(user=user).count(),
        'pending_claims': Claim.objects.filter(user=user, status='pending').count(),
        'approved_claims': Claim.objects.filter(user=user, status='approved').count(),
        'unread_notifications': Notification.objects.filter(user=user, is_read=False).count(),
    }

    # --- Conditionally include Lost and Found lists ---
    recent_activities = []

    user_lost_items = LostItem.objects.filter(user=user).order_by('-created_at')
    user_found_items = FoundItem.objects.filter(user=user).order_by('-created_at')
    user_claims = Claim.objects.filter(user=user).order_by('-created_at')

    # ✅ Only include if user has Lost items
    if user_lost_items.exists():
        for item in user_lost_items[:5]:
            recent_activities.append({
                'type': 'lost_item',
                'title': item.title,
                'status': item.status,
                'date': item.created_at,
                'id': item.id
            })

    # ✅ Only include if user has Found items
    if user_found_items.exists():
        for item in user_found_items[:5]:
            recent_activities.append({
                'type': 'found_item',
                'title': item.title,
                'status': item.status,
                'date': item.created_at,
                'id': item.id
            })

    # ✅ Always include claims (if any)
    if user_claims.exists():
        for claim in user_claims[:5]:
            recent_activities.append({
                'type': 'claim',
                'title': f"Claim for {claim.found_item.title}" if claim.found_item else "Claim",
                'status': claim.status,
                'date': claim.created_at,
                'id': claim.id
            })

    # Sort activities (latest first)
    if recent_activities:
        recent_activities.sort(key=lambda x: x['date'], reverse=True)
        stats['recent_activities'] = recent_activities[:10]
    else:
        stats['recent_activities'] = []

    # --- Serializer output ---
    serializer = DashboardStatsSerializer(data=stats)
    serializer.is_valid(raise_exception=False)

    return Response(serializer.data)
###########################################################################################################################################################################################################
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
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def image_based_search(request):
    """
    Upload an image and find visually similar lost/found items using custom fingerprint algorithm.
    """
    # Validate request data
    serializer = ImageSearchRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    uploaded_image = serializer.validated_data['image']
    search_type = serializer.validated_data['search_type']
    max_results = serializer.validated_data['max_results']

    # Find similar images using custom algorithm
    similar_images = find_similar_images(uploaded_image, search_type, max_results)
    
    if not similar_images:
        return Response({
            'search_metadata': {
                'search_type': search_type,
                'results_count': 0,
                'message': 'No similar items found'
            },
            'results': []
        }, status=status.HTTP_200_OK)

    # Prepare response data
    results_data = []
    lost_item_ids = []
    found_item_ids = []
    
    # Separate item IDs by type
    for result in similar_images:
        if result['item_type'] == 'lost':
            lost_item_ids.append(result['item_id'])
        else:
            found_item_ids.append(result['item_id'])
    
    # Fetch complete item data
    lost_items = LostItem.objects.filter(id__in=lost_item_ids)
    found_items = FoundItem.objects.filter(id__in=found_item_ids)
    
    # Create item mapping for easy lookup
    items_map = {}
    for item in lost_items:
        items_map[('lost', item.id)] = item
    for item in found_items:
        items_map[('found', item.id)] = item
    
    # Build final results with complete item data
    for result in similar_images:
        item_key = (result['item_type'], result['item_id'])
        if item_key in items_map:
            item = items_map[item_key]
            
            if result['item_type'] == 'lost':
                item_serializer = LostItemSerializer(item, context={'request': request})
            else:
                item_serializer = FoundItemSerializer(item, context={'request': request})
            
            results_data.append({
                'item_type': result['item_type'],
                'item_id': result['item_id'],
                'similarity_score': result['similarity_score'],
                'item_data': item_serializer.data,
                'feature_data': ImageFeatureSerializer(result['feature']).data
            })

    # Sort by similarity score (already sorted by the function, but ensure order)
    results_data.sort(key=lambda x: x['similarity_score'], reverse=True)

    return Response({
        'search_metadata': {
            'search_type': search_type,
            'results_count': len(results_data),
            'min_score': min([r['similarity_score'] for r in results_data]) if results_data else 0,
            'max_score': max([r['similarity_score'] for r in results_data]) if results_data else 0
        },
        'results': results_data
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_image_features(request, item_type, item_id):
    """
    Get image features for a specific item
    """
    try:
        feature = ImageFeature.objects.get(item_type=item_type, item_id=item_id)
        serializer = ImageFeatureSerializer(feature)
        return Response(serializer.data)
    except ImageFeature.DoesNotExist:
        return Response(
            {"error": "Image features not found for this item"}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def regenerate_image_features(request, item_type, item_id):
    """
    Regenerate image features for a specific item
    """
    # Determine which model to use based on item_type
    if item_type == 'lost':
        model_class = LostItem
    elif item_type == 'found':
        model_class = FoundItem
    else:
        return Response(
            {"error": "Invalid item type"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get the item
    item = get_object_or_404(model_class, id=item_id)
    
    if not item.item_image:
        return Response(
            {"error": "Item has no image"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Import the signal function to regenerate features
    from .models import generate_image_fingerprint
    
    fingerprint = generate_image_fingerprint(item.item_image)
    if fingerprint:
        ImageFeature.objects.update_or_create(
            item_type=item_type,
            item_id=item_id,
            defaults=fingerprint
        )
        
        # Return updated features
        feature = ImageFeature.objects.get(item_type=item_type, item_id=item_id)
        serializer = ImageFeatureSerializer(feature)
        return Response({
            "message": "Image features regenerated successfully",
            "features": serializer.data
        })
    else:
        return Response(
            {"error": "Failed to generate image features"}, 
            status=status.HTTP_400_BAD_REQUEST
        )










