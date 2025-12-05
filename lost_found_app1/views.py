from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q
from django.shortcuts import render, get_object_or_404
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
from .models import (
    User,
    Category,
    LostItem,
    FoundItem, 
    Claim, 
    Notification,
    ImageSearchLog,
    Message
)
from .serializers import *
from rest_framework.views import APIView
import os
###################################################################################################################################################################################################
###################################################################################################################################################################################################
def home(request):
    context = {}
    return render(request, 'home.html', context=context)
###################################################################################################################################################################################################
###################################################################################################################################################################################################
class AuthViewSet(viewsets.GenericViewSet):
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
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
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
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        return Response({
            'message': 'Login successful!',
            'user': validated_data['user'],
            'tokens': validated_data['tokens'],
            'redirect_url': validated_data['redirect_url']
        }, status=status.HTTP_200_OK)

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

class UserProfileViewSet(viewsets.GenericViewSet,
                        mixins.RetrieveModelMixin,
                        mixins.UpdateModelMixin):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
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
            
            if 'profile_image' in request.FILES:
                serializer.validated_data['profile_image'] = request.FILES['profile_image']
            
            self.perform_update(serializer)
            
            return Response({
                'message': 'Profile updated successfully!',
                'user': serializer.data
            }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['put'], serializer_class=UpdatePasswordSerializer, permission_classes=[])
    def password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'message': 'Password updated successfully!'
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['put'], serializer_class=ForgotPasswordSerializer, permission_classes=[])
    def forgot_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'message': 'Password reset successfully!'
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['delete'], permission_classes=[IsAuthenticated])
    def delete_account(self, request):
        user = request.user
        user.delete()

        return Response({
            'message': 'Your account has been deleted successfully.'
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def details(self, request):
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data, status=status.HTTP_200_OK)

    def perform_update(self, serializer):
        serializer.save()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    from .serializers import UserProfileSerializer
    user = request.user
    serializer = UserProfileSerializer(user)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_users(request):
    from .serializers import UserListSerializer
    
    users = User.objects.filter(is_active=True)
    
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

################################################################################################################################################################
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return super().list(request, *args, **kwargs)
        return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=['post'])
    def initialize_defaults(self, request):
        expanded_categories = [
            {'name': 'Electronics', 'description': 'Phones, laptops, tablets, chargers, headphones, cameras, smartwatches'},
            {'name': 'Books', 'description': 'Textbooks, notebooks, diaries, novels, magazines, journals'},
            {'name': 'Clothing', 'description': 'Shirts, pants, jackets, hats, shoes, dresses, accessories'},
            {'name': 'Accessories', 'description': 'Wallets, keys, bags, watches, jewelry, sunglasses, belts'},
            {'name': 'Documents', 'description': 'IDs, passports, licenses, certificates, folders, papers'},
            {'name': 'Sports', 'description': 'Sports equipment, balls, rackets, bottles, helmets, jerseys'},
            {'name': 'Stationery', 'description': 'Pens, pencils, notebooks, markers, erasers, rulers, staplers'},
            {'name': 'Toys', 'description': 'Children toys, games, stuffed animals, puzzles, board games'},
            {'name': 'Kitchen', 'description': 'Kitchen utensils, containers, lunchboxes, thermos, cutlery'},
            {'name': 'Personal Care', 'description': 'Toiletries, cosmetics, hygiene products, makeup, razors'},
            {'name': 'Jewelry', 'description': 'Rings, necklaces, bracelets, earrings, pendants, chains'},
            {'name': 'Bags', 'description': 'Backpacks, purses, handbags, briefcases, suitcases, duffel bags'},
            {'name': 'School Supplies', 'description': 'Backpacks, notebooks, binders, textbooks, calculators'},
            {'name': 'Musical Instruments', 'description': 'Guitars, pianos, violins, flutes, drums, trumpets'},
            {'name': 'Tools', 'description': 'Hammers, screwdrivers, wrenches, pliers, drills, flashlights'},
            {'name': 'Other', 'description': 'Miscellaneous items that dont fit other categories'}
        ]
        
        created_categories = []
        for category_data in expanded_categories:
            category, created = Category.objects.get_or_create(
                name=category_data['name'],
                defaults={'description': category_data['description']}
            )
            if created:
                created_categories.append(category.name)
        
        return Response({
            'message': f'Created {len(created_categories)} new categories',
            'created_categories': created_categories,
            'total_categories': Category.objects.count()
        })

#########################################################################################################################################################################################
class LostItemViewSet(viewsets.ModelViewSet):
    serializer_class = LostItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'user_type', None) == 'admin':
            return LostItem.objects.all()
        return LostItem.objects.filter(user=user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        if instance.item_image:
            auto_categorize_item(instance)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user and getattr(request.user, 'user_type', None) != 'admin':
            return Response({"detail": "You can only edit your own items."},
                            status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user and getattr(request.user, 'user_type', None) != 'admin':
            return Response({"detail": "You can only delete your own items."},
                            status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def my_lost_items(self, request):
        items = LostItem.objects.filter(user=request.user)
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_found(self, request, pk=None):
        item = self.get_object()
        if item.user != request.user and getattr(request.user, 'user_type', None) != 'admin':
            return Response({"detail": "Not authorized."},
                            status=status.HTTP_403_FORBIDDEN)

        item.status = 'found'
        item.save()
        serializer = self.get_serializer(item)
        return Response(serializer.data)

#########################################################################################################################################################################################
class FoundItemViewSet(viewsets.ModelViewSet):
    serializer_class = FoundItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'user_type', None) == 'admin':
            return FoundItem.objects.all()
        return FoundItem.objects.filter(user=user)

    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        if instance.item_image:
            auto_categorize_item(instance)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user and request.user.user_type != 'admin':
            return Response({"detail": "You can only edit your own items."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user and request.user.user_type != 'admin':
            return Response({"detail": "You can only delete your own items."}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def my_found_items(self, request):
        items = FoundItem.objects.filter(user=request.user)
        serializer = self.get_serializer(items, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_returned(self, request, pk=None):
        item = self.get_object()
        user = request.user
        if item.user != user and getattr(user, 'user_type', None) != 'admin':
            return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)
        item.status = 'returned'
        item.save()
        serializer = self.get_serializer(item, context={'request': request})
        return Response(serializer.data)
################################################################################################################################################################
class MyItemsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        if user.user_type != 'resident':
            return Response({"detail": "Access denied. Only residents can access this."}, status=403)
        serializer = UserItemsSerializer(user)
        return Response(serializer.data)
################################################################################################################################################################
class ClaimViewSet(viewsets.ModelViewSet):
    serializer_class = ClaimSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'admin':
            return Claim.objects.all()
        return Claim.objects.filter(user=user)

################################################################################################################################################################
class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(
            Q(sender=user) | Q(receiver=user)
        ).select_related('claim', 'sender', 'receiver')

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=False, methods=['get'])
    def claim_messages(self, request, claim_id=None):
        claim = get_object_or_404(Claim, id=claim_id)
        
        if request.user not in [claim.user, claim.found_item.user]:
            return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)
        
        messages = Message.objects.filter(claim=claim).select_related('sender', 'receiver')
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        message = self.get_object()
        if message.receiver == request.user:
            message.is_read = True
            message.save()
        return Response({"detail": "Message marked as read."})

################################################################################################################################################################
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

##################################################################################################################################################
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def manual_image_search(request):
    """
    Enhanced Smart Manual Image Search
    ----------------------------------
    - Auto-detects search type if blank.
    - Allows searching Lost + Found by category without specifying search_type.
    - Supports color/category filters.
    - Works for admins and normal users.
    """
    import re, time
    from django.db.models import Q

    start_time = time.time()

    try:
        # --- Validate Input ---
        serializer = ManualImageSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # --- Extract Parameters ---
        search_query = data.get('search_query', '').strip()
        search_type = (data.get('search_type') or '').lower().strip()
        color_filters = data.get('color_filters', '').strip()
        category_filters = data.get('category_filters', '').strip()
        max_results = data.get('max_results', 100)

        # --- Auto-adjust search type ---
        # Case 1: Category filter present but search_type blank → both lost + found
        if category_filters and not search_type:
            search_type = 'all'

        # Case 2: Everything empty → show all
        if not search_query and not color_filters and not category_filters:
            search_type = 'all'

        # --- Split Filters ---
        search_terms = [s.strip().lower() for s in re.split(r'[, ]+', search_query) if s.strip()]
        color_terms = [c.strip().lower() for c in re.split(r'[, ]+', color_filters) if c.strip()]
        category_terms = [c.strip().lower() for c in re.split(r'[, ]+', category_filters) if c.strip()]

        # --- Admin Check ---
        is_admin = request.user.is_staff or request.user.is_superuser

        # --- Base QuerySets ---
        if is_admin:
            lost_base = LostItem.objects.select_related('category', 'user').all()
            found_base = FoundItem.objects.select_related('category', 'user').all()
        else:
            lost_base = LostItem.objects.select_related('category', 'user').filter(user=request.user)
            found_base = FoundItem.objects.select_related('category', 'user').filter(user=request.user)

        # --- Filtering Function ---
        def apply_filters(qs, search_terms, color_terms, category_terms, is_lost=True):
            q_objects = Q()

            # Text Search
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

            # Color Filters
            if color_terms:
                color_q = Q()
                for color_term in color_terms:
                    color_q |= Q(color_tags__icontains=color_term) | Q(color__icontains=color_term)
                q_objects &= color_q

            # Category Filters
            if category_terms:
                category_q = Q()
                for cat_term in category_terms:
                    category_q |= Q(category__name__iexact=cat_term)
                q_objects &= category_q

            return qs.filter(q_objects).distinct()

        # --- STEP 1: Initial Results ---
        if search_type == 'lost':
            initial_results = list(lost_base.order_by('-created_at')[:max_results])
        elif search_type == 'found':
            initial_results = list(found_base.order_by('-created_at')[:max_results])
        else:  # all
            initial_results = list(lost_base.order_by('-created_at')[:max_results]) + \
                              list(found_base.order_by('-created_at')[:max_results])

        # --- STEP 2: Apply Filters ---
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
            filtered_results = initial_results

        # --- Serialize Filtered Results ---
        lost_data = LostItemSerializer(
            [obj for obj in filtered_results if isinstance(obj, LostItem)],
            many=True, context={'request': request}
        ).data
        found_data = FoundItemSerializer(
            [obj for obj in filtered_results if isinstance(obj, FoundItem)],
            many=True, context={'request': request}
        ).data
        results_data = lost_data + found_data

        # --- Serialize Initial Results ---
        initial_lost_data = LostItemSerializer(
            [obj for obj in initial_results if isinstance(obj, LostItem)],
            many=True, context={'request': request}
        ).data
        initial_found_data = FoundItemSerializer(
            [obj for obj in initial_results if isinstance(obj, FoundItem)],
            many=True, context={'request': request}
        ).data
        initial_data = initial_lost_data + initial_found_data

        # --- Log Search ---
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
                "is_admin": is_admin,
                "auto_search_type_applied": bool(category_filters and not data.get('search_type'))
            }
        }, status=200)

    except Exception as e:
        logger.error(f"Manual image search error: {e}", exc_info=True)
        return Response({
            "success": False,
            "message": "An error occurred during search.",
            "error": str(e)
        }, status=500)

################################################################################################################################################################
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def detect_category_from_upload(request):
    """
    Supports BOTH:
    1. multipart/form-data (image file upload)
    2. application/json (image_url)
    """
    try:
        temp_path = None  # default

        # -------------------------------
        # CASE 1: JSON Request (image_url)
        # -------------------------------
        if request.content_type == "application/json":
            data = request.data
            image_url = data.get("image_url")

            if image_url:
                # Process image_url
                try:
                    import tempfile, requests, io
                    from PIL import Image

                    response = requests.get(image_url, timeout=30)
                    response.raise_for_status()

                    # Validate it is a valid image
                    image = Image.open(io.BytesIO(response.content))

                    # Save to temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                        image.save(temp_file, format='JPEG')
                        temp_path = temp_file.name

                except Exception as e:
                    return Response({
                        'success': False,
                        'message': f'Failed to download image from URL: {str(e)}'
                    }, status=status.HTTP_400_BAD_REQUEST)

            else:
                return Response({
                    'success': False,
                    'message': 'JSON request must include "image_url". '
                               'To upload an image file, use multipart/form-data.'
                }, status=status.HTTP_400_BAD_REQUEST)

        # ----------------------------------------
        # CASE 2: multipart/form-data (image file)
        # ----------------------------------------
        elif "image" in request.FILES:
            image_file = request.FILES["image"]

            # Save file temporarily
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                for chunk in image_file.chunks():
                    temp_file.write(chunk)
                temp_path = temp_file.name

        else:
            return Response({
                'success': False,
                'message': 'No image found. Send either:\n'
                           '- multipart/form-data with "image" file, OR\n'
                           '- application/json with "image_url".'
            }, status=status.HTTP_400_BAD_REQUEST)

        # -------------------------------
        # COMMON: Category Detection
        # -------------------------------
        title = request.data.get('title', '')
        description = request.data.get('description', '')

        from .category_detector import AdvancedCategoryDetector
        detector = AdvancedCategoryDetector()
        detected_category = detector.detect_category(temp_path, title, description)

        # Remove temporary file
        try:
            import os
            os.unlink(temp_path)
        except:
            pass

        # Create or fetch category
        from .models import Category
        category, created = Category.objects.get_or_create(
            name=detected_category.capitalize(),
            defaults={'description': f'Auto-detected {detected_category} category'}
        )

        return Response({
            'success': True,
            'detected_category': detected_category,
            'category_id': category.id,
            'category_name': category.name,
            'is_new_category': created
        })

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Category detection error: {e}", exc_info=True)

        return Response({
            'success': False,
            'message': 'Category detection failed',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
################################################################################################################################################################
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_dashboard(request):
    user = request.user

    stats = {
        'total_lost_items': LostItem.objects.filter(user=user).count(),
        'total_found_items': FoundItem.objects.filter(user=user).count(),
        'total_claims': Claim.objects.filter(user=user).count(),
        'pending_claims': Claim.objects.filter(user=user, status='pending').count(),
        'approved_claims': Claim.objects.filter(user=user, status='approved').count(),
    }

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

    recent_activities.sort(key=lambda x: x['date'], reverse=True)
    recent_activities = recent_activities[:10]

    stats['recent_activities'] = recent_activities
    stats['unread_notifications'] = Notification.objects.filter(user=user, is_read=False).count()

    serializer = DashboardStatsSerializer(data=stats)
    serializer.is_valid(raise_exception=False)

    return Response(serializer.data)

################################################################################################################################################################
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminOnly])
def admin_dashboard(request):
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
    
    recent_activities.sort(key=lambda x: x['date'], reverse=True)
    recent_activities = recent_activities[:15]
    
    stats['recent_activities'] = recent_activities
    
    serializer = AdminDashboardStatsSerializer(stats)
    return Response(serializer.data)

################################################################################################################################################################
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminOnly])
def verify_lost_item(request, item_id):
    try:
        item = LostItem.objects.get(id=item_id)
        item.is_verified = True
        item.save()
        
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

################################################################################################################################################################
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminOnly])
def verify_found_item(request, item_id):
    try:
        item = FoundItem.objects.get(id=item_id)
        item.is_verified = True
        item.save()
        
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
